# Changelog

## Unreleased

## 0.2.0 — Custom organization and background downloads

- Add interactive filename fields and path previews with flat, artist, decade and combined folder layouts.
- Load existing MP3s recursively for metadata edits and safe reorganization without re-encoding.
- Prefetch audio during search/review and apply committed metadata only when saving.
- Retry failed audio transfers/conversions up to five times with cancellable backoff.
- Preserve collision protection, changed-file checks and embedded-source recovery across nested folders.

## 0.1.1 — Native release validation

- Avoid reverse DNS during loopback server startup, which stalled macOS CI.
- The initial 0.1.0 tag did not pass all native checks and was not released.

## 0.1.0 — Initial repository setup

- Local YouTube Music playlist downloads as tagged 320 kbps MP3.
- English/Korean UI, automatic themes and optional Korean romanization.
- Metadata review during background search, YouTube previews and title links.
- Portable embedded-source duplicate detection and metadata-only reuse.
- Console URL, status, logging and shutdown controls.
- Native Windows/macOS integration and three-platform release workflow.
- GPL-3.0-or-later license, dependency notices, source archives and contributor/LLM guides.

Platform validation is recorded by each release workflow; a listed feature is not a claim that every platform build has passed.
