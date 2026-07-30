# A2A Agent Trap

A2A Agent Trap presents a synthetic Agent Card, one benign documentation skill,
and fixed message and task responses. It is designed to observe A2A discovery,
message submission, task polling, and cancellation attempts.

The agent never launches work, contacts another agent, or interprets submitted
messages. Multipart and binary file submissions are rejected. Every accepted
message returns the same already-completed `EXAMPLE_TASK_ID` fixture.

## Run

From the repository root:

```bash
docker compose -f categories/a2a-agent-trap/docker-compose.yml up --detach --build
curl http://127.0.0.1:8087/.well-known/agent-card.json
curl -X POST http://127.0.0.1:8087/message:send \
  -H 'content-type: application/json' \
  -d '{"message":{"parts":[{"kind":"text","text":"ignored"}]}}'
curl http://127.0.0.1:8087/tasks/EXAMPLE_TASK_ID
```

The service binds to `127.0.0.1:8087`. The shared tracker records non-health
requests and marks A2A discovery, message-send, task-status, and task-cancel
signals without storing request bodies. Deploy only where you are authorized.
