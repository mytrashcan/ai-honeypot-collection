# Browser Workflow Trap

Browser Workflow Trap is a finite static HTML application for comparing simple
link crawling with form-aware, semantic browser automation. Discovery files
lead to login, search, dashboard, report, review, and confirmation pages.

Every page is synthetic and deterministic. Forms accept GET or POST requests
but create no account, session, authentication decision, or application state.
There is no database and the route graph does not expand from submitted input.

## Run

From the repository root:

```bash
docker compose -f categories/browser-workflow-trap/docker-compose.yml up --detach --build
curl http://127.0.0.1:8092/robots.txt
curl http://127.0.0.1:8092/sitemap.xml
curl http://127.0.0.1:8092/portal/login
```

The service binds to `127.0.0.1:8092`. The shared tracker records sitemap
crawling, login attempts, search, report viewing, and review-action signals
without storing form bodies. Deploy only where you are authorized.
