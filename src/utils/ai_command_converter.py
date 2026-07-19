"""
Claude AI로 자연어를 명령어로 변환 (브로커 무관).

docs/command_guide_for_ai.md를 시스템 프롬프트에 그대로 삽입해 변환 규칙의 단일 소스로 삼는다.
명령어를 추가/변경할 때는 반드시 docs/command_guide_for_ai.md도 함께 갱신해야 한다
(CLAUDE.md의 필수 규칙 참고).
"""

import json
from typing import List, Tuple

from anthropic import Anthropic

from config.config import claude_api_key, claude_model
from src.paths import COMMAND_GUIDE_FOR_AI as _GUIDE_PATH


def _load_command_guide() -> str:
    try:
        return _GUIDE_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _build_api_name_list() -> str:
    """
    docs/api/api-list.json 기반 'api {한글이름}' 자연어 인식용 전체 목록.

    command_guide_for_ai.md에 하드코딩하지 않고 여기서 매 호출 시 api-list.json을 읽어
    동적으로 만든다 — API 명세가 추가/변경돼도 이 목록이 따로 손보지 않아도 항상
    최신 상태를 유지한다 (manage/generate/generate_api_docs.py 재실행만으로 반영됨).
    """
    try:
        from src.utils.api_spec import search_api_entries

        entries = search_api_entries(None)
    except Exception:
        return ""
    return "\n".join(f"- {e['name']} ({e.get('category', '')})" for e in entries)


def _get_client(api_key: str = None):
    key = api_key or claude_api_key
    if not key or key.startswith("YOUR_"):
        return None
    return Anthropic(api_key=key)


def _build_system_prompt() -> str:
    guide = _load_command_guide()
    api_names = _build_api_name_list()
    return f"""당신은 KB증권 Open API Agent의 명령어 변환 AI 어시스턴트입니다.

사용자의 자연어 지시사항을 정확한 명령어로 변환하는 것이 당신의 역할입니다.

다음은 봇에서 지원하는 모든 명령어와 사용법입니다:

```
{guide}
```

`api` 명령으로 실행 가능한 전체 API 한글 이름 목록입니다 (이름 뒤 괄호는 업무구분).
아래 목록에 있는 이름(공백 무시, 완전히 똑같지 않아도 의미가 명확히 일치하면 인정)만
`api {{이름}}`으로 만드세요 — 목록에 없는 이름을 지어내지 마세요:

```
{api_names}
```

변환 규칙:
1. 사용자의 자연어 지시를 이해하고 해당하는 명령어를 찾아서 배열로 반환하세요.
2. 명령어는 `/` 없이 순수 텍스트 형식입니다. 예: `srch 005930`
3. 한 가지 지시사항에 여러 명령어가 필요하면 모두 배열에 포함하세요.
4. 종목코드/종목명 처리는 위 가이드의 "기본 규칙"을 그대로 따르세요 — buy/sell/srch/investor에서
   사용자가 종목명으로 말했다면 코드를 절대 추측하지 말고 종목명을 그대로 사용하세요
   (예: `buy 삼성전자 10`, `buy NH투자증권 10` — 유명하지 않은 종목이어도 이름을 그대로 쓰면
   됩니다, 실제 코드 확정은 이후 별도 단계에서 처리됩니다). 사용자가 이미 6자리 숫자로
   말했을 때만 그 코드를 그대로 사용하세요.
5. 명령어가 없으면 빈 배열 `[]`을 반환하세요.

응답 형식:
- JSON 배열 형식으로만 응답하세요. 다른 설명이나 텍스트는 없어야 합니다.
- 예: `["login real", "buy 삼성전자 10"]`
- 명령어를 찾을 수 없으면: `[]`

중요: JSON 배열만 반환하고, 추가 설명이나 주석은 절대 포함하지 마세요."""


def convert_natural_to_commands(text: str, api_key: str = None, model: str = None) -> Tuple[List[str], str]:
    """
    자연어를 명령어로 변환

    api_key/model을 생략하면 config.py의 전역값을 쓴다(터미널/텔레그램 봇의 기존 동작).
    src/web/client.py는 웹 세션(사용자)별로 설정 화면에서 입력받은 값을 넘겨,
    다중 사용자가 하나의 서버를 같이 써도 서로 다른 Claude 키를 쓸 수 있게 한다.

    Returns:
        (명령어_배열, 에러메시지) - 성공 시 (명령어들, ""), 실패 시 ([], 에러메시지)
    """
    client = _get_client(api_key)
    if client is None:
        return [], "❌ Claude API 키가 설정되지 않았습니다. (터미널/텔레그램은 config/config.py의 claude_api_key, 웹은 설정 화면을 확인하세요)"

    try:
        message = client.messages.create(
            model=model or claude_model,
            max_tokens=500,
            system=[{"type": "text", "text": _build_system_prompt(), "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": text}],
        )

        response_text = message.content[0].text.strip()
        if response_text.startswith("```"):
            lines = [l for l in response_text.split("\n") if not l.strip().startswith("```")]
            response_text = "\n".join(lines).strip()

        try:
            commands = json.loads(response_text)
        except json.JSONDecodeError:
            return [], f"명령어 변환 실패: AI 응답 파싱 오류\n응답: {response_text}"

        if not isinstance(commands, list) or not all(isinstance(c, str) for c in commands):
            return [], "명령어 변환 실패: 잘못된 응답 형식"

        return commands, ""

    except Exception as e:
        return [], f"명령어 변환 실패: {str(e)}"


def get_conversion_help() -> str:
    return """📝 자연어 명령어 사용법

한국어로 자연스럽게 지시하면 봇이 자동으로 명령어로 변환합니다.

예시:
• "삼성전자 10주 사줘" → buy 005930 10
• "전부 다 팔아줘" → sell all
• "미체결 주문 취소해줘" → ccl pend
• "익절 5퍼로 설정" → 익절 5
• "로그인해줘" → login real

명령어 형식으로도 입력 가능합니다:
• login real
• buy 005930 10
• sell all
"""
