# 🎵 YT-PL-Downloader

**A local YouTube Music playlist downloader for your music folder.**

[한국어](README.ko.md) · [Releases](https://github.com/Mingyu-Kim/YT-Playlist-local-downloader/releases) · [Contributing](CONTRIBUTING.md) · [LLM guide](AGENTS.md)

## ✨ Features

- 🎧 MP3 **320 kbps**, album art, lyrics and available credits.
- 🔎 YouTube Music + MusicBrainz metadata; review songs while the remaining search continues.
- ▶️ Play/stop previews and clickable YouTube Music titles.
- 🌏 English metadata preferred; optional Korean romanization (`안녕 → Annyeong`).
- 🚗 One flat folder, with `Artist - Title.mp3` filenames.
- ♻️ Embedded YouTube identifiers prevent duplicate downloads—even after renaming files or losing the database.
- 🌓 English/Korean interface, system light/dark theme, visible terminal logs.

## 📦 Download & run

Choose your platform from **[Releases](https://github.com/Mingyu-Kim/YT-Playlist-local-downloader/releases)**:

| Platform | Release archive | Launch |
| --- | --- | --- |
| Windows x64 | `YT-PL-Downloader-<version>-windows-x64.zip` | Double-click `YT-PL-Downloader.exe` |
| macOS Apple Silicon | `YT-PL-Downloader-<version>-macos-arm64.zip` | Double-click `Launch.command` |
| macOS Intel | `YT-PL-Downloader-<version>-macos-x64.zip` | Double-click `Launch.command` |

Each archive includes a native executable, bundled Node/FFmpeg, notices and checksums. No Python or Node installation is needed. macOS artifacts are built on macOS; availability depends on successful release CI. Builds are currently unsigned and not Apple-notarized. Do not disable system security protections; use a trusted source build if your system rejects an unsigned download.

1. Launch the app. A terminal shows the local URL and opens your browser.
2. Paste a **public or unlisted YouTube Music playlist**, choose an output folder, then select **Find songs & metadata**.
3. Review/edit songs as they appear. Use **▶ / ■** to preview/stop, or click a title to open YouTube Music.
4. Resolve uncertain matches, then select **Download songs**. Searching and pending edits finish before downloading.
5. Keep the terminal open. Type **`o` + Enter** to reopen the browser, **`s`** for status, or **`q`** to quit. **Ctrl+C** also quits.

> YouTube audio is already lossy; 320 kbps MP3 does not restore lost detail. Metadata is included when available, never invented. Romanization is transliteration, not translation. Embedded playback may be restricted; title links are the fallback. Only download material you are authorized to download and follow applicable service terms.

## ♻️ Existing music & privacy

Before downloading, the app scans MP3s directly in the selected folder. YouTube ID/source tags restore the inventory when files or the database move. Old tagged files are upgraded without re-downloading audio. Untagged or damaged files are not matched by filename. Metadata changes reuse and retag existing audio.

The server listens on **127.0.0.1 only**, with a random port, request token and Host/Origin checks. There is no remote control or telemetry service. YouTube/YouTube Music, MusicBrainz and artwork hosts receive requests needed for downloads, lookups and previews. Private/sign-in-only playlists are not supported.

| Local state | Location |
| --- | --- |
| Windows | `%LOCALAPPDATA%\YT-PL-Downloader` |
| macOS | `~/Library/Application Support/YT-PL-Downloader` |

This folder contains the current session, metadata cache, SQLite inventory and rotated logs. Music goes to your chosen folder. Never include personal state/cookies in bug reports. This app is independent of MusicManager and has no backup/history UI.

## 🛠️ Develop

Python **3.14**, Git, and a native compiler for the bundled FFmpeg build:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS: source .venv/bin/activate
python -m pip install -r requirements/dev.txt
python scripts/prepare_tools.py
# Build FFmpeg from the verified sources (see docs/RELEASING.md):
bash scripts/build_ffmpeg.sh
python app.py
python -m pytest
python -m ruff check .
python scripts/build.py
```

See [release/build instructions](docs/RELEASING.md) for Windows compiler setup, native Mac builds, source bundles, checksums and signing limitations. `--no-browser` and `--data-dir PATH` support isolated testing.

## 🤝 Contribute

Start with [CONTRIBUTING.md](CONTRIBUTING.md), [architecture](docs/ARCHITECTURE.md), and [AGENTS.md](AGENTS.md). Give an LLM those files plus your specific task; [AI examples](docs/AI_DEVELOPMENT.md) describe focused workflows. Tests must use temporary folders and must not download real playlists by default.

## ⚖️ License

Project code: **[GPL-3.0-or-later](LICENSE)**. Copyright © 2026 Mingyu Kim and contributors. Third-party components retain their own licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Release workflows package corresponding sources, build recipes and dependency notices alongside binaries. The license does not grant rights to music or third-party metadata.
