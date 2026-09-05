# Contributing to MovingOut

<!-- test PR to surface the CI status check in GitHub's ruleset picker -->

Thanks for wanting to contribute! This project is licensed under the
[PolyForm Noncommercial License 1.0.0](LICENSE): contributions are welcome
for any noncommercial purpose (personal use, hobby, learning, research,
etc.). By opening a pull request you agree that your contribution is made
under the same license as the rest of the project (this is also how GitHub's
Terms of Service already treat pull requests opened against a public repo).

## Workflow

1. **Fork** the repository.
2. **Create a branch** off `main` for your change — don't commit directly to
   `main`:
   - `feature/<short-description>` for new functionality
   - `fix/<short-description>` for bug fixes
3. Make your changes and keep commits focused and readable.
4. Open a **pull request** against `main`. The CI checks (syntax + lint) must
   pass before a PR can be merged.
5. Be responsive to review feedback — small, focused PRs get reviewed faster.

## Before opening a PR

The project has no external dependencies (standard library only), so setup
is minimal:

```bash
# Syntax check
python3 -m compileall -q movout

# Lint (catches unused imports, undefined names, etc.)
python3 -m pip install ruff
python3 -m ruff check movout --select E9,F

# Shell scripts, if you touched install.sh or packaging/
shellcheck install.sh packaging/build-deb.sh
```

## Code style

Keep changes consistent with the existing style in the file you're editing —
no new dependencies, no unrelated refactors bundled into a bug-fix PR.

## Reporting issues

Open a GitHub issue with steps to reproduce, your distro, and the exact
command you ran.
