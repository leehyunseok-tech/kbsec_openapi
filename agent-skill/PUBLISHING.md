# 이 스킬을 만든 방법 / 다시 배포하는 방법 (메인테이너용)

이 문서는 `agent-skill/` 자체를 쓰는 사람을 위한 문서가 아니라, **이 스킬을 만들고 유지보수하는
사람**(=지금 이 프로젝트를 관리하는 사용자)을 위한 절차서다. `kbsec-skill`을 GitHub에 별도
공개 저장소로 올리고 `npx skills add`로 설치 가능하게 만드는 전체 과정을 담는다.

## 1. Agent Skill이란

Claude Code, Codex 등 여러 코딩 에이전트가 공유하는 확장 포맷이다
([Agent Skills Specification](https://agentskills.io)). 핵심은 단 하나:

- `SKILL.md` 파일에 YAML frontmatter로 `name`/`description`을 적는다.
- 에이전트가 이 파일을 읽고, 필요하면 같은 저장소의 다른 파일(`references/`, `scripts/` 등)도
  참고해 작업을 수행한다.

배포/설치는 스킬 스펙과 무관한 별도 생태계 도구인
[vercel-labs/skills](https://github.com/vercel-labs/skills) (`npx skills`)가 담당한다. 이
CLI가 GitHub 저장소를 읽어 `SKILL.md`를 찾고, Claude Code(`.claude/skills/`), Codex
(`.codex/skills/` 또는 `.agents/skills/`) 등 감지된 에이전트의 스킬 디렉터리에 심볼릭
링크/복사한다.

## 2. 참고한 예시: BEOKS/tossinvest-skill

`https://github.com/BEOKS/tossinvest-skill` 구조를 그대로 따랐다:

```
SKILL.md                     — 에이전트 진입점
agents/openai.yaml           — Codex 계열 UI 메타데이터
references/workflows.md      — 엔드포인트 맵, 인증 흐름, 안전 규칙
references/*.json            — 공식 API 스키마 번들
scripts/<name>.py            — 표준 라이브러리 기반 CLI
README.md                    — 저장소 랜딩 페이지 (npx 설치 안내 포함)
```

토스증권 스킬은 공식 OpenAPI JSON을 그대로 복사해 번들했지만, KB증권은 단일 OpenAPI
문서를 공개하지 않는다. 대신 이 프로젝트(`kbsec_api`)가 이미 `docs/api/md/*.md` 74개 파일을
런타임에 파싱하는 `src/utils/api_spec.py`를 갖고 있어서, 그 파서를 한 번 돌려
`references/endpoints.json`(코드/카테고리/엔드포인트/필드명/필수여부/선택지)으로 내보내는
방식으로 대체했다. 아래 "5. endpoints.json 갱신 방법"에 재생성 절차가 있다.

## 3. 로컬에서 먼저 검증

GitHub에 올리기 전에 로컬에서 그대로 동작하는지 확인한다.

```bash
# CLI 자체 스모크 테스트 (자격증명 없이도 되는 것들)
python3 agent-skill/scripts/kbsec.py list-endpoints
python3 agent-skill/scripts/kbsec.py spec SSAM1802
python3 agent-skill/scripts/kbsec.py buy --symbol 005930 --qty 1 --price 70000   # dry-run

# 실제 자격증명으로 (config/config.py의 값을 절대 커밋/출력하지 말 것 — 아래 4번 참고)
export KBSEC_CLIENT_KEY="..."
export KBSEC_CLIENT_SECRET="..."
python3 agent-skill/scripts/kbsec.py balance
```

`npx skills`로 로컬 경로를 바로 설치해 실제 설치 흐름도 검증할 수 있다 (별도 저장소로
나누기 전, `kbsec_api` 루트에서):

```bash
npx skills add ./agent-skill --agent claude-code
npx skills list
```

## 4. GitHub에 별도 공개 저장소로 올리기

`kbsec-skill` 저장소는 **공개(public)** 여야 `npx skills add`로 누구나 설치할 수 있다. 올리기
전에 반드시 확인:

- [ ] `agent-skill/` 안에 `config/config.py`, 실제 앱키/시크릿, 텔레그램 토큰 등 민감정보가
      전혀 없다 (이 스킬은 설계상 환경변수만 읽고, 저장소에는 예시/플레이스홀더도 넣지 않았다).
- [ ] `scripts/kbsec.py`가 자격증명을 로그/출력하지 않는다 (`token` 명령은 기본적으로
      마스킹된 토큰만 출력한다).
- [ ] `git status`로 의도치 않은 파일이 섞여 들어가지 않는지 확인한다.

별도 저장소로 분리해서 올리는 절차 (이 프로젝트의 커밋 히스토리를 가져가지 않고, 현재
`agent-skill/` 내용만 새 저장소의 루트로 복사):

```bash
# 1) kbsec_api 바깥에 새 폴더를 만들고 agent-skill 내용만 복사
mkdir ../kbsec-skill
cp -r agent-skill/. ../kbsec-skill/
cd ../kbsec-skill

# 2) 새 git 저장소로 초기화하고 첫 커밋
git init
git add .
git commit -m "Initial commit: KB Securities Open API agent skill"

# 3) GitHub에 저장소 생성 (gh CLI가 있는 경우 — 없으면 4번의 웹 UI 방식 사용)
gh repo create leehyunseok-tech/kbsec-skill --public --source=. --remote=origin
git push -u origin main
```

`gh` CLI가 없거나 로그인이 안 되어 있으면 웹에서 만든다:

1. https://github.com/new 접속 → Repository name에 `kbsec-skill` 입력 → **Public** 선택 →
   README/`.gitignore`/license 자동 생성 옵션은 모두 체크 해제(이미 파일이 있으므로) → Create.
2. 로컬에서 원격 저장소 연결 후 푸시:
   ```bash
   git remote add origin https://github.com/leehyunseok-tech/kbsec-skill.git
   git branch -M main
   git push -u origin main
   ```

> 이 저장소를 공개로 올리는 행위, 그리고 실제 `git push`는 되돌리기 번거로운 공개 행위이므로
> 사용자가 직접 실행/승인하는 것을 권장한다.

## 5. endpoints.json 갱신 방법

`kbsec_api` 프로젝트에서 `docs/api/md`가 바뀌면(새 API 추가, 필드 변경 등)
`agent-skill/references/endpoints.json`도 다시 만들어야 한다. `kbsec_api` 저장소 루트에서
아래 스크립트를 임시로 만들어 실행하면 된다 (실행 후 삭제):

```python
# kbsec_api 루트에 build_endpoints.py로 저장 후 실행, 끝나면 삭제
import json
from pathlib import Path
from urllib.parse import urlsplit
from src.utils.api_spec import _load_api_list, load_api_spec

OUT_PATH = Path("agent-skill/references/endpoints.json")
entries = _load_api_list()
out = []
for e in entries:
    if not e.get("code"):
        out.append({"code": None, "name": e.get("name"), "category": e.get("category"),
                     "endpoint": urlsplit(e.get("prod_url", "")).path, "method": "POST",
                     "fields": [], "output_labels": {}})
for code in sorted(e["code"] for e in entries if e.get("code")):
    spec = load_api_spec(code)
    if spec is None:
        continue
    out.append({
        "code": spec.code, "name": spec.name, "category": spec.category,
        "endpoint": spec.endpoint, "method": "POST",
        "fields": [{"name_en": f.name_en, "name_kr": f.name_kr, "length": f.length,
                     "required": f.required, "description": f.description, "choices": f.choices}
                    for f in spec.fields],
        "output_labels": spec.output_labels,
    })
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {len(out)} entries")
```

```bash
uv run python build_endpoints.py && rm build_endpoints.py
```

새 주문 계열 API가 추가됐다면 `scripts/kbsec.py`의 `MUTATING_CODES` 집합에도 그 코드를
추가해야 dry-run 게이트가 걸린다 — 잊으면 새 주문 API가 안전장치 없이 즉시 실행된다.

그 다음 `kbsec-skill` 저장소 쪽으로 파일을 다시 복사하고 커밋/푸시한다:

```bash
cp agent-skill/references/endpoints.json ../kbsec-skill/references/endpoints.json
cp agent-skill/scripts/kbsec.py ../kbsec-skill/scripts/kbsec.py
cd ../kbsec-skill
git add -A
git commit -m "Update bundled endpoint spec"
git push
```

이미 설치되어 있는 사용자는 `npx skills update kbsec-skill`로 갱신할 수 있다.

## 6. 설치 확인 (npx)

저장소를 올린 뒤 실제로 설치되는지 확인한다.

```bash
# 어떤 스킬이 있는지만 확인 (설치 없이)
npx skills add leehyunseok-tech/kbsec-skill --list

# 전체 에이전트 대상 설치
npx skills add leehyunseok-tech/kbsec-skill

# Claude Code만 지정
npx skills add leehyunseok-tech/kbsec-skill --agent claude-code

# 설치 없이 프롬프트만 생성해 바로 사용
npx skills use leehyunseok-tech/kbsec-skill --skill kbsec-skill --agent claude-code
```

설치되면 (Claude Code 기준) `.claude/skills/kbsec-skill/`에 심볼릭 링크 또는 복사본이
생기고, `python3 <설치경로>/scripts/kbsec.py ...`로 바로 실행할 수 있다. 에이전트가 자연어
요청을 받으면 `SKILL.md`의 description을 보고 이 스킬을 자동으로 활성화한다.

## 7. 이후 이 방식으로 다른 브로커 스킬도 만들 수 있다

같은 뼈대(`SKILL.md` + `references/workflows.md` + `references/*.json` + `scripts/*.py`)를
그대로 재사용하면 된다. 브로커마다 달라지는 부분은:

- 인증 방식과 요청/응답 envelope (KB는 `dataHeader`/`dataBody`, Toss는 표준 OAuth2 + 공용
  `result` envelope)
- 필드 스펙을 어디서 가져올지 (공식 OpenAPI JSON이 있으면 그대로 복사, 없으면 이번처럼
  기존 프로젝트의 파서를 재사용해 직접 내보낸다)
- 주문류 API 목록(`MUTATING_CODES`에 해당하는 것) — dry-run 게이트는 반드시 유지한다
