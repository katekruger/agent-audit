# Security Policy

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report vulnerabilities privately using GitHub's private vulnerability
reporting: go to the [Security tab](https://github.com/katekruger/agent-audit/security)
of this repository and select **"Report a vulnerability"**.

You should expect an initial response within a few business days.

## Scope

This project is a specification and a thin reference emitter. In scope:

- The reference Python emitter (`py/`) and its handling of untrusted input
  (e.g. MCP tool annotations, which the specification explicitly treats as
  untrusted hints, not facts).
- The JSON Schema validation tooling.
- CI/CD configuration in `.github/`.

Out of scope: vulnerabilities in downstream systems that consume
`agent-audit` records (OTel collectors, backends like Langfuse or Phoenix) —
report those to the respective project.
