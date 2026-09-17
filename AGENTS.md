# Instructions for coding agents

Read this file, README.md (or README.ko.md), docs/ARCHITECTURE.md and the relevant tests before editing. These instructions apply throughout this repository.

## Product contract

- This is YT-PL-Downloader, independent of MusicManager. No Tidal, backups/history UI, or year folders.
- Local loopback web server + native console executable. Preserve `o`, `s`, `q`, Ctrl+C and single-instance locking on Windows/macOS.
- Output: flat folder, Artist - Title MP3, 320 kbps for new downloads. Do not re-encode existing audio to change tags.
- Prefer published English metadata; never translate/guess music identities. Optional Korean Revised Romanization applies to ALL textual tags and filenames.
- Review completed songs during search; no downloads until scan and edits finish. Preserve committed edits. Network operations must not hold the controller state lock.
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

## Validation and handoff

Install requirements/dev.txt; prepare native tools as described in docs/RELEASING.md. Run `python -m pytest`, `python -m ruff check .`, and `tools/node --check web/app.js` (Windows: tools/node.exe).
For release changes also run `python scripts/build.py` and `python scripts/smoke_release.py`. Build each OS natively; never claim Mac validation from a Windows-only run.
Update both READMEs for user-visible behavior, CHANGELOG.md for changes, and architecture/build docs when contracts change. Report changed behavior, tests, and unverified limitations. Do not fabricate test evidence, repository links, signatures or notarization.
