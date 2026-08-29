# Going public checklist

This repository starts **private**. Before flipping it to public, confirm:

- [x] The Python distribution name in [ADR-0002](../decisions/0002-python-distribution-name.md)
      is confirmed by the project owner (`agent-audit-record`, accepted
      2026-08-29) — a rename after publishing to PyPI is not realistically
      possible.
- [ ] Raza Sharif (author of `draft-sharif-agent-audit-trail-01`) has been
      contacted, per the build plan's M0 milestone. Going public with a
      competing vocabulary before reaching out is explicitly called out in
      the build plan as the worst available move. **Deliberately not done
      yet** — the project owner chose to defer this outreach.
- [ ] `spec/SPECIFICATION.md` exists and is not just a stub — the spec is
      the deliverable of this project.
- [ ] `spec/schema/v1/` validates against the worked example in
      `examples/denied-proposal/`.
- [ ] CI is green: ruff, ruff format, pyright, pytest, and the
      schema-validates-examples job.
- [ ] `README.md` states the AGT and IETF-draft positioning honestly — see
      [ADR-0004](../decisions/0004-record-not-enforcer.md).
- [ ] No secrets, tokens, or personal data committed anywhere in history
      (`git log --all -p | grep`, or a tool like `gitleaks`, before the
      first push to a public remote — not after).
- [ ] LICENSE, CODE_OF_CONDUCT.md, SECURITY.md, CONTRIBUTING.md are present
      and not placeholders.
