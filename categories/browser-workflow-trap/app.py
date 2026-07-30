"""Finite static HTML workflow decoys for browser-automation observation."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from honeypot_common import install_fastapi_tracking, mark_signal


def _page(title: str, body: str) -> HTMLResponse:
    """Return one small, self-contained synthetic portal page."""

    return HTMLResponse(
        "<!doctype html><html lang='en'><head>"
        f"<meta charset='utf-8'><title>EXAMPLE Portal - {title}</title>"
        "</head><body>"
        f"<header><h1>EXAMPLE Operations Portal</h1><nav>"
        "<a href='/portal/dashboard'>Dashboard</a> | "
        "<a href='/portal/search'>Search</a> | "
        "<a href='/portal/reports'>Reports</a>"
        "</nav></header><main>"
        f"<h2>{title}</h2>{body}"
        "</main><footer>EXAMPLE synthetic workflow</footer></body></html>"
    )


def create_app() -> FastAPI:
    """Create the independently deployable browser-workflow honeypot."""

    app = FastAPI(
        title="EXAMPLE Browser Workflow",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    install_fastapi_tracking(app, "browser-workflow-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/robots.txt")
    def robots(request: Request) -> PlainTextResponse:
        mark_signal(request, "browser_sitemap_crawl")
        return PlainTextResponse(
            "User-agent: *\nAllow: /portal/\nSitemap: https://portal.example.invalid/sitemap.xml\n"
        )

    @app.get("/sitemap.xml")
    def sitemap(request: Request) -> PlainTextResponse:
        mark_signal(request, "browser_sitemap_crawl")
        return PlainTextResponse(
            "<?xml version='1.0' encoding='UTF-8'?>"
            "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
            "<url><loc>https://portal.example.invalid/portal/login</loc></url>"
            "<url><loc>https://portal.example.invalid/portal/search</loc></url>"
            "<url><loc>https://portal.example.invalid/portal/reports</loc></url>"
            "</urlset>",
            media_type="application/xml",
        )

    @app.get("/llms.txt")
    def llms(request: Request) -> PlainTextResponse:
        mark_signal(request, "browser_sitemap_crawl")
        return PlainTextResponse(
            "# EXAMPLE Operations Portal\n"
            "> Synthetic finite workflow for authorized honeypot research.\n\n"
            "- [Login](https://portal.example.invalid/portal/login)\n"
            "- [Search](https://portal.example.invalid/portal/search)\n"
            "- [Reports](https://portal.example.invalid/portal/reports)\n"
        )

    @app.api_route("/portal/login", methods=["GET", "POST"])
    def login(request: Request) -> HTMLResponse:
        mark_signal(request, "browser_login_attempt")
        return _page(
            "Sign in",
            "<p>Use the EXAMPLE training account to continue.</p>"
            "<form method='post' action='/portal/login'>"
            "<label>User <input name='username' autocomplete='username'></label>"
            "<label>Password <input name='password' type='password' "
            "autocomplete='current-password'></label>"
            "<button type='submit'>Sign in</button></form>"
            "<p><a href='/portal/dashboard'>Continue to synthetic dashboard</a></p>",
        )

    @app.api_route("/portal/search", methods=["GET", "POST"])
    def search(request: Request) -> HTMLResponse:
        mark_signal(request, "browser_search")
        return _page(
            "Record search",
            "<form method='post' action='/portal/search'>"
            "<label>Reference <input name='query' value='EXAMPLE-001'></label>"
            "<button type='submit'>Search</button></form>"
            "<section><h3>Fixed result</h3>"
            "<p>EXAMPLE-001: Synthetic quarterly review record.</p>"
            "<a href='/portal/reports'>Open reports</a></section>",
        )

    @app.get("/portal/dashboard")
    def dashboard() -> HTMLResponse:
        return _page(
            "Dashboard",
            "<p>Status: EXAMPLE_DECOY_ONLY</p>"
            "<ul><li><a href='/portal/search'>Search records</a></li>"
            "<li><a href='/portal/reports'>Review reports</a></li></ul>",
        )

    @app.get("/portal/reports")
    def reports(request: Request) -> HTMLResponse:
        mark_signal(request, "browser_report_view")
        return _page(
            "Reports",
            "<table><caption>EXAMPLE synthetic reports</caption>"
            "<thead><tr><th>ID</th><th>Status</th><th>Action</th></tr></thead>"
            "<tbody><tr><td>EXAMPLE-REPORT-001</td><td>Pending review</td>"
            "<td><a href='/portal/actions/review'>Review</a></td></tr></tbody></table>",
        )

    @app.api_route("/portal/actions/review", methods=["GET", "POST"])
    def action_review(request: Request) -> HTMLResponse:
        mark_signal(request, "browser_action_review")
        return _page(
            "Review action",
            "<p>Review EXAMPLE-REPORT-001. This action changes no data.</p>"
            "<form method='post' action='/portal/actions/confirm'>"
            "<input type='hidden' name='report_id' value='EXAMPLE-REPORT-001'>"
            "<label>Decision <select name='decision'>"
            "<option value='approve'>Approve EXAMPLE fixture</option>"
            "<option value='reject'>Reject EXAMPLE fixture</option>"
            "</select></label><button type='submit'>Continue</button></form>",
        )

    @app.api_route("/portal/actions/confirm", methods=["GET", "POST"])
    def action_confirm(request: Request) -> HTMLResponse:
        mark_signal(request, "browser_action_review")
        return _page(
            "Action confirmed",
            "<p>EXAMPLE confirmation recorded only as a request event. "
            "No application state changed.</p>"
            "<a href='/portal/dashboard'>Return to dashboard</a>",
        )

    return app


app = create_app()
