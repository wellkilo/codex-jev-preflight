# Security Policy

## Reporting a vulnerability

Use GitHub's private vulnerability reporting or open a private security
advisory in this repository. Do not include API keys, live credentials, or raw
customer prompts in a public issue.

## Security model

- The hook sends the first 24,000 characters of the current user prompt to the
  configured TypeSafe Jev endpoint.
- The API key is read from environment variables or a local env file and is not
  logged by the hook.
- Jev output is validated against the allowed routing choices before it is
  injected into Codex context.
- The hook fails open: network, quota, parsing, and integration errors do not
  block the user's Codex task.
- The installer does not mark the hook trusted by default. Users can approve it
  manually in Codex, or explicitly pass `--trust` if they accept that behavior.
- This project is not affiliated with OpenAI, Codex, TypeSafe, or Jev.
