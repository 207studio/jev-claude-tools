# Upstream services and related projects

This repository publishes skills, configuration and scripts written for this toolkit. It does not redistribute installed upstream packages, model weights, or vendor archives.

- [TypeSafe](https://docs.typesafe.ai/) supplies the hosted Jev decision API. Use is subject to TypeSafe's service terms and pricing.
- [jev-codex-tools](https://github.com/207studio/jev-codex-tools) is our Codex-side toolkit. The skills here call its CLIs (`jev-judge`, `jev-verify`, `jev-aside`, `jev-macos`, `jev-ios`) and its `jev_context` MCP server. It is a separate repository, not bundled.
- [ddfeyes/jev-mode](https://github.com/ddfeyes/jev-mode) (MIT) is the batch-judgment CLI behind the `jev-mode` skill. The skill's `references/batch.md` adapts its measured question-design guidance; the upstream notice is kept there. The CLI itself is not bundled.
- [fast-jev-compaction](https://github.com/tamaratran/fast-jev-compaction) is a separate Claude Code plugin that replaces the compaction summary with Jev decisions. Not bundled.
- [jev-router](https://github.com/gargpratyush/jev-router) is a separate per-turn model router. Not bundled. See [findings](docs/FINDINGS.md) §5 before installing it next to jev-codex-tools.
- [jevprune](https://github.com/ibrahemid/jevprune) is a separate output-filtering tool with its own Claude Code skill. Not bundled; install it from upstream.
- Claude Code, Codex, Aside, Apple's accessibility APIs and serve-sim are external host tools or interfaces. Their presence is not permission for a particular operation.

Third-party names identify integrations, not endorsement. Preserve upstream notices if you redistribute upstream code. The MIT license here covers this repository's own files; it does not relicense external services or tools.
