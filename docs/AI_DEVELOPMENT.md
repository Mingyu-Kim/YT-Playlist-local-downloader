# 🤖 Improving the app with an LLM

Give your coding assistant the repository, **AGENTS.md**, **docs/ARCHITECTURE.md**, and the relevant task. Those files are the shared project context; there is no dependency on a particular LLM vendor.

Example task:

> Read AGENTS.md and docs/ARCHITECTURE.md. Improve [specific behavior]. Preserve existing metadata, file-safety and bilingual UI contracts. Add a regression test using temporary state and no real network downloads. Run relevant checks and summarize changes, evidence and remaining limitations.

For a UI task:

> Add [control] in English and Korean. Preserve system themes and accessibility labels. Do not interrupt active previews or overwrite unsaved editor fields while polling. Verify the local UI using isolated test data.

For release work:

> Read docs/RELEASING.md and THIRD_PARTY_NOTICES.md. Update only the intended dependency/tool versions and checksum manifest. Keep source archives and notices aligned. Run native tests and packaged smoke checks. Report unavailable platforms honestly.

## Review checklist

- Does the change solve the reported issue without touching personal files?
- Are all network requests outside the shared state lock?
- Can cancellation, restart and database-loss reuse still work?
- Are English/Korean text, docs and tests updated together?
- Are dependency sources/licenses included and checksums verified?
- Did the assistant actually run the checks it reports?

## 🇰🇷 사용 예시

> AGENTS.md와 docs/ARCHITECTURE.md를 읽고 [구체적인 기능]을 개선해 주세요. 기존 파일 안전성·메타데이터·한영 UI 규칙을 유지하세요. 실제 음악 대신 임시 파일로 회귀 테스트를 작성하고, 실행한 검사와 확인하지 못한 부분을 구분해서 보고해 주세요.
