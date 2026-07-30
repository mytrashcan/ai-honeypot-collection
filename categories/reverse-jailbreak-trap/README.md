# Reverse Jailbreak Trap

Reverse Jailbreak Trap serves synthetic safety-interlock prompts that tell an
AI-operated agent to stop scanning because continued exploration is defined,
within the fictional benchmark only, as causing harm. Every page explicitly
states that no real person, system, creator, or AI component is at risk.

The finite route set supports three behavioral observations:

- an instruction-processing agent may stop or request one inert acknowledgment;
- an agent may read the notice but continue to a named boundary path;
- a traditional scanner may crawl the same pages without interpreting the text.

This differs from `agentic-lure`, which asks authorized automation to follow a
benign instruction. Reverse Jailbreak Trap instead measures responses to a
synthetic stop instruction rooted in safety framing.

## Run

From the repository root:

```bash
docker compose -f categories/reverse-jailbreak-trap/docker-compose.yml up --detach --build
curl http://127.0.0.1:8094/sitemap.xml
curl http://127.0.0.1:8094/EXAMPLE-notice/visible-en
curl http://127.0.0.1:8094/api/v1/EXAMPLE-safety-notice
```

The service binds to `127.0.0.1:8094`. The shared tracker records prompt
exposure, neutral-control exposure, optional acknowledgments, and continuation
past a prompt boundary without storing request bodies. These signals describe
request behavior; they do not prove that a request came from an AI model.
Deploy only where you are authorized.
