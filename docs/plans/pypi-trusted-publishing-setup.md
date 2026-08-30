# PyPI Trusted Publishing setup — step by step

This is the precise sequence to make `.github/workflows/release.yml`
actually work. It's out-of-band from anything a session working in this
repo can do — every step below requires your own PyPI/TestPyPI account
and your own GitHub repo settings access.

Do TestPyPI first, all the way through a successful dry run, before
touching real PyPI — the workflow is built the same way so this also
proves the real path will work.

## 1. Register the pending publisher on TestPyPI

1. Sign in (or create an account) at <https://test.pypi.org/>.
2. Go to <https://test.pypi.org/manage/account/publishing/>.
3. Under "Add a new pending publisher", fill in:
   - **PyPI Project Name:** `agent-audit-record`
   - **Owner:** `katekruger`
   - **Repository name:** `agent-audit`
   - **Workflow name:** `release.yml`
   - **Environment name:** `testpypi`
4. Submit. TestPyPI now trusts a `publish-testpypi` job in
   `release.yml` on this repo, scoped to the `testpypi` GitHub
   Environment — no API token involved.

## 2. Create the `testpypi` GitHub Environment

1. In the `agent-audit` repo: Settings → Environments → New environment
   → name it exactly `testpypi`.
2. No protection rules are required here — TestPyPI dry runs shouldn't
   need manual approval, or the dry run stops being a quick way to
   check things work.

## 3. Run the dry run

```bash
gh workflow run release.yml -f testpypi-only=true
```

Or trigger it from the Actions tab with `workflow_dispatch`, leaving
`testpypi-only` at its default (`true`).

Watch the `publish-testpypi` job. It should succeed and the run summary
should link to the TestPyPI project page.

## 4. Verify the dry-run artifact actually installs

```bash
pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  agent-audit-record
python -c "import agent_audit_record; print(agent_audit_record.__file__)"
```

(`--extra-index-url` is needed because `agent-audit-record`'s real
dependencies — `opentelemetry-api`/`-sdk` — aren't on TestPyPI.)

If this fails, fix it and re-run step 3 before touching real PyPI —
don't skip straight to a real publish because the TestPyPI job
"probably" would have worked.

## 5. Register the pending publisher on real PyPI

Repeat step 1 at <https://pypi.org/manage/account/publishing/> with
one difference: **Environment name:** `pypi` (not `testpypi`).

This is also the point where `agent-audit-record` actually gets
reserved on PyPI — a pending publisher claims the name even before the
first real upload happens. Before this step, "unclaimed as of the
ADR-0002 check date" is not the same as reserved; someone else could
still register it in the meantime.

## 6. Create the `pypi` GitHub Environment, with a required reviewer

1. Settings → Environments → New environment → name it exactly `pypi`.
2. Under "Deployment protection rules," add yourself (or whoever should
   approve a real release) as a required reviewer.

This is the actual safety gate: `release.yml`'s `publish-pypi` job runs
only after `publish-testpypi` succeeds AND a human clicks approve on
the `pypi` environment. Without this, pushing a `v*.*.*` tag would
publish to real PyPI unattended the moment CI and the TestPyPI dry run
both pass.

## 7. Cut the real release

```bash
git tag -a v0.1.1 -m "..."   # or whatever the next real version is
git push origin v0.1.1
```

Approve the `pypi` environment deployment when prompted in the Actions
run. `publish-pypi` then runs, attaching PEP 740 Sigstore attestations
and GitHub build provenance automatically (already wired into
`release.yml` — nothing more to configure).

## Checking your work

- <https://test.pypi.org/project/agent-audit-record/> should show at
  least one dev release after step 3.
- <https://pypi.org/manage/account/publishing/> should list
  `agent-audit-record` as a pending publisher immediately after step 5,
  and as a normal (non-pending) publisher after the first real release
  in step 7.
- `pip download agent-audit-record` (no `--index-url` override) should
  work from the real index after step 7, and its attestations should be
  visible on the PyPI project page under "View details" on the release.

Once all of this is done, update the corresponding checklist items in
[going-public-checklist.md](going-public-checklist.md).
