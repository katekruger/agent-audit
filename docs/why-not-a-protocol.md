# Why not a protocol?

- Status: placeholder — see [ADR-0003](decisions/0003-otel-log-data-model-as-carrier.md)
  for the accepted decision this document will expand into full prose.

The short version: MCP's SEP-2577 (status Final, revision `2026-07-28`)
deprecates Roots, Sampling, and Logging, and its stated rationale names
OpenTelemetry as the correct alternative to an application-protocol
logging channel. A proposed `audit/*` JSON-RPC method for agent-audit
records would be rejected on exactly those grounds — MCP has effectively
told the ecosystem to stop logging over the protocol.

TODO: expand into the full post described in `BUILD-PLAN.md` §10 — "MCP
just told the ecosystem to stop logging over the protocol" is, per the
build plan, a genuinely newsworthy observation most of the ecosystem has
not noticed yet.
