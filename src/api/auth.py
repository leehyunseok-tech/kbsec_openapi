"""KB증권 OAuth2 접근토큰 발급 (/oauth2/token). 수기 작성 — 코드 생성 대상 아님."""

import json

from config import config
from src.utils.api_logger import log_api_error, log_api_request, log_api_response
from src.api.client import _post

TOKEN_ENDPOINT = "/oauth2/token"


def get_token(host_url, client_key, client_secret):
    """
    KB증권 OAuth2 접근토큰 발급.

    Args:
        host_url: 'https://developer.kbsec.com:32484' (운영) 또는
                  'https://ddeveloper.kbsec.com:32484' (개발)
        client_key: KB증권 홈페이지에서 발급받은 appKey (KB API 요청 시 clientId 필드로 전송됨)
        client_secret: KB증권 홈페이지에서 발급받은 appSecret

    Returns:
        dict: {
            'status_code': int|None,
            'body': dict,               # KB 응답 전체(dataHeader+dataBody)
            'access_token': str|None,
            'expires_in': int|None,
            'success': bool,
        }
    """
    url = host_url + TOKEN_ENDPOINT
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    payload = {
        "dataHeader": dict(config.device_info),
        "dataBody": {
            "grantType": "client_credentials",
            "clientId": client_key,
            "clientSecret": client_secret,
        },
    }

    log_api_request(api_name="토큰 발급", api_id=None, url=url, headers=headers, data=payload)

    try:
        response = _post(url, payload, headers)
        response_body = response.json() if response.content else {}

        log_api_response(
            status_code=response.status_code,
            response_headers=dict(response.headers),
            response_body=response_body,
        )

        data_body = response_body.get("dataBody", {})
        result_code = response_body.get("dataHeader", {}).get("resultCode")
        success = response.status_code == 200 and result_code == "200"
        access_token = data_body.get("access_token") if success else None
        expires_in = data_body.get("expires_in") if success else None

        return {
            "status_code": response.status_code,
            "body": response_body,
            "access_token": access_token,
            "expires_in": expires_in,
            "success": success,
        }
    except json.JSONDecodeError as e:
        log_api_error("JSON 파싱 오류", str(e))
        return {"status_code": None, "body": {"error": str(e)}, "access_token": None, "expires_in": None, "success": False}
    except Exception as e:
        log_api_error("네트워크 오류", str(e))
        return {"status_code": None, "body": {"error": str(e)}, "access_token": None, "expires_in": None, "success": False}
