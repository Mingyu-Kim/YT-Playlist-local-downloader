# 🧭 Architecture

The app uses Python's standard HTTP server and plain HTML/CSS/JavaScript. Keeping source modules at the repository root is intentional: the source entry point and PyInstaller entry point are the same. No Node web build is required; bundled Node is only yt-dlp's JavaScript runtime.

| Path | Responsibility |
| --- | --- |
| app.py | Loopback routes, token/Host/Origin checks, lifecycle |
| platform_support.py | Native instance locks and folder dialogs/opening |
| console_ui.py | Console commands, status monitor, rotated logs |
| controller.py | Thread-safe session state, scan/review/download coordination |
| metadata.py | YouTube Music enrichment, MusicBrainz candidates, shared rate limit |
| downloads.py | MP3 encoding/tagging, inventory, source-tag scanning and safe reuse |
| text_rules.py | Published English components, Korean romanization, safe filenames |
| common.py | App paths, bundled tools, atomic JSON writes |
| web/ | Bilingual UI, themes, review editor and embedded preview |
| tests/ | Offline regression tests with temporary state/audio |
| scripts/ | Verified tools, native FFmpeg, packaging and release smoke tests |

## State and concurrency

`Controller.lock` protects shared state. The main worker runs playlist analysis, local-folder loading or final publication. During analysis, two background workers fetch/encode audio into a controller-owned temporary staging directory while metadata is resolved and edited. They never publish user-visible music; final publication uses committed review metadata. Workers join before the main operation ends; cancellation also interrupts retry backoff. Staging is cleared on a new scan and after publication, and is not restored across restarts. Completed analysis results are appended once and become reviewable. HTTP edit requests copy one track, resolve metadata outside the lock using a separate client, then atomically commit. `state.editing` prevents conflicting edits or starting downloads/new scans. MusicBrainz throttling is shared across clients. Shutdown cancels the main worker and waits for active edits.

Session JSON is saved atomically. Restoring an interrupted operation resets transient busy/editing state. Browser polling must not reset open editor fields or recreate a playing iframe.

## Data and audio safety

`library.sqlite3` is a cache, not the only source of identity. Scan MP3 descendants (excluding symlinks, directory junctions and temporary work directories) for `TXXX:YOUTUBE_ID`, legacy source URLs and `WOAS`. Conflicting identifiers and invalid MP3s are ignored. `YTPL_PROFILE` records the applied metadata profile. File SHA-256 detects external changes. Work happens in a temporary directory under the output directory, then atomic replacement publishes an existing owned file; new destinations use no-clobber rename on Windows or hard links on macOS (exclusive-copy fallback on filesystems without hard links); unrelated files must never be overwritten.

New audio: yt-dlp → FFmpeg/libmp3lame 320 kbps → Mutagen ID3v2.3. Reuse: verify/copy audio → retag if needed → publish. Preserve album art where available. Romanization applies to text metadata; URLs/IDs remain machine identifiers.

Custom filenames use validated `{artist}`, `{title}`, `{album}`, `{track}`, `{decade}` tokens. Folder choices are flat, artist, decade or both orders; missing dates map to `Unknown decade`. Components are sanitized and resolved paths must remain within the selected root. Explicit layout changes also rename matching-profile files. Local-folder records carry a path-derived ID and the loaded file digest, independent of YouTube identity; source tags, artwork and unedited frames are preserved when retagging. Local files are never fetched from the network. Unsafe or externally changed sources fail before publication. Empty folders are left in place.

Audio transfer and conversion use an initial attempt plus five cancellable retries (1, 2, 4, 8, 16 seconds); yt-dlp internal transfer retries are disabled to avoid multiplying attempts. Filesystem publication and local safety failures are not automatically retried.

## API

`GET /api/state`, `GET /api/track/<id>`; POST `preview-layout`, `load-folder`, `analyze`, `edit`, `download`, `cancel`, `options`, `folder`, `open-output`, `quit`. Every API request requires the app token; exact Host and same-origin checks are retained. Static scripts/styles are local. CSP permits only the YouTube iframe as an external frame.

## Known constraints

No authenticated/private playlists; upstream APIs can change. Embedded preview playback may be restricted. No translations or guaranteed complete metadata. UI strings are maintained in web/app.js. There is no formal schema migration framework yet; extend persisted fields compatibly. Live-network tests are explicit opt-in only.
