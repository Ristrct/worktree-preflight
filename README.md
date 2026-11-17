# Worktree Preflight

Run this when Git works in your terminal but fails or sees the wrong checkout inside a coding agent. It checks the current directory, tries Git with the checkout you intended to use, then tries again with common Git path overrides removed from the child process.

Requires Python 3.10+ and Git. Run the same command inside the agent and in your normal terminal.

```powershell
python path/to/preflight.py --expected "C:/projects/my worktree"
```

Here’s a real Windows run from a different checkout. Git could read both repositories, and the report showed that only the explicit path selected the intended one.

```text
Git override variables present: none
Current directory: root=DIFFERENT checkout | status=OK
Explicit checkout: root=expected checkout | status=OK
Explicit checkout without listed overrides: root=expected checkout | status=OK
Git works when pointed directly at the expected checkout.
```

[Watch the 20-second demo](demo.mp4).

Pass the root of the intended checkout. You can paste the report into a bug issue. It shows which checks passed and the names of any Git path overrides. It omits their values, checkout paths, Git output, and file names. The status probe skips untracked files and submodules and disables optional locks and filesystem monitoring.

Exit codes are `0` when the current and explicit checkout checks pass, `1` when either check finds a problem, and `2` when the probe cannot complete. Compare reports before changing Git settings or sandbox permissions. This tool tests which checkout Git can read. Fixing the agent's routing or sandbox is up to the host.

Inspired by [Codex issue #52527](https://github.com/openai/codex/issues/52527) and [Codex issue #42797](https://github.com/openai/codex/issues/42797).
