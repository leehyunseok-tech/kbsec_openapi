"""프로젝트 운영/관리 스크립트 모음 (런타임 코드가 아님 — src/의 실행 애플리케이션과 완전히 분리).

- manage/generate/ — 원본 데이터(종목마스터 .mst, API 명세 xlsx/md)를 읽어 문서·런타임
  데이터·자동 생성 코드를 재생성하는 스크립트. `uv run python -m manage.generate.<파일명>`.
- manage/run/ — 텔레그램/터미널/웹 클라이언트 실행 스크립트(run-*.bat/sh).
- manage/install/ — 신규 클론 환경 설치 스크립트(install-*.bat/sh).

상세 설명은 docs/개발환경/manage.md 참고.
"""
