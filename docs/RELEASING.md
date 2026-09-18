# 📦 Native builds and releases

## Targets

Python **3.14.0**; Windows x64, macOS Apple Silicon and macOS Intel. Build each target on that OS/architecture—PyInstaller does not cross-build macOS executables on Windows. CI uses `windows-2022`, `macos-15` (arm64) and `macos-15-intel` (x64). macOS outputs are console binaries with an executable `Launch.command`; this preserves the visible terminal behavior.

## Build prerequisites

- Windows: Python 3.14.0 and Git; use an MSYS2 UCRT64 shell with `make`, `diffutils`, `mingw-w64-ucrt-x86_64-gcc`, and `mingw-w64-ucrt-x86_64-pkgconf` (CI provisions these). A local portable w64devkit toolchain also works; run the shell recipe with Git Bash and keep Git Bash utilities first on PATH, followed by the toolchain bin. With Git under Program Files, set `BUILD_SHELL=C:/PROGRA~1/Git/usr/bin/sh.exe` to avoid native Make splitting the shell path. `SKIP_LAME_CONFIGURE=1` is only for retrying a completed local configuration, never fresh CI builds.
- macOS: Python 3.14.0 and Xcode Command Line Tools (`clang`, `make`). Native system folder picker uses AppleScript, avoiding threaded Cocoa/Tk calls.
- Create/activate `.venv`, then install `requirements/dev.txt`.

```sh
python scripts/prepare_tools.py
bash scripts/build_ffmpeg.sh
python -m pytest
python -m ruff check .
# Windows uses tools/node.exe
./tools/node --check web/app.js
python scripts/build.py
python scripts/smoke_release.py
python scripts/collect_sources.py
python scripts/package_release.py
```

`prepare_tools.py` verifies checksums in `scripts/tools.lock.json`, downloads official Node and extracts FFmpeg/LAME sources into ignored `.vendor/`. `build_ffmpeg.sh` compiles a static audio helper from those exact sources. It intentionally disables autodetected third-party codecs and network access; yt-dlp handles downloads. Build outputs and source downloads must never be committed.

The package script reads committed source (`git archive HEAD`). **Commit all release changes before packaging**; do not distribute a binary built from changes absent from the source archive. Check `VERSION`, changelog and README together. Test release artifacts after extraction, including paths with spaces/non-ASCII characters, folder picker, repeat launch, Ctrl+C, source-tag reuse and bilingual UI.

## GitHub release flow

1. Merge tested changes into `main` and set VERSION (e.g. `0.1.0`).
2. Tag the matching commit: `git tag v0.1.0` and `git push origin v0.1.0`.
3. The release workflow prepares a **draft**, builds/tests each native target, and uploads binaries, corresponding sources and checksums directly to that draft.
4. The final job checks all nine assets and updates the draft notes only after all builds pass. Failed builds leave an incomplete draft; never publish it. Inspect assets, source bundles and platform results before publishing.
5. Manual workflow dispatch on a branch validates packages without uploading or publishing; tag dispatch resumes the draft flow.

Pull-request CI has read-only permissions. Only the release publishing job gets `contents: write`; actions are pinned to commit SHAs. Dependency updates are proposed monthly. No signing key, Apple account or external credential is required for unsigned draft builds.

## Signing and limitations

Windows Authenticode and Apple Developer ID/notarization are not configured. Do not claim that unsigned builds are signed or bypass Gatekeeper/SmartScreen as part of the release process. A maintainer can add signing using protected CI environments and narrowly scoped secrets later. CI passing does not replace a real-device playback/UI test.

## License/source gate

Ship each native ZIP alongside its matching `-sources.zip` and checksums. Keep THIRD_PARTY_NOTICES.md accurate. A source-only GitHub archive is insufficient for bundled dependencies. Sources and license notices are generated from the actual build environment. See the distribution instructions there before mirroring or modifying releases.

## Strict free-runner policy

Run hosted CI and release jobs only in public repositories, using standard `windows-2022`, `macos-15`, `macos-15-intel` and `ubuntu-latest` runners. Every hosted job is guarded with `github.event.repository.private == false`; private repositories must build/package locally. Do not introduce larger/custom runners, Actions artifact uploads, paid caches, or a paid fallback. Release ZIPs go directly to GitHub Release assets; no Actions artifact storage is used. macOS remains supported because these standard runners are free for public repositories. See https://docs.github.com/en/billing/concepts/product-billing/github-actions.

These workflow guards do not change account billing settings or prevent charges from unrelated repositories or older workflow revisions. Recheck GitHub's pricing before changing this policy.
