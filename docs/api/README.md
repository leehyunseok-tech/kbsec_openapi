# docs/api 파이프라인

KB증권 OpenAPI 명세(xlsx) → 마크다운 → 목록/코드 생성까지의 흐름.

`xlsx/`, `md/` 모두 **업무구분(TR 성격)별 폴더 구조**로 정리되어 있다 (`OAuth/`,
`국내주식/{기본시세,시세분석,투자정보,계좌잔고,주식주문,주문내역}/`,
`해외주식/{기본시세,시세분석,계좌잔고,주식주문,주문내역}/`). `xlsx/`와 `md/`는
항상 동일한 폴더 구조 + 파일명(확장자만 다름)을 유지한다.

> ⚠️ **새 API 명세를 추가할 때는 반드시 TR 성격에 맞는 업무구분 폴더 안에 넣을 것**
> (예: 계좌 잔고 조회 API → `docs/api/xlsx/국내주식/계좌잔고/`, 신규 업무구분이면
> 새 폴더를 만들어도 됨 — `md/` 쪽에 자동으로 동일한 폴더가 생긴다). 이 폴더 구조가
> **웹 "API 명세" 페이지(`/api.html`)의 좌측 트리에 그대로 반영**된다 —
> `src/web/spec_browser.py`의 `build_tree()`가 `docs/api/md`의 실제 디렉터리 구조를
> 그대로 순회해 트리 JSON을 만들기 때문에(별도 분류 로직이나 `api-list.json`을
> 참조하지 않음), 엉뚱한 폴더에 넣으면 API 목록/코드 생성은 정상 동작하더라도 웹
> 화면에서 잘못된 업무구분 아래에 표시된다.

```
docs/api/xlsx/<업무구분>/.../*.xlsx   원본 API 명세서 (.xlsx, KB증권 제공)
        │  convert_xlsx_to_md.py (또는 generate_api_docs.py)
        ▼
docs/api/md/<업무구분>/.../*.md       API별 명세 마크다운 (.md, 기본정보/INPUT/OUTPUT 표 포함)
        │  generate_api_list.py         │  generate_api_client.py
        ▼                                ▼
docs/api/api-list.md, .json       src/api/*.py (카테고리별 함수), src/api/registry.py
(전체 API 목록, 업무구분 컬럼 포함)     (실제 호출 코드, 자동 생성)
```

**⚠️ 위 4개 생성 스크립트는 전부 `docs/api/`가 아니라 `manage/generate/`에 있다**(프로젝트
루트의 `manage/` 폴더 — `src/`도 아니다) — 명세(md)를 읽어 산출물만 재생성하는 순수 관리
스크립트라 `docs/`(문서/데이터 폴더)나 `src/`(런타임 애플리케이션 코드)가 아닌 운영/관리
스크립트 전용 폴더에 두는 것이 위치상 더 정확하기 때문. 전부
`uv run python -m manage.generate.<파일명(확장자 제외)>` 형태로 모듈 실행한다. 각 스크립트의
상세 역할·삭제 가능 여부·산출물·실행 시점은 `docs/개발환경/manage.md` 참고.

- `manage/generate/convert_xlsx_to_md.py` — `xlsx/` 원본(단일 파일/폴더/`--recursive`)을 동일한 상대 경로의 `md/`로 변환. 실행: `uv run python -m manage.generate.convert_xlsx_to_md`
- `manage/generate/generate_api_list.py` — `md/`를 재귀 스캔해 각 API의 기본정보(코드/명/설명/URL 등)와, 파일이 속한 하위 폴더 경로를 `" > "`로 이어붙인 **업무구분**(JSON은 `category` 키)을 `api-list.md`, `api-list.json`으로 정리. md가 추가/변경되면 재실행. 실행: `uv run python -m manage.generate.generate_api_list`
- `manage/generate/generate_api_client.py` — `md/`의 "## INPUT" 표까지 파싱해 `src/api/` 디렉토리에 카테고리별 모듈(함수 1개 = API 1개)과 `src/api/registry.py`를 생성. `src/api/client.py`, `src/api/auth.py`는 수기 작성이라 생성 대상이 아님. **API 코드를 `CODE_TO_MODULE` 딕셔너리에 직접 관리하므로, md의 API 코드가 추가/변경(개명)되면 이 딕셔너리도 함께 갱신한 뒤 재실행해야 한다** — 매핑에 없는 코드는 경고만 출력하고 건너뛴다. **재생성 후에는 반드시 `git diff src/api`로 실사용 함수의 시그니처 변화를 확인하고 호출부를 함께 맞출 것** — 이때 명세에서 빠진 필드라도 운영에서 검증된 요청 페이로드를 바꾸지 않으려면 `extra=` 파라미터로 유지한다. 내부적으로 `manage.generate.generate_api_list`의 `SPEC_DIR`/`collect_entries`/`dedupe`를 import해 재사용한다. 실행: `uv run python -m manage.generate.generate_api_client`
- `manage/generate/generate_api_docs.py` — 위 `convert_xlsx_to_md.py` + `generate_api_list.py`를 한 번에 실행하는 통합 스크립트. `xlsx/`에 새 명세 파일을 추가한 뒤 이것만 실행하면 된다.
  - `uv run python -m manage.generate.generate_api_docs` — `xlsx/` 전체 재변환 + 목록 재생성
  - `uv run python -m manage.generate.generate_api_docs "국내주식/계좌잔고"` — 특정 업무구분 폴더만 재변환(+ 목록은 항상 전체 재생성)
  - `uv run python -m manage.generate.generate_api_docs "국내주식/계좌잔고/SSQM0004-예수금내역-....xlsx"` — 특정 파일 하나만 재변환
  - 인자는 `docs/api/xlsx` 기준 상대경로 또는 절대경로 모두 허용. 새 업무구분 폴더를 추가해도 `md/` 쪽에 자동으로 동일한 폴더가 생성된다.

`docs/api/old/`에는 예전 flat 구조(업무구분 폴더 없이 `md/`, `xlsx/`에 전부 나열)의
이전 세대 산출물이 그대로 보관되어 있다 — 참고용 스냅샷일 뿐 더 이상 갱신되지 않는다.
