# Instructions for coding agents

Read this file, README.md (or README.ko.md), docs/ARCHITECTURE.md and the relevant tests before editing. These instructions apply throughout this repository.

## Product contract

- This is YT-PL-Downloader, independent of MusicManager. No Tidal or backups/history UI. Date organization uses decades, never individual-year folders.
- Local loopback web server + native console executable. Preserve `o`, `s`, `q`, Ctrl+C and single-instance locking on Windows/macOS.
- Output: user-defined filename format and flat/artist/decade folder structure; default Artist - Title MP3 in a flat folder. 320 kbps for new downloads. Do not re-encode existing audio to change tags.
- Prefer published English metadata; never translate/guess music identities. Optional Korean Revised Romanization applies to ALL textual tags and filenames.
- Review completed songs during search; prefetch audio during scan/review into temporary staging, but publish only after scan and edits finish. Preserve committed edits. Network operations must not hold the controller state lock.
- Keep completed staged audio through failed/cancelled saves and reuse it without another download or encode. A missing supplied staged file must fail visibly. Staging is session-scoped.
- After successful moves, remove only empty old parent directories within the output root; preserve the root, symlinks/junctions, nonempty directories and unrelated empty folders.
- Recover downloads from embedded YouTube source identifiers, not filenames. Protect unrelated files and detect changed files before overwriting.
- Maintain EN/KO labels, system light/dark theme, keyboard labels, and preview stop behavior.

## Engineering rules

- Read THIRD_PARTY_NOTICES.md before adding dependencies. Project license is GPL-3.0-or-later; preserve notices and ship corresponding source for release bundles.
- Keep Host/Origin/token checks and 127.0.0.1 binding. Never expose the API remotely or log tokens/cookies.
- All test files, audio and state go in temporary directories. Never use the user's library, Data folder, credentials or live playlists for default tests.
- Use platform_support.py for OS behavior. Keep helper processes hidden on Windows while the main console remains visible.
- Preserve source tags/profile recovery and atomic JSON writes. Test cancellation, collisions and database-loss reuse for relevant changes.
- Do not commit executables, downloads, .venv, tools binaries, personal logs, tokens, session state or VERIFICATION.json.
- Keep changes focused. Existing compact formatting is technical debt, not a reason to reformat unrelated modules.
- Actions must use only standard windows-2022 and ubuntu-latest runners in public repositories. No macOS Actions jobs; macOS builds are local only. Guard every hosted job against private repositories. No paid runners, artifact storage, caches or paid fallback; use local builds for private repositories.

## Validation and handoff

Install requirements/dev.txt; prepare native tools as described in docs/RELEASING.md. Run `python -m pytest`, `python -m ruff check .`, and `tools/node --check web/app.js` (Windows: tools/node.exe).
For release changes also run `python scripts/build.py` and `python scripts/smoke_release.py`. Build each OS natively; never claim Mac validation from a Windows-only run.
Update both READMEs for user-visible behavior, CHANGELOG.md for changes, and architecture/build docs when contracts change. Report changed behavior, tests, and unverified limitations. Do not fabricate test evidence, repository links, signatures or notarization.
