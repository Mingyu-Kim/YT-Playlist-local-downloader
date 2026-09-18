# 🎵 YT-PL-Downloader

**YouTube Music 플레이리스트를 내 컴퓨터의 음악 폴더로 저장하는 앱입니다.**

[English](README.md) · [다운로드](https://github.com/Mingyu-Kim/YT-Playlist-local-downloader/releases) · [기여 안내](CONTRIBUTING.md) · [LLM 안내](AGENTS.md)

## ✨ 주요 기능

- 🎧 **320 kbps MP3**, 앨범 이미지·가사·제공되는 참여 아티스트 정보 저장.
- 🔎 YouTube Music + MusicBrainz 메타데이터 검색. 검색 중에도 먼저 표시된 곡을 검토·수정.
- ▶️ 미리 듣기/정지 및 제목을 통한 YouTube Music 바로가기.
- 🌏 영문 메타데이터 우선. 선택 시 한글을 로마자로 변환 (`안녕 → Annyeong`).
- 🚗 파일 이름 형식과 폴더 구조를 직접 지정하고 경로를 미리 확인.
- 📂 하위 폴더까지 기존 MP3를 불러와 재인코딩 없이 태그와 구조 변경.
- ⚡ 검토 중 백그라운드 음원 다운로드, 전송·변환 오류 시 최대 5회 재시도.
- ♻️ 파일에 YouTube 식별자를 저장해 파일명 변경·DB 분실 후에도 중복 다운로드 방지.
- 🌓 한국어/영어 UI, 시스템 밝은/어두운 테마, 터미널 상태·로그 표시.

## 📦 다운로드 및 실행

**[Releases](https://github.com/Mingyu-Kim/YT-Playlist-local-downloader/releases)**에서 운영체제에 맞는 파일을 선택하세요.

| 운영체제 | 배포 파일 | 실행 방법 |
| --- | --- | --- |
| Windows x64 | `YT-PL-Downloader-<version>-windows-x64.zip` | `YT-PL-Downloader.exe` 더블클릭 |
| macOS Apple Silicon | `YT-PL-Downloader-<version>-macos-arm64.zip` | `Launch.command` 더블클릭 |
| macOS Intel | `YT-PL-Downloader-<version>-macos-x64.zip` | `Launch.command` 더블클릭 |

Node/FFmpeg가 포함되어 Python·Node 별도 설치가 필요 없습니다. 라이선스 안내와 체크섬도 함께 제공합니다. macOS 파일은 macOS CI에서 빌드하며, 성공한 배포에만 포함됩니다. 현재 바이너리는 서명 및 Apple 공증이 없습니다. 시스템 보안을 해제하지 마세요. 서명되지 않은 앱이 차단되면 신뢰할 수 있는 소스에서 직접 빌드하세요.

1. 앱을 실행하면 터미널에 로컬 주소가 표시되고 브라우저가 열립니다.
2. **공개/일부 공개 YouTube Music 플레이리스트**와 저장 폴더를 입력하고 **곡과 메타데이터 찾기**를 누르세요.
3. 먼저 나타난 곡부터 검토·수정하세요. **▶ / ■**로 미리 듣기/정지하고 제목을 눌러 YouTube Music에서 확인할 수 있습니다.
4. 파일 이름 형식과 폴더 구조를 미리 보기로 확인하세요. 검토 중 음원은 임시 공간에 먼저 다운로드됩니다. 모호한 결과를 검토하고 **검토 완료 및 음악 저장**을 누르면 최종 태그와 경로가 적용됩니다. 제외한 곡은 저장하지 않습니다. 취소하면 전송·재시도가 중지됩니다. 앱 재시작 후 임시 음원은 복구하지 않습니다.
5. 터미널을 열어 두세요. **`o` + Enter**는 브라우저 열기, **`s`**는 상태, **`q`** 또는 **Ctrl+C**는 종료입니다.

> YouTube 원본은 손실 압축 음원입니다. 320 kbps 변환으로 원본에 없는 음질이 복원되지는 않습니다. 제공되고 확인된 메타데이터만 저장합니다. 로마자 변환은 번역이 아닙니다. 내장 재생이 제한된 곡은 제목 링크를 이용하세요. 다운로드 권한이 있는 콘텐츠에만 사용하고 서비스 이용 조건을 준수하세요.

## ♻️ 기존 음악과 개인정보

다운로드 전에 선택한 폴더와 하위 폴더의 MP3를 검사합니다. 심볼릭 링크, 디렉터리 정션, 임시 작업 폴더는 제외합니다. YouTube ID/주소 태그가 있으면 DB가 없어지거나 파일명·경로가 달라져도 재사용합니다. 이전 버전의 태그도 인식하며, 메타데이터 변경 시 음원을 재다운로드·재인코딩하지 않습니다. 태그 없는 파일이나 손상 파일은 파일명으로 추측하지 않습니다.

**이 폴더에서 음악 불러오기**로 기존 MP3를 검토하고 **태그 및 폴더 구조 적용**을 누르세요. YouTube 태그가 없는 파일도 편집할 수 있습니다. 제목·아티스트가 없으면 먼저 입력해야 합니다. 손상되거나 읽을 수 없는 파일은 로그에 기록하고 건너뜁니다. 불러온 뒤 외부에서 변경된 파일은 보호하며 다시 불러와야 합니다.

파일 이름 항목: `{artist}`, `{title}`, `{album}`, `{track}`, `{decade}`. `{title}`과 아티스트 폴더를 선택하면 `Artist/Song.mp3`, 10년 단위 폴더는 `2010s/Song.mp3`가 됩니다. 연도는 개별 연도 대신 `1990s`, `2000s`, `2010s`, `2020s`처럼 묶으며 날짜가 없으면 `Unknown decade`를 사용합니다. 폴더 구분 없음을 선택하면 대상 폴더에 바로 저장합니다. 잘못된 파일 이름 문자는 치환하고 충돌 시 식별자를 덧붙이거나 안전하게 중단합니다. 기존 음원은 재인코딩하지 않습니다.

음원 전송·변환은 최초 시도 후 최대 5회 재시도하며 대기 중에도 취소할 수 있습니다. 미리 다운로드에 실패한 곡은 목록에 표시하고 저장 시 다시 시도합니다. 이미 확인된 음원은 재사용합니다.

서버는 **127.0.0.1에서만** 실행하며 임의 포트, 요청 토큰 및 Host/Origin 검사를 사용합니다. 원격 제어·텔레메트리 서비스는 없습니다. 검색·다운로드·미리 듣기를 위해 YouTube/YouTube Music, MusicBrainz, 앨범 이미지 제공 서버에 요청을 보냅니다. 로그인 전용 플레이리스트는 지원하지 않습니다.

| 앱 데이터 | 경로 |
| --- | --- |
| Windows | `%LOCALAPPDATA%\YT-PL-Downloader` |
| macOS | `~/Library/Application Support/YT-PL-Downloader` |

현재 세션, 메타데이터 캐시, SQLite 목록, 순환 로그를 저장합니다. 음악은 지정한 폴더에 저장합니다. 버그 제보에 개인 데이터·쿠키를 첨부하지 마세요. MusicManager와는 독립적인 앱이며 백업/기록 UI는 없습니다.

## 🛠️ 개발 및 빌드

Python **3.14**, Git, FFmpeg 빌드용 네이티브 컴파일러가 필요합니다.

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS: source .venv/bin/activate
python -m pip install -r requirements/dev.txt
python scripts/prepare_tools.py
# 컴파일러 설정: docs/RELEASING.md 참고
bash scripts/build_ffmpeg.sh
python app.py
python -m pytest
python -m ruff check .
python scripts/build.py
```

[빌드·배포 안내](docs/RELEASING.md)에서 플랫폼별 빌드, 소스 묶음, 체크섬 및 서명 제한을 확인하세요. `--no-browser`, `--data-dir PATH`로 테스트 환경을 분리할 수 있습니다.

## 🤝 기여 및 LLM 활용

[CONTRIBUTING.md](CONTRIBUTING.md), [구조 설명](docs/ARCHITECTURE.md), [AGENTS.md](AGENTS.md)를 먼저 읽으세요. LLM에 이 파일들과 구체적인 작업을 전달하면 기존 동작을 유지하면서 개선하기 쉽습니다. [AI 작업 예시](docs/AI_DEVELOPMENT.md)도 제공합니다. 자동 테스트는 임시 폴더를 사용하며 실제 음악 다운로드를 기본으로 실행하지 않습니다.

## ⚖️ 라이선스

프로젝트 코드: **[GPL-3.0-or-later](LICENSE)**. Copyright © 2026 Mingyu Kim and contributors. 외부 구성 요소는 각각의 라이선스를 유지합니다. [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)를 참고하세요. 배포 시 대응 소스, 빌드 스크립트, 라이선스 안내를 바이너리와 함께 제공합니다. 이 라이선스가 음악·외부 메타데이터의 이용 권한을 부여하지는 않습니다.
