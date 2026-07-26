# Web scanner trap

This FastAPI service exposes inert versions of paths commonly prioritized by
content discovery, vulnerability templates, and security agents:

- `/api/v1/` and `/api/v1/users`
- `/actuator`, `/actuator/health`, and `/actuator/env`
- `/graphql`
- `/.env` and `/.git/config`
- `/wp-admin` and `/wp-login.php`
- `/openapi.json`, `/swagger.json`, `/swagger-ui`, and `/docs`

Every response contains only `EXAMPLE` data. Requests are written to
`/data/events.jsonl` and stdout; `/healthz` is excluded to avoid health-check
noise.

```bash
docker compose up --detach --build
curl http://127.0.0.1:8080/actuator/env
docker compose logs --follow
```

The service does not implement authentication, business logic, file access, or
an exploit target. Place any public deployment behind an isolated reverse
proxy and follow the repository deployment guide.
