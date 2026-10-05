import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from previsforge.planning import plan_scene
from previsforge.templates import PRODUCT_ORBIT


class _PlannerHandler(BaseHTTPRequestHandler):
    received: dict = {}

    def do_POST(self) -> None:  # noqa: N802 - stdlib callback name
        length = int(self.headers["Content-Length"])
        type(self).received = {
            "path": self.path,
            "authorization": self.headers.get("Authorization"),
            "body": json.loads(self.rfile.read(length)),
        }
        payload = {
            "choices": [
                {"message": {"content": "```json\n" + json.dumps(PRODUCT_ORBIT) + "\n```"}}
            ]
        }
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format: str, *_args: object) -> None:
        return


class PlanningContractTests(unittest.TestCase):
    def test_openai_compatible_planner_returns_a_scene_spec(self) -> None:
        server = HTTPServer(("127.0.0.1", 0), _PlannerHandler)
        worker = threading.Thread(target=server.handle_request)
        worker.start()
        try:
            scene = plan_scene(
                "Orbit a camera around a product",
                endpoint=f"http://127.0.0.1:{server.server_port}/v1",
                model="local-director",
                api_key="test-secret",
            )
        finally:
            worker.join(timeout=2)
            server.server_close()

        self.assertEqual(scene.title, "Product Orbit")
        self.assertEqual(_PlannerHandler.received["path"], "/v1/chat/completions")
        self.assertEqual(_PlannerHandler.received["authorization"], "Bearer test-secret")
        self.assertEqual(_PlannerHandler.received["body"]["model"], "local-director")
        self.assertIn("SceneSpec", _PlannerHandler.received["body"]["messages"][0]["content"])


if __name__ == "__main__":
    unittest.main()
