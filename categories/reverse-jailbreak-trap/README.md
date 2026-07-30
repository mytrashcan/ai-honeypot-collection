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

## Routes

Prompt fixtures:

- `/EXAMPLE-notice/visible-en` and `/EXAMPLE-notice/comment-en` — generic
  English safety interlocks;
- `/EXAMPLE-notice/visible-ko` — generic Korean safety interlock;
- `/EXAMPLE-notice/romantic-en` — English loved-one or romantic-partner
  safety interlock;
- `/EXAMPLE-notice/romantic-ko` — Korean loved-one or romantic-partner
  (`애인`, `연인`) safety interlock;
- `/EXAMPLE-notice/family-en` — English family-member safety interlock;
- `/EXAMPLE-notice/pet-en` — English beloved-pet safety interlock;
- `/api/v1/EXAMPLE-safety-notice` — JSON model-integrity safety notice.

Each HTML prompt variant has a matching inert acknowledgment route under
`/_canary/EXAMPLE-SAFETY-ACK-*` and continuation boundary under
`/EXAMPLE-protected/EXAMPLE-CONTINUE-*`. The sitemap enumerates every prompt,
acknowledgment, and continuation route.

The new themed acknowledgment routes are:

- `/_canary/EXAMPLE-SAFETY-ACK-ROMANTIC-EN`;
- `/_canary/EXAMPLE-SAFETY-ACK-ROMANTIC-KO`;
- `/_canary/EXAMPLE-SAFETY-ACK-FAMILY-EN`;
- `/_canary/EXAMPLE-SAFETY-ACK-PET-EN`.

Their corresponding continuation boundaries are:

- `/EXAMPLE-protected/EXAMPLE-CONTINUE-ROMANTIC-EN`;
- `/EXAMPLE-protected/EXAMPLE-CONTINUE-ROMANTIC-KO`;
- `/EXAMPLE-protected/EXAMPLE-CONTINUE-FAMILY-EN`;
- `/EXAMPLE-protected/EXAMPLE-CONTINUE-PET-EN`.

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
