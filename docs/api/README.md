# docs/api 파이프라인

KB증권 OpenAPI 명세(xlsx) → 마크다운 → 목록/코드 생성까지의 흐름.

`xlsx/`, `md/` 모두 **업무구분별 폴더 구조**로 정리되어 있다 (`OAuth/`,
`국내주식/{기본시세,시세분석,투자정보,계좌잔고,주식주문,주문내역}/`,
`해외주식/{기본시세,시세분석,계좌잔고,주식주문,주문내역}/`). `xlsx/`와 `md/`는
항상 동일한 폴더 구조 + 파일명(확장자만 다름)을 유지한다.

```
docs/api/xlsx/<업무구분>/.../*.xlsx   원본 API 명세서 (.xlsx, KB증권 제공)
        │  convert_xlsx_to_md.py (또는 generate_api_docs.py)
        ▼
docs/api/md/<업무구분>/.../*.md       API별 명세 마크다운 (.md, 기본정보/INPUT/OUTPUT 표 포함)
        │  generate_api_list.py          │  generate_api_client.py
        ▼                                ▼
docs/api/api-list.md, .json     src/api/*.py (카테고리별 함수), src/api/registry.py
(전체 API 목록, 업무구분 컬럼 포함)  (실제 호출 코드, 자동 생성)
```

- `convert_xlsx_to_md.py` — `xlsx/` 원본(단일 파일/폴더/`--recursive`)을 동일한 상대 경로의 `md/`로 변환.
- `generate_api_list.py` — `md/`를 재귀 스캔해 각 API의 기본정보(코드/명/설명/URL 등)와, 파일이 속한 하위 폴더 경로를 `" > "`로 이어붙인 **업무구분**(JSON은 `category` 키)을 `api-list.md`, `api-list.json`으로 정리. md가 추가/변경되면 재실행.
- `generate_api_client.py` — `md/`의 "## INPUT" 표까지 파싱해 `src/api/` 디렉토리에 카테고리별 모듈(함수 1개 = API 1개)과 `src/api/registry.py`를 생성. `src/api/client.py`, `src/api/auth.py`는 수기 작성이라 생성 대상이 아님. **API 코드를 `CODE_TO_MODULE` 딕셔너리에 직접 관리하므로, md의 API 코드가 추가/변경(개명)되면 이 딕셔너리도 함께 갱신한 뒤 재실행해야 한다** — 매핑에 없는 코드는 경고만 출력하고 건너뛴다. (2026-07-18에 신형 md 기준으로 매핑 갱신 및 재생성 완료: `SPQO2226`→`SPQM2226` 개명 반영, `GSS10180`/`IVS10920`/`IVU10020` 신규 추가, `SKQO3390` 제거. **재생성 후에는 반드시 `git diff src/api`로 실사용 함수의 시그니처 변화를 확인하고 호출부를 함께 맞출 것** — 이때 명세에서 빠진 필드라도 운영에서 검증된 요청 페이로드를 바꾸지 않으려면 `extra=` 파라미터로 유지한다.)
- `generate_api_docs.py` — 위 `convert_xlsx_to_md.py` + `generate_api_list.py`를 한 번에 실행하는 통합 스크립트. `xlsx/`에 새 명세 파일을 추가한 뒤 이것만 실행하면 된다.
  - `uv run python docs/api/generate_api_docs.py` — `xlsx/` 전체 재변환 + 목록 재생성
  - `uv run python docs/api/generate_api_docs.py "국내주식/계좌잔고"` — 특정 업무구분 폴더만 재변환(+ 목록은 항상 전체 재생성)
  - `uv run python docs/api/generate_api_docs.py "국내주식/계좌잔고/SSQM0004-예수금내역-....xlsx"` — 특정 파일 하나만 재변환
  - 인자는 `docs/api/xlsx` 기준 상대경로 또는 절대경로 모두 허용. 새 업무구분 폴더를 추가해도 `md/` 쪽에 자동으로 동일한 폴더가 생성된다.

`docs/api/old/`에는 예전 flat 구조(업무구분 폴더 없이 `md/`, `xlsx/`에 전부 나열)의
이전 세대 산출물이 그대로 보관되어 있다 — 참고용 스냅샷일 뿐 더 이상 갱신되지 않는다.
