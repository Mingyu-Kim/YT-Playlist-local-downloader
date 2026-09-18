# 🎵 YT-PL-Downloader

**A local YouTube Music playlist downloader for your music folder.**

[한국어](README.ko.md) · [Releases](https://github.com/Mingyu-Kim/YT-Playlist-local-downloader/releases) · [Contributing](CONTRIBUTING.md) · [LLM guide](AGENTS.md)

## ✨ Features

- 🎧 MP3 **320 kbps**, album art, lyrics and available credits.
- 🔎 YouTube Music + MusicBrainz metadata; review songs while the remaining search continues.
- ▶️ Play/stop previews and clickable YouTube Music titles.
- 🌏 English metadata preferred; optional Korean romanization (`안녕 → Annyeong`).
- 🚗 Custom filenames with live previews; flat, artist, decade, or combined folders.
- 📂 Load existing MP3s recursively to edit tags and reorganize without re-encoding.
- ⚡ Audio downloads in the background during review; failed audio transfers/conversions retry up to five times.
- ♻️ Embedded YouTube identifiers prevent duplicate downloads—even after renaming files or losing the database.
- 🌓 English/Korean interface, system light/dark theme, visible terminal logs.

## 📦 Download & run

Download the **Windows x64 ZIP** from [Releases](https://github.com/Mingyu-Kim/YT-Playlist-local-downloader/releases), extract it, then launch the executable:

| Platform | Release archive | Launch |
| --- | --- | --- |
| Windows x64 | `YT-PL-Downloader-<version>-windows-x64.zip` | Double-click `YT-PL-Downloader.exe` |

Each archive includes a native executable, bundled Node/FFmpeg, notices and checksums. No Python or Node installation is needed. Automated CI and new releases target Windows only. Existing macOS assets remain available in older releases; new macOS builds must be made locally on macOS. Builds are currently unsigned and not Apple-notarized. Do not disable system security protections; use a trusted source build if your system rejects an unsigned download.

1. Launch the app. A terminal shows the local URL and opens your browser.
2. Paste a **public or unlisted YouTube Music playlist**, choose an output folder, then select **Find songs & metadata**.
3. Review/edit songs as they appear. Use **▶ / ■** to preview/stop, or click a title to open YouTube Music.
4. Choose a filename format and folder structure using the live preview. Resolve uncertain matches, wait for scanning and active edits to finish, then select **Finish review & save songs** to apply the final tags and paths.
5. Keep the terminal open. Type **`o` + Enter** to reopen the browser, **`s`** for status, or **`q`** to quit. **Ctrl+C** also quits.

> YouTube audio is already lossy; 320 kbps MP3 does not restore lost detail. Metadata is included when available, never invented. Romanization is transliteration, not translation. Embedded playback may be restricted; title links are the fallback. Only download material you are authorized to download and follow applicable service terms.

## 🗂️ Filename and folder choices

Use the field buttons to insert `{artist}`, `{title}`, `{album}`, `{track}` or `{decade}` into **Filename format**. You can add separators such as ` - `; `.mp3` is appended automatically. Use **Folder structure** to choose directories rather than typing slashes into the filename format. The preview shows up to three songs, or a sample before loading songs.

For a song named *Song* by *Artist*, released in 2017:

| Filename format | Folder structure | Result |
| --- | --- | --- |
| `{artist} - {title}` | No organization | `Artist - Song.mp3` |
| `{title}` | Artist | `Artist/Song.mp3` |
| `{title}` | Decade | `2010s/Song.mp3` |
| `{title}` | Artist / decade | `Artist/2010s/Song.mp3` |
| `{track} - {title}` | Decade / artist | `2010s/Artist/1 - Song.mp3` (track 1) |

Dates are grouped into decades (`1990s`, `2000s`, `2010s`, `2020s`), never individual-year folders. Missing dates use `Unknown decade`. Optional Korean romanization also applies to filenames and metadata-derived folder names. Unsafe filename characters are replaced; collisions receive an identifier suffix or fail safely.

## ⚡ Background audio and retries

Audio downloads into temporary staging during metadata search and review. Saving copies the staged MP3 and applies your final edits without downloading or encoding the audio again. Songs marked **Skip song** are not saved to the target folder. Already verified local downloads are reused.

Failed or cancelled saves retain completed staged audio for retries in the same session. Audio that was not successfully prefetched is fetched into staging when you save. Transfers/conversions get one initial attempt plus up to five retries, with cancellable waits. Tag-writing, collision and changed-file errors need to be resolved before you retry saving.

A missing staged file is reported rather than silently re-downloaded. Start a new scan if you need to fetch it again. Starting a new scan or exiting the app clears staging; staged audio is not recovered after a restart. Successfully saved files remain reusable through their embedded YouTube identifiers.

## ♻️ Edit and reorganize existing music

1. Choose the folder containing your MP3s and select **Load songs from this folder**. No playlist URL is needed.
2. Review/edit the loaded songs, including files without YouTube tags. Add a title and artist where missing, or skip the song.
3. Choose the filename format and folder structure, check the preview, then select **Apply tags & folder structure**.

Loading scans subfolders too, excluding symbolic links, directory junctions and temporary work folders. Damaged/unreadable MP3s are skipped with a log entry. Existing audio is copied and retagged without re-encoding. Files changed since loading are protected; reload the folder before editing those files again.

After a successful move, empty old parent directories are removed up to (but not including) the target folder. Nonempty directories, linked directories and unrelated empty folders are left alone.

Before playlist downloads, the same recursive scan recovers existing music by embedded YouTube ID/source tags, even after files are renamed or the inventory database is lost. Untagged or damaged files are never matched by filename.

## 🔒 Privacy and local state

The server listens on **127.0.0.1 only**, with a random port, request token and Host/Origin checks. There is no remote control or telemetry service. YouTube/YouTube Music, MusicBrainz and artwork hosts receive requests needed for downloads, lookups and previews. Private/sign-in-only playlists are not supported.

| Local state | Location |
| --- | --- |
| Windows | `%LOCALAPPDATA%\YT-PL-Downloader` |
| macOS | `~/Library/Application Support/YT-PL-Downloader` |

This folder contains the current session, metadata cache, SQLite inventory, temporary staged audio and rotated logs. Music goes to your chosen folder. Never include personal state/cookies in bug reports. This app is independent of MusicManager and has no backup/history UI.

## 🛠️ Develop

Python **3.14.0**, Git, and a native compiler for the bundled FFmpeg build:

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
# Windows: tools/node.exe --check web/app.js
# macOS local build: tools/node --check web/app.js
python scripts/build.py
python scripts/smoke_release.py
```

See [release/build instructions](docs/RELEASING.md) for Windows compiler setup, native Mac builds, source bundles, checksums and signing limitations. `--no-browser` and `--data-dir PATH` support isolated testing.

CI and releases use only standard free hosted runners in public repositories. Hosted jobs skip private repositories; build locally instead. Release bundles upload directly to Release assets, without Actions artifact storage. macOS Actions jobs are disabled; macOS builds are local only.

## 🤝 Contribute

Start with [CONTRIBUTING.md](CONTRIBUTING.md), [architecture](docs/ARCHITECTURE.md), and [AGENTS.md](AGENTS.md). Give an LLM those files plus your specific task; [AI examples](docs/AI_DEVELOPMENT.md) describe focused workflows. Tests must use temporary folders and must not download real playlists by default.

## ⚖️ License

Project code: **[GPL-3.0-or-later](LICENSE)**. Copyright © 2026 Mingyu Kim and contributors. Third-party components retain their own licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Release workflows package corresponding sources, build recipes and dependency notices alongside binaries. The license does not grant rights to music or third-party metadata.
