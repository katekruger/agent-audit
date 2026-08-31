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
      yet** — the project owner chose to defer this outreach; see
      [ADR-0006](../decisions/0006-ietf-outreach-deferred-before-public.md).
      A ready-to-send draft (with the author's public IETF-datatracker
      contact address) exists outside this repo, pending the owner's
      review and send.
- [ ] `spec/SPECIFICATION.md` exists and is not just a stub — the spec is
      the deliverable of this project.
- [ ] `spec/schema/v1/` validates against the worked example in
      `examples/denied-proposal/`.
- [ ] CI is green: ruff, ruff format, pyright, pytest, and the
      schema-validates-examples job.
- [ ] `README.md` states the AGT and IETF-draft positioning honestly — see
      [ADR-0004](../decisions/0004-record-not-enforcer.md).
- [x] `docs/why-not-a-protocol.md` and `docs/vs-agent-governance-toolkit.md`
      are full posts, not placeholders — accepted 2026-08-30.
- [ ] No secrets, tokens, or personal data committed anywhere in history
      (`git log --all -p | grep`, or a tool like `gitleaks`, before the
      first push to a public remote — not after).
- [ ] LICENSE, CODE_OF_CONDUCT.md, SECURITY.md, CONTRIBUTING.md are present
      and not placeholders.
- [ ] `.github/workflows/zizmor.yml` exists and is green. Once public,
      flip `advanced-security: "false"` / `annotations: "true"` back to
      `advanced-security: "true"` so findings land in the Security tab
      (requires GitHub Advanced Security, free for public repos).
- [x] `.github/workflows/release.yml` exists — verified 2026-08-31: builds
      from `py/`, uses OIDC (`id-token: write`, no API token), emits PEP 740
      Sigstore attestations, TestPyPI dry run gates the real publish. Before
      the first tag push, follow
      [pypi-trusted-publishing-setup.md](pypi-trusted-publishing-setup.md)
      end to end:
  - [ ] A `testpypi` GitHub Environment exists, pointed at a pending
        Trusted Publisher configured at
        <https://test.pypi.org/manage/account/publishing/> for
        `agent-audit-record` / this repo / `release.yml` /
        `publish-testpypi`.
  - [ ] A `pypi` GitHub Environment exists, pointed at a pending Trusted
        Publisher configured at
        <https://pypi.org/manage/account/publishing/> for
        `agent-audit-record` / this repo / `release.yml` /
        `publish-pypi`, with required reviewers set on the environment
        so a real PyPI publish needs manual approval.
  - [ ] A `workflow_dispatch` dry run (`testpypi-only: true`) has
        actually published a build to TestPyPI and it installs cleanly
        (`pip install -i https://test.pypi.org/simple/
        agent-audit-record`).
  - [ ] `agent-audit-record` is claimed on PyPI as more than "unclaimed
        as of the ADR-0002 check date" — a pending publisher only
        reserves the name once the first Trusted-Publishing upload
        actually lands.
- [x] M9 (OTel `mcp.*` PR): opened —
      [open-telemetry/semantic-conventions-genai#480](https://github.com/open-telemetry/semantic-conventions-genai/pull/480),
      2026-08-30. Built and validated (`make check-policies`,
      `make generate-all`) against upstream before opening. EasyCLA
      signed and all 41 checks passing as of 2026-08-30; sitting on
      `open-telemetry/semconv-genai-approvers` code-owner review —
      merging is on the upstream maintainers, not something we control
      or need to act on further.
