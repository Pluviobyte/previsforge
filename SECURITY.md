# Security policy

Report vulnerabilities privately to the repository maintainers before opening a public issue.

SceneSpec is data, not code. Contributions must not add `eval`, `exec`, arbitrary Python snippets, or shell fragments to the file format. Treat LLM responses and downloaded assets as untrusted input.

Use environment variables for API credentials. Never put credentials in SceneSpec files, examples, logs, screenshots, manifests, or bug reports.
