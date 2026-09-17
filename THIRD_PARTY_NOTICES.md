# ⚖️ Third-party notices and corresponding source

YT-PL-Downloader's original code is GPL-3.0-or-later (Copyright © 2026 Mingyu Kim and contributors). The full license is in LICENSE. This choice is consistent with the GPL-3.0-or-later korean-romanizer dependency and Mutagen's GPL-2.0-or-later license. Third-party code is not relicensed under the project copyright.

| Component | License / role | Upstream |
| --- | --- | --- |
| korean-romanizer | GPL-3.0-or-later; romanization | https://github.com/osori/korean-romanizer |
| Mutagen | GPL-2.0-or-later; audio tags | https://github.com/quodlibet/mutagen |
| yt-dlp / yt-dlp-ejs | Unlicense / ISC; media extraction and JS support | https://github.com/yt-dlp/yt-dlp · https://github.com/yt-dlp/ejs |
| ytmusicapi | MIT; metadata | https://github.com/sigma67/ytmusicapi |
| RapidFuzz / Pillow / Requests | MIT / HPND-style / Apache-2.0; matching, images, HTTP | Package notices in release licenses/ |
| FFmpeg | LGPL-2.1-or-later for this build; no GPL/nonfree options | https://ffmpeg.org |
| LAME | LGPL-2.0-or-later; MP3 encoder | https://lame.sourceforge.io |
| Node.js | MIT plus bundled third-party notices | https://nodejs.org |
| CPython | PSF license and included third-party notices | https://python.org |
| PyInstaller | GPL-2.0-or-later with bootloader distribution exception | https://pyinstaller.org |

Release archives include collected notices for installed dependencies, native tools, and Python, with exact versions in `dependencies.json`. Node's upstream LICENSE includes its bundled components. FFmpeg is built locally from pinned source using only native audio decoding and static LAME; no prebuilt FFmpeg downloaded through imageio is used for official releases.

## Distribution

Always distribute the binary ZIP **together with** its matching `-sources.zip` and `.sha256` file, on the same release page. The source ZIP contains project source, build scripts, exact FFmpeg/LAME/Node/CPython sources and source distributions of the Python dependencies used for that platform. `sources.json` records checksums and upstream URLs. GitHub's automatically generated repository source ZIP alone does not contain bundled dependency sources.

Retain all notices, preserve the GPL license and provide the corresponding source when redistributing modified builds. The scripts fail if dependency sources cannot be obtained; investigate missing sources rather than substituting an unrelated version. Source-built audio helpers can be rebuilt/modified using the provided recipe. Build/CI tools and system libraries retain their own terms.

The app's license does not grant permission to download copyrighted music or reuse third-party artwork, lyrics or metadata. YouTube, MusicBrainz and other services are independent and do not endorse this project.

References: [FFmpeg license guidance](https://ffmpeg.org/legal.html), [GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0.html), [PyInstaller license exception](https://pyinstaller.org/en/stable/license.html).
