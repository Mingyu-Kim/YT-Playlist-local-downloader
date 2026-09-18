# 🤝 Contributing / 기여 안내

Thanks for helping improve YT-PL-Downloader. Read [AGENTS.md](AGENTS.md) and [architecture](docs/ARCHITECTURE.md) before making changes.

1. Open an issue describing the problem and intended behavior. For small fixes, a focused pull request is enough.
2. Create a branch (`fix/...`, `feat/...`, or `docs/...`) from `main`.
3. Set up Python 3.14 and `requirements/dev.txt`; follow [native tool setup](docs/RELEASING.md).
4. Add regression tests for behavior changes. Default tests are offline and use temporary paths.
5. Run `python -m pytest`, `python -m ruff check .`, and `tools/node.exe --check web/app.js` on Windows (`tools/node --check web/app.js` for local macOS development).
6. Update English/Korean documentation and the changelog when relevant.
7. Explain the problem, final behavior, tests and limitations in the PR. Include screenshots for UI changes when useful.

For download or organization changes, cover staged-audio reuse after failure/cancellation, collisions, changed-file protection, database-loss recovery, and empty-directory cleanup boundaries. Tests must not transfer real songs. Keep the output root and unrelated files/directories intact.

Hosted automation builds Windows only on public repositories using the allowed standard runners. Do not add macOS jobs, larger/custom runners, Actions artifact storage, paid caches or a paid fallback. Follow [RELEASING.md](docs/RELEASING.md) for local builds and source-matched packages; local packaging and GitHub publication are separate actions.

Never attach real music, cookies, tokens, personal library databases, absolute personal paths or unredacted logs. AI-assisted contributions are welcome; the contributor must review the code and run validation. [AI development guide](docs/AI_DEVELOPMENT.md).

By submitting a contribution, you agree to license it under GPL-3.0-or-later. Retain third-party attribution. No separate CLA is required. Be respectful and give actionable technical feedback.

## 🇰🇷 요약

`main`에서 작업 브랜치를 만들고 변경 범위를 작게 유지하세요. 동작 변경은 임시 폴더 기반 테스트로 검증하고, 사용자에게 보이는 변경은 영문·한글 README에 반영하세요. 개인 음악·로그·DB·쿠키를 올리지 마세요. AI가 만든 코드도 직접 검토하고 테스트해야 합니다. 기여 코드는 GPL-3.0-or-later로 제공됩니다.
