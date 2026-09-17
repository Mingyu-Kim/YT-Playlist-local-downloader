# 📦 Native builds and releases

## Targets

Python **3.14.0**; Windows x64, macOS Apple Silicon and macOS Intel. Build each target on that OS/architecture—PyInstaller does not cross-build macOS executables on Windows. CI uses `windows-2022`, `macos-15` (arm64) and `macos-15-intel` (x64). macOS outputs are console binaries with an executable `Launch.command`; this preserves the visible terminal behavior.

## Build prerequisites

- Windows: Python 3.14.0 and Git; use an MSYS2 UCRT64 shell with `make`, `diffutils`, `mingw-w64-ucrt-x86_64-gcc`, and `mingw-w64-ucrt-x86_64-pkgconf` (CI provisions these). A local portable w64devkit toolchain also works; run the shell recipe with Git Bash and put the toolchain bin first on PATH.
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
3. The release workflow builds/tests each native target, collects notices and corresponding sources, and uploads checksummed artifacts.
4. A **draft** GitHub Release is created only after all builds pass. Inspect assets, source bundles and platform results before publishing it.
5. Manual workflow dispatch builds validation artifacts without publishing a release.

Pull-request CI has read-only permissions. Only the release publishing job gets `contents: write`; actions are pinned to commit SHAs. Dependency updates are proposed monthly. No signing key, Apple account or external credential is required for unsigned draft builds.

## Signing and limitations

Windows Authenticode and Apple Developer ID/notarization are not configured. Do not claim that unsigned builds are signed or bypass Gatekeeper/SmartScreen as part of the release process. A maintainer can add signing using protected CI environments and narrowly scoped secrets later. CI passing does not replace a real-device playback/UI test.

## License/source gate

Ship each native ZIP alongside its matching `-sources.zip` and checksums. Keep THIRD_PARTY_NOTICES.md accurate. A source-only GitHub archive is insufficient for bundled dependencies. Sources and license notices are generated from the actual build environment. See the distribution instructions there before mirroring or modifying releases.
