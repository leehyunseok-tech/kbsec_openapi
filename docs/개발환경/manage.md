# `manage/` — 운영(생성/갱신/실행/설치) 스크립트

`manage/`(프로젝트 루트, **`src/`가 아님**)는 애플리케이션 런타임 코드가 전혀 아닌
운영/관리 스크립트를 모아둔 폴더다. `config/`·`docs/`·`mst/`와 같은 층위의 독립 폴더이며,
텔레그램/터미널/웹 클라이언트가 동작하는 동안에는 이 폴더의 아무것도 import하지 않는다.
세 하위 폴더로 나뉜다.

```
manage/
├── generate/    데이터·코드 생성 스크립트 (이 문서에서 상세히 다룸, 아래 참고)
├── run/         클라이언트 실행 스크립트 (run-main/run-terminal/run-web, .bat + .sh)
└── install/     신규 클론 환경 설치 스크립트 (install-project, .bat + .sh)
```

- **`manage/run/`**, **`manage/install/`**: 프로젝트 루트에 있던 `run-*.bat`/`.sh`,
  `install-project.bat`/`.sh`가 이 두 폴더로 이동한 것 — 파일 자체가 이동했을 뿐 사용법은
  README의 "실행 스크립트"/"원클릭 설치" 절에 그대로 있다(예: `manage\run\run-terminal.bat`,
  `./manage/install/install-project.sh`). 두 폴더 모두 `.bat`/`.sh`뿐이라 Python 패키지가
  아니며, 프로젝트 루트에서 두 단계 아래로 옮겨졌기 때문에 스크립트 내부의 `cd`가
  `%~dp0..\..`(bat)/`$(dirname "${BASH_SOURCE[0]}")/../..`(sh)로 프로젝트 루트까지
  되짚어가도록 되어 있다.
- **`manage/generate/`**: 아래부터 이 문서가 상세히 다루는 대상. 데이터/원본이 갱신됐을 때
  **사람이 손으로 한 번 실행**해 산출물(문서·런타임 데이터·자동 생성 코드)을 최신 상태로
  맞추는 스크립트 5개. `docs/` 아래에는 더 이상 `.py` 파일이 하나도 없다 — 예전에는 API
  명세 파이프라인 스크립트 일부가 `docs/api/`에 있었지만, 전부 이 폴더로 옮겨졌다(관리
  스크립트는 `docs/`가 아니라 `manage/generate/`에 모으는 것으로 정리됨).

모든 `manage/generate/` 스크립트는 `uv run python -m manage.generate.<파일명(확장자 제외)>`
형태로 **모듈 실행**한다(프로젝트 루트를 `sys.path`에 올려야 절대 임포트가 풀리므로 `python
manage/generate/xxx.py`처럼 파일 경로로 직접 실행하지 말 것 — `src/run/*.py`와 동일한 이유,
`CLAUDE.md` "소스 레이아웃" 참고).

```
manage/generate/
├── generate_mst.py          종목마스터 파이프라인
├── convert_xlsx_to_md.py    API 명세 xlsx → md 변환
├── generate_api_list.py     API 목록(api-list.md/json) 생성
├── generate_api_client.py   API 호출 코드(src/api/*.py + registry.py) 생성
└── generate_api_docs.py     convert_xlsx_to_md + generate_api_list 통합 실행
```

**결론부터: 5개 전부 현재 사용 중이며 삭제하면 안 된다.** 각 스크립트의 이유는
아래 섹션별 "삭제 가능 여부"에 정리했다.

---

## 1. `generate_mst.py` — 종목마스터 파이프라인

### 무엇을 만드는가

`mst/origin/`의 KB 배포 원본 `.mst`(코스피 `mtsjname.mst` / 코스닥 `mtsoutjname.mst` /
미국 `FORENMST_US.MST`)와 공식 필드 명세(`docs/mst/xlsx/mst_*.xlsx`)를 읽어, 중간 파일
없이 아래를 한 번에 재생성한다.

- `docs/mst/xlsx/openapi_mst_*.xlsx` — 공식 명세에서 실제 사용/참조하는 필드만 선별한 표
- `docs/mst/md/openapi_mst_*.md` — 위 선별표의 마크다운 판 + 코드→라벨 변환 규칙
- `mst/api/openapi_field_kospi-kosdaq.mst`, `mst/api/openapi_field_foren-us.mst` —
  `src/utils/stock_master.py`가 실제로 로드하는 **런타임 데이터**(종목검색 `/stcd`,
  `buy`/`sell`/`srch`의 종목명→코드 결정적 해석 근거)

필드 선별 기준은 스크립트 안 `CURATION` 표가 단일 소스이고, 라벨/코드표의 근거는 KB
공식 명세(`docs/mst/xlsx/mst_*.xlsx`)다. `CURATION`이 가리키는 필드 순번이 공식 명세에
없으면 즉시 실패하고, 용도 설명에 적힌 API 코드가 `docs/api/api-list.md`에 없어도
즉시 실패한다 — 둘 다 KB가 마스터 레이아웃이나 API 목록을 바꿨을 때를 놓치지 않기
위한 검증이다.

### 실행

```bash
uv run python -m manage.generate.generate_mst
```

### 언제 실행해야 하는가

- **KB가 종목마스터 원본 `.mst` 3종을 새로 배포했을 때** — 새 파일을 `mst/origin/`에
  덮어쓴 뒤 실행. (상장/상폐, 종목구분·관리종목·거래정지 상태 변경 등은 원본 파일이
  갱신되지 않으면 반영되지 않는다 — 이 스크립트는 원본을 재해석할 뿐 KB 서버에서
  최신 데이터를 내려받지는 않는다.)
- **`docs/mst/xlsx/mst_*.xlsx`(공식 필드 명세)가 바뀌었을 때** — KB가 마스터 파일
  레이아웃(필드 순번/의미)을 변경한 경우. 이 경우 스크립트 안 `CURATION` 표의 필드
  순번도 함께 재검토해야 할 수 있다.
- **`docs/api/api-list.md`가 갱신된 뒤, `CURATION` 표의 용도 설명에 새 API 코드를
  추가했을 때** — 코드 존재 검증이 걸려 있으므로 순서상 API 목록(`generate_api_list.py`)
  갱신이 먼저다.
- 산출물(`docs/mst/xlsx/openapi_mst_*.xlsx`, `docs/mst/md/openapi_mst_*.md`,
  `mst/api/openapi_field_*.mst`)을 **손으로 직접 고치지 않는다** — 재실행 시 덮어써진다.

### 실행 결과 검증

스크립트 자체가 삼성전자(005930, 종목구분=주식)와 AAPL(종목타입=주식)이 결과에
포함되는지 자체 점검(sanity check)을 수행하고, 공식 코드표에 없는 값이 몇 건인지
출력한다. 0건이 아니면 코드표 확장을 검토해야 한다는 신호다.

### 삭제 가능 여부

❌ 불가. `src/utils/stock_master.py`가 읽는 종목검색 런타임 데이터의 유일한 생성
경로다 — 삭제하면 KB가 종목마스터를 갱신해도 반영할 방법이 없어진다.

---

## 2. `convert_xlsx_to_md.py` — API 명세 xlsx → md 변환

### 무엇을 만드는가

`docs/api/xlsx/*.xlsx`(KB API 명세 원본, 업무구분별 폴더 구조)를 동일한 상대 경로의
`docs/api/md/*.md`로 변환한다. 단일 파일/폴더/`--recursive`(하위 폴더 포함) 세 가지
방식을 지원한다.

### 실행

```bash
uv run python -m manage.generate.convert_xlsx_to_md "docs/api/xlsx/파일.xlsx"          # 단일 파일
uv run python -m manage.generate.convert_xlsx_to_md "docs/api/xlsx/국내주식/계좌잔고/"  # 폴더
uv run python -m manage.generate.convert_xlsx_to_md "docs/api/xlsx/" --recursive        # 전체
```

보통은 아래 통합 스크립트(`generate_api_docs.py`)를 통해 간접 실행된다.

### 언제 실행해야 하는가

- **KB가 새 API 명세 xlsx를 배포했을 때** — `docs/api/xlsx/`의 해당 업무구분 폴더에
  파일을 넣은 뒤 실행(아래 "TR 성격별 폴더 분류" 절 참고 — 어느 폴더에 넣는지가
  웹 화면 표시에 직결된다).
- **기존 xlsx 명세가 수정됐을 때** — 같은 파일을 다시 변환하면 md가 덮어써진다.

### 삭제 가능 여부

❌ 불가. `generate_api_docs.py`가 `convert_single_file` 함수를 import해서 재사용하므로
(아래 5번 참고) 삭제하면 통합 스크립트가 깨진다. KB가 새 명세 xlsx를 배포할 때마다
필요하다.

---

## 3. `generate_api_list.py` — API 목록 생성

### 무엇을 만드는가

`docs/api/md/` 아래 전체 API 명세(.md, 업무구분별 폴더 구조)를 재귀 스캔해 두 산출물을
동시에 생성한다.

- `docs/api/api-list.md` — 사람이 읽는 표 형태 전체 API 목록
- `docs/api/api-list.json` — 프로그램이 읽는 배열 형태 (아래 "런타임 사용처" 참고)

md 파일이 속한 하위 폴더 경로를 `" > "`로 이어붙여 **업무구분**(JSON은 `category` 키)
컬럼으로 기록하고, 동일 API 코드가 여러 파일로 중복 존재하면(재수집 등) 파일명
타임스탬프가 가장 최신인 파일만 대표로 남긴다.

### 실행

```bash
uv run python -m manage.generate.generate_api_list
```

보통은 아래 통합 스크립트를 통해 간접 실행된다.

```bash
uv run python -m manage.generate.generate_api_docs   # xlsx→md 변환 + 이 스크립트를 한 번에 실행
```

### 언제 실행해야 하는가

- **`docs/api/md/*.md`가 추가/변경됐을 때** — 신규 API 명세를 받았거나(보통
  `generate_api_docs.py`로 xlsx→md 변환과 함께 처리), 기존 명세의 기본정보(설명/URL 등)가
  수정됐을 때.
- **`generate_api_client.py`(코드 생성)를 실행하기 전** — `generate_api_client.py`는
  이 스크립트의 `SPEC_DIR`/`collect_entries`/`dedupe`를 import해서 재사용하므로, 명세가
  바뀐 뒤 두 스크립트를 실행하는 순서를 지켜야 한다(먼저 목록 스캔 로직이 최신 명세를
  올바르게 인식하는지 `docs/api/api-list.md`로 눈으로 확인한 다음 클라이언트 코드를
  생성하는 편이 안전).
- **`generate_mst.py`를 실행하기 전** — `generate_mst.py`가 `CURATION` 표의
  API 코드를 `docs/api/api-list.md`로 검증하므로, API 목록이 최신이어야 새로 추가한
  API 코드가 검증을 통과한다.
- 산출물(`docs/api/api-list.md`, `api-list.json`)을 **손으로 직접 고치지 않는다** —
  재실행 시 덮어써진다.

### 삭제 가능 여부

❌ 불가. `generate_api_client.py`가 `SPEC_DIR`/`collect_entries`/`dedupe`를 import해서
재사용하고, `generate_api_docs.py`가 `main()`을 호출한다 — 다른 두 스크립트의 의존
대상이다. 산출물(`api-list.json`)의 런타임 사용처는 아래 절 참고.

---

## 4. `generate_api_client.py` — API 호출 코드 생성

### 무엇을 만드는가

`docs/api/md/*.md`의 "## INPUT" 표를 파싱해 `src/api/` 아래 카테고리별 모듈(함수 1개 =
API 1개)과 `src/api/registry.py`(`REGISTRY` — 코드→함수 매핑)를 자동 생성한다.
`src/api/client.py`/`auth.py`는 수기 작성이라 생성 대상이 아니다.

**API 코드를 `CODE_TO_MODULE` 딕셔너리에 직접 관리하므로, md의 API 코드가 추가/변경
(개명)되면 이 딕셔너리도 함께 갱신한 뒤 재실행해야 한다** — 매핑에 없는 코드는 경고만
출력하고 건너뛴다. **재생성 후에는 반드시 `git diff src/api`로 실사용 함수의 시그니처
변화를 확인하고 호출부를 함께 맞출 것** — 이때 명세에서 빠진 필드라도 운영에서 검증된
요청 페이로드를 바꾸지 않으려면 `extra=` 파라미터로 유지한다.

### 실행

```bash
uv run python -m manage.generate.generate_api_client
```

### 언제 실행해야 하는가

- **`docs/api/md`에 API 명세가 추가/변경됐을 때** — `generate_api_list.py`(또는
  `generate_api_docs.py`)로 목록을 먼저 갱신한 뒤 실행하는 것이 안전하다(3번 참고).
- **새 API를 추가할 때** — 먼저 이 스크립트의 `CODE_TO_MODULE` 딕셔너리에 코드→모듈
  배정을 추가해야 한다(누락 시 경고 출력 후 건너뜀).
- 산출물(`src/api/*.py` 카테고리 모듈, `src/api/registry.py`)을 **손으로 직접 고치지
  않는다** — 재실행 시 덮어써진다.

### 산출물의 런타임 사용처

`src/api/registry.py`의 `REGISTRY`는 `terminal.py`의 `call {코드}` 명령(구버전 저수준
호출 경로)이 조회에 사용한다. 실제 명령 핸들러(`buy_command.py` 등)는 생성된
`src/api/*.py` 함수를 직접 import해서 쓴다.

### 삭제 가능 여부

❌ 불가 — `src/api/` 대부분이 이 스크립트의 산출물이다.

---

## 5. `generate_api_docs.py` — 통합 실행 스크립트

### 무엇을 만드는가

`convert_xlsx_to_md.py` + `generate_api_list.py`를 한 번에 실행하는 통합 스크립트다.
`docs/api/xlsx/`에 새 명세 파일을 추가한 뒤 이것 하나만 실행하면 xlsx→md 변환과
`api-list.*` 재생성이 한 번에 끝난다(매번 두 스크립트를 따로 실행할 필요 없음).

### 실행

```bash
uv run python -m manage.generate.generate_api_docs                                    # xlsx/ 전체 재변환 + 목록 재생성
uv run python -m manage.generate.generate_api_docs "국내주식/계좌잔고"                  # 특정 업무구분 폴더만 재변환(+ 목록은 항상 전체 재생성)
uv run python -m manage.generate.generate_api_docs "국내주식/계좌잔고/SSQM0004-....xlsx" # 특정 파일 하나만 재변환
```

인자는 `docs/api/xlsx` 기준 상대경로 또는 절대경로 모두 허용한다. 새 업무구분 폴더를
추가해도 `md/` 쪽에 자동으로 동일한 폴더가 생성된다.

### 언제 실행해야 하는가

- **KB에서 새 명세를 받았거나 기존 명세가 바뀌었을 때** — 사실상 이 스크립트가
  API 명세 갱신의 표준 진입점이다. `docs/api/xlsx/`에 파일을 넣고 이것만 실행한 뒤,
  코드 시그니처가 바뀔 수 있는 경우에만 이어서 `generate_api_client.py`를 실행한다.

### 삭제 가능 여부

❌ 불가 — 없어도 `convert_xlsx_to_md.py`+`generate_api_list.py`를 개별 실행하면 동일한
결과를 얻을 수는 있지만, `docs/api/README.md`에 권장 워크플로로 문서화되어 있고
실제로 이 스크립트만 실행하는 것이 표준 절차다.

---

## `docs/api/api-list.json` 런타임 사용처 조사

`docs/api/api-list.json`은 `generate_api_list.py`의 **산출물**이지만, 그와 별개로
애플리케이션 런타임(`src/`)에서도 실제로 읽는다 — 삭제하면 아래 기능이 전부 깨진다.

| 사용 위치 | 용도 |
|---|---|
| `src/utils/api_spec.py` (`_load_api_list`, `find_api_entry`, `search_api_entries`) | `api-list.json`을 mtime 기반으로 캐싱해 읽는 **단일 진입점**. 아래 모든 사용처가 결국 이 함수들을 거친다 |
| `src/commands/api_command.py` | `/api {코드}`, `/api list [키워드]` 등 API 직접호출 명령이 `search_api_entries`로 코드/이름/업무구분 검색 |
| `src/run/terminal.py` (`/list` 명령) | 저수준 직접 호출(`call`/`info`/`list`)의 `list`가 동일하게 `search_api_entries` 사용 |
| `src/utils/api_resolver.py` | AI가 변환한 `api {한글이름}` 토큰을 실제 API 코드로 로컬에서 결정적으로 매칭(이름이 여러 API와 겹치면 번호 선택 세션으로 연결) |
| `src/utils/ai_command_converter.py` (`_build_api_name_list`) | Claude 시스템 프롬프트에 삽입할 "API 직접호출 가능한 전체 API 이름 목록"을 매 호출마다 `api-list.json`에서 동적으로 구성(`docs/command_guide_for_ai.md`에 하드코딩하지 않음) |
| `src/run/command_pipeline.py` | 위 흐름(자연어 → `api {이름}` → 코드 해석)을 있는 그대로 설명하는 주석 |

**명시적으로 쓰지 않는 곳**: `src/web/spec_browser.py`(웹 "API 명세" 탐색 화면)는
`api-list.json`이 아니라 `docs/api/md`의 **폴더 구조 그대로**를 트리로 보여준다고
파일 상단 docstring에 명시되어 있다 — 의도적으로 분리된 설계다. 자세한 내용은 바로
아래 절 참고.

`api-list.json`은 "API 직접호출"(`/api`, `/call`, `/list`, 자연어 `api {이름}` 인식) 기능
전체가 의존하는 핵심 런타임 데이터다. `docs/api/md`가 갱신될 때마다 `generate_api_docs.py`
(또는 `generate_api_list.py`)를 재실행해 최신 상태로 유지해야 한다 — `api_spec.py`가
mtime을 확인해 자동으로 다시 읽으므로 재생성 후 프로세스 재시작은 필요 없다.

---

## ⚠️ `docs/api/xlsx/`에 명세를 넣을 때: TR 성격별 폴더 분류 → 웹 API 명세 트리에 그대로 반영됨

새 API 명세 xlsx를 추가할 때는 **반드시 TR 성격(업무구분)에 맞는 폴더 안에** 넣어야
한다. 현재 폴더 구조는 다음과 같다.

```
docs/api/xlsx/
├── OAuth/
├── 국내주식/{기본시세,시세분석,투자정보,계좌잔고,주식주문,주문내역}/
└── 해외주식/{기본시세,시세분석,계좌잔고,주식주문,주문내역}/
```

(신규 업무구분이 필요하면 새 폴더를 만들어도 된다 — `convert_xlsx_to_md.py`/
`generate_api_docs.py`가 `docs/api/md/` 쪽에 동일한 폴더를 자동으로 만든다.)

**이 폴더 구조가 그대로 웹 "API 명세" 화면(`/api.html`)의 좌측 트리 분류로 표시된다.**
`src/web/spec_browser.py`의 `build_tree()`가 `docs/api/api-list.json`이 아니라
`docs/api/md`의 **실제 디렉터리 구조를 그대로 재귀 순회**해 트리 JSON을 만들기
때문이다(별도의 분류 로직이 없다). 즉:

- 예수금내역(SSQM0004)처럼 계좌잔고 성격의 API를 `국내주식/계좌잔고/`가 아니라
  `국내주식/기본시세/`처럼 엉뚱한 폴더에 넣으면, `generate_api_list.py`가 만드는
  API 목록(`api-list.md`/`.json`)의 업무구분 컬럼도 잘못 기록되고, 웹 화면에서도
  "기본시세" 카테고리 아래에 예수금내역이 나타난다 — API 코드 생성(`generate_api_client.py`)
  자체는 정상 동작하므로 이 실수는 눈으로 웹 화면을 보기 전까지 드러나지 않는다.
- `xlsx/`와 `md/`는 항상 동일한 폴더 구조 + 파일명(확장자만 다름)을 유지해야 한다 —
  `convert_xlsx_to_md.py`가 `docs/api/xlsx/<업무구분>/.../*.xlsx` →
  `docs/api/md/<업무구분>/.../*.md`로 상대 경로를 그대로 보존해서 변환하기 때문에,
  두 폴더 구조가 어긋나면(예: xlsx만 옮기고 md는 그대로 둠) 웹 화면과 실제 데이터가
  불일치하게 된다.

---

## 스크립트 실행 순서 (여러 개를 함께 돌려야 할 때)

KB가 종목마스터 원본과 API 명세를 동시에 갱신한 경우(드물지만 가능), 의존 방향 때문에
아래 순서를 지킨다.

```bash
uv run python -m manage.generate.generate_api_docs     # 1) API 명세 xlsx→md + api-list.* 갱신
uv run python -m manage.generate.generate_mst           # 2) mst 파이프라인 (CURATION의 API 코드를 api-list.md로 검증)
uv run python -m manage.generate.generate_api_client    # 3) src/api/*.py 코드 재생성 (필요시)
```

`generate_mst.py`가 1번 산출물(`api-list.md`)에 의존하므로 순서를 바꾸면 존재하지 않는
API 코드로 검증이 실패할 수 있다.
