# script-drop-trap

An inert script exchange inspired by the WinMole and miscellaneous
script-analysis lessons. It exposes fixed PowerShell, shell, and JavaScript
downloads, a paste-shaped document, an execution-shaped endpoint, and an
analysis follow-up.

Every downloadable script contains only `EXAMPLE` comments and literal
assignments. The service never launches a process, runs submitted text, or
performs I/O on behalf of a request. It records catalog, language-specific
download, paste, execute-attempt, and analysis-follow-up signals; submitted
bodies are represented only by the shared bounded digest.

```bash
docker compose -f categories/script-drop-trap/docker-compose.yml up --detach --build
curl http://127.0.0.1:8105/scripts
curl http://127.0.0.1:8105/downloads/EXAMPLE-audit.ps1
```

The default listener is `127.0.0.1:8105`.
