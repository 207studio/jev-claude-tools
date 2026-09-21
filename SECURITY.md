# Data handling and security boundaries

Jev is an external API. A judgment sends the explicitly selected file, record, search candidate or UI label and a question to TypeSafe. `jev-code-search` sends each ripgrep candidate passage. Don't point these tools at material you aren't authorized to send to that service.

**Keep your key out of prompts, request files and commits.** The scripts read it from an env file (`--env-file`). Some plugins ask you to put `TYPESAFE_API_KEY` in `~/.claude/settings.json`; if you do, that file now holds a secret — don't share or commit it, and remember any backups of it hold the same secret. This repository's `.gitignore` excludes `settings.json`, `.claude.json`, env files and backups for that reason.

Skills are instructions your agent will follow. Read a skill before installing it, including these. We screened 101 third-party Jev skills for destructive, exfiltration, credential-handling, guard-bypass and remote-code instructions before deciding not to install them; a model's "no risk" verdict at low confidence is not a clearance.

`jev-verify` may choose whether or which **supplied** verification to run. It must not generate executable commands, and a SKIP is "not run", never "passed". `jev-action-control` executes only actions you already allowed, rechecks state before acting, and stops on low confidence or permission denial.

`scripts/weekly-sweep.sh` is read-only: it measures, checks and searches, and installs or modifies nothing. Nothing here registers hooks or changes Claude Code permissions on its own.

This is an experimental extraction from one person's setup and has not been security-audited.

Report vulnerabilities through GitHub private vulnerability reporting if it's enabled on this repository. Otherwise open an issue with a non-sensitive description and ask for a private channel. Never put real credentials or session data in a public issue.
