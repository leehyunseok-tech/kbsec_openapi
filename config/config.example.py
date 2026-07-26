# ============================================================
#  설정 템플릿
#  이 파일을 복사해 같은 디렉토리에 config.py 로 저장한 뒤
#  본인의 키 값을 입력하세요. (config.py 는 .gitignore 로 제외됨)
# ============================================================

# 운영환경 / 개발환경 호스트 URL (변경 불필요)
real_host_url = "https://developer.kbsec.com:32484"
dev_host_url = "https://ddeveloper.kbsec.com:32484"

# KB증권 홈페이지에서 발급받은 앱키 / 앱시크릿 (KB API 요청 시 clientId/clientSecret 필드로 전송됨)
real_client_key = "YOUR_REAL_CLIENT_KEY"
real_client_secret = "YOUR_REAL_CLIENT_SECRET"
dev_client_key = "YOUR_DEV_CLIENT_KEY"
dev_client_secret = "YOUR_DEV_CLIENT_SECRET"

# 토큰 발급(/oauth2/token) 요청의 dataHeader에 필요한 디바이스 정보.
# 서버/스크립트 환경이므로 고정값을 사용한다.
device_info = {
    "udId": "",
    "subChannel": "",
    "deviceModel": "Server",
    "deviceOs": "Server",
    "carrier": "",
    "connectionType": "",
    "appName": "kbsec_api",
    "appVersion": "0.1.0",
    "scrNo": "0000",
}


# 텔레그램 봇 토큰/채팅방 ID (https://t.me/BotFather 에서 발급)
telegram_chat_id = "YOUR_TELEGRAM_CHAT_ID"
telegram_token = "YOUR_TELEGRAM_BOT_TOKEN"

# 자연어 명령어 변환용 Claude API 키 (https://platform.anthropic.com 에서 발급, 선택)
claude_api_key = "YOUR_CLAUDE_API_KEY"
# 자연어 명령어 변환에 사용할 Claude 모델
# 가능한 모델: "claude-opus-4-8" (최고 성능), "claude-sonnet-4-6" (균형), "claude-haiku-4-5-20251001" (빠름)
# 모델의 상세 스팩은 https://platform.claude.com/dashboard 에서 확인 가능
claude_model = "claude-haiku-4-5-20251001"

# (선택) 웹 클라이언트 접속 관문 — HTTP Basic Auth. 웹 화면(정적 파일+/api/*) 전체에
# 아이디/비밀번호를 요구한다. 두 값 다 빈 문자열("")이면 비활성 — 지금처럼 관문
# 없이 그대로 동작한다. 둘 다 값을 채우면 그 즉시 켜진다(하나만 채우면 비활성
# 유지). KB 계좌 로그인(설정 화면의 앱키)과는 별개다. 환경변수
# KBSEC_WEB_BASIC_AUTH_USER/KBSEC_WEB_BASIC_AUTH_PASS가 설정되어 있으면 그쪽이
# 우선이고, 여기 값은 그 환경변수가 없을 때만 쓰인다. 외부(클라우드 등)에 노출할
# 때는 반드시 채울 것(영문/숫자 권장 — 한글 등은 도구에 따라 인코딩이 달라질 수 있음).
web_basic_auth_user = ""
web_basic_auth_pass = ""