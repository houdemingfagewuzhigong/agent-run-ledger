# Launch Promotion

Repository: https://github.com/houdemingfagewuzhigong/agent-run-ledger

## Hacker News

Title:

Show HN: Agent Run Ledger - track what each AI coding agent changed

Body:

I built a small zero-dependency CLI for teams using multiple coding agents in the same repo.

Agent Run Ledger records each agent run into `.agent-ledger/runs.json`, captures branch/commit, dirty files, diff stats, and flags risky handoffs like workflow changes, lockfile changes, secret-adjacent files, or very large diffs.

It can render an HTML timeline and export JSON/SARIF, so you can use it locally or in GitHub Actions before merging or handing the repo to another agent.

Repo: https://github.com/houdemingfagewuzhigong/agent-run-ledger

## Reddit r/opensource

I built Agent Run Ledger, a zero-dependency CLI for tracking what AI coding agents changed in a repository.

The idea is simple: if you use Codex/Cursor/Copilot/Claude Code/custom MCP tools in the same repo, every agent run should leave a receipt. The tool records branch, commit, dirty files, diff stats, and risk flags, then exports HTML, JSON, and SARIF.

Repo: https://github.com/houdemingfagewuzhigong/agent-run-ledger

I would appreciate feedback on what risk flags should be included by default.

## Reddit r/selfhosted

For anyone self-hosting coding-agent workflows or local MCP tools: I made Agent Run Ledger, a tiny Python CLI that records what each agent changed before you hand the repo to the next tool.

It stores a local `.agent-ledger/runs.json`, renders an HTML timeline, and exports SARIF/JSON for automation. No services, no dependencies.

Repo: https://github.com/houdemingfagewuzhigong/agent-run-ledger

## Reddit r/programming

AI coding agents make code edits cheap, but handoffs are messy. I built Agent Run Ledger to record what each agent changed: branch, commit, dirty files, diff stats, and risk flags for workflow/lockfile/secret-adjacent changes.

It is a zero-dependency Python CLI with HTML, JSON, and SARIF output.

Repo: https://github.com/houdemingfagewuzhigong/agent-run-ledger

## X Short Post

Built Agent Run Ledger: a zero-dependency CLI that records what each AI coding agent changed before the next handoff.

HTML timeline, JSON, SARIF, GitHub Actions friendly.

https://github.com/houdemingfagewuzhigong/agent-run-ledger

## X Long Post

When multiple AI coding agents touch the same repo, the hard part becomes handoff quality: what changed, who changed it, and what deserves review before the next agent runs?

I built Agent Run Ledger for that.

It records each run into `.agent-ledger/runs.json`, captures branch/commit, dirty files, diff stats, and flags risky changes like workflows, lockfiles, secret-adjacent files, and huge diffs.

It also exports HTML, JSON, and SARIF so it can work locally or in CI.

Repo: https://github.com/houdemingfagewuzhigong/agent-run-ledger
