"""
KB증권 REST API 공용 호출 로직.

KB의 요청/응답 봉투는 dataHeader/dataBody로 나뉜 중첩 구조다:
  요청: {"dataBody": {...업무 파라미터...}, "dataHeader": {"ipAddr": ..., "macAddr": ...}}
  응답: {"dataHeader": {"resultCode", "resultMessage", "processCode", ...}, "dataBody": {...}}

인증(토큰 발급)은 dataHeader가 디바이스 정보 블록이라 이 모듈의 공용 헬퍼를 쓰지 않고
api/auth.py에서 별도로 처리한다.
"""

import json

from src.utils.api_logger import log_api_error, log_api_request, log_api_response
from src.utils.device_info import get_local_ip, get_mac_address
from src.utils.http_client import http_client


def _post(url, payload, headers):
    return http_client.post(url, headers=headers, json=payload)


def build_business_headers(token):
    return {
        "Content-Type": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}",
    }


def call_business_api(api_name, api_code, endpoint, data_body, required, token, host_url,
                       ip_addr=None, mac_addr=None):
    """
    KB증권 업무 API(토큰 발급 제외) 공용 호출.

    Args:
        api_name: API 한글명 (로그용)
        api_code: API 코드 (예: 'SSAM1801')
        endpoint: URL 경로 (예: '/api/v1/ssam1801')
        data_body: dataBody에 들어갈 dict
        required: data_body 중 값이 비어 있으면 안 되는 필드명 리스트
        token: Authorization 헤더에 쓸 접근토큰
        host_url: 프로토콜+호스트 (예: 'https://developer.kbsec.com:32484')
        ip_addr / mac_addr: dataHeader에 넣을 값. 생략 시 자동 탐지.

    Returns:
        dict: {'status_code': int|None, 'body': dict, 'success': bool}
        body는 KB 응답 전체(JSON, dataHeader+dataBody 포함)이거나 오류 시 {'error': str}.
    """
    missing = [f for f in required if not data_body.get(f)]
    if missing:
        message = f"필수 파라미터 누락: {', '.join(missing)}"
        log_api_error("파라미터 검증 오류", message)
        return {"status_code": None, "body": {"error": message}, "success": False}

    url = host_url + endpoint
    headers = build_business_headers(token)
    payload = {
        "dataBody": data_body,
        "dataHeader": {
            "ipAddr": ip_addr or get_local_ip(),
            "macAddr": mac_addr or get_mac_address(),
        },
    }

    log_api_request(api_name=api_name, api_id=api_code, url=url, headers=headers, data=payload)

    try:
        response = _post(url, payload, headers)
        response_body = response.json() if response.content else {}

        log_api_response(
            status_code=response.status_code,
            response_headers=dict(response.headers),
            response_body=response_body,
        )

        result_code = response_body.get("dataHeader", {}).get("resultCode")
        success = response.status_code == 200 and result_code == "200"

        return {"status_code": response.status_code, "body": response_body, "success": success}
    except json.JSONDecodeError as e:
        log_api_error("JSON 파싱 오류", str(e))
        return {"status_code": None, "body": {"error": str(e)}, "success": False}
    except Exception as e:
        log_api_error("네트워크 오류", str(e))
        return {"status_code": None, "body": {"error": str(e)}, "success": False}
