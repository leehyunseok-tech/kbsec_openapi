"""텔레그램 메시지/파일/사진 전송. 브로커 무관."""

import json

import requests as _req

from src.utils.http_client import http_client
from config.config import telegram_chat_id, telegram_token

MAX_MESSAGE_LENGTH = 4096


def _split_message(text, max_len=MAX_MESSAGE_LENGTH):
    """텔레그램 글자 수 제한에 맞게 메시지를 분할."""
    if len(text) <= max_len:
        return [text]

    parts = []
    while text:
        if len(text) <= max_len:
            parts.append(text)
            break
        cut = text.rfind("\n", 0, max_len)
        if cut <= 0:
            cut = max_len
        parts.append(text[:cut])
        text = text[cut:].lstrip("\n")
    return parts


def _send_single(text):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    data = {"chat_id": telegram_chat_id, "text": text}

    try:
        response = http_client.post(url, headers=headers, json=data)
        response_body = response.json() if response.status_code == 200 else {}
        return {"status_code": response.status_code, "body": response_body, "success": response.status_code == 200}
    except Exception as e:
        print(f"네트워크 오류: {str(e)}")
        return {"status_code": None, "body": {}, "success": False}


def send_message(message):
    """
    텔레그램으로 메시지 전송 (4096자 초과 시 자동 분할).

    Returns:
        dict: {'status_code': int, 'body': dict, 'success': bool}
    """
    if message is None or (isinstance(message, str) and message.strip() == ""):
        return {"status_code": None, "body": {}, "success": False}

    text = str(message) if not isinstance(message, str) else message
    parts = _split_message(text)

    result = {"status_code": None, "body": {}, "success": False}
    for part in parts:
        result = _send_single(part)
        if not result["success"]:
            return result
    return result


def send_message_with_buttons(message, buttons):
    """
    인라인 키보드 버튼이 붙은 메시지 전송 (확인/선택 프롬프트용).

    Args:
        message: 메시지 본문
        buttons: list[list[tuple[str, str]]] — 바깥 리스트의 각 항목이 한 줄(row),
            튜플은 (버튼에 표시할 텍스트, 탭 시 돌아올 callback_data)

    Returns:
        dict: {'status_code': int, 'body': dict, 'success': bool}
    """
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    keyboard = {"inline_keyboard": [[{"text": label, "callback_data": data} for label, data in row] for row in buttons]}
    data = {"chat_id": telegram_chat_id, "text": message, "reply_markup": keyboard}

    try:
        response = http_client.post(url, headers=headers, json=data)
        response_body = response.json() if response.status_code == 200 else {}
        return {"status_code": response.status_code, "body": response_body, "success": response.status_code == 200}
    except Exception as e:
        print(f"네트워크 오류: {str(e)}")
        return {"status_code": None, "body": {}, "success": False}


def answer_callback_query(callback_query_id, text=None):
    """
    인라인 버튼 탭(callback_query) 응답 — 반드시 호출해야 버튼의 로딩 스피너가 멈춘다.

    Returns:
        bool: 성공 여부
    """
    url = f"https://api.telegram.org/bot{telegram_token}/answerCallbackQuery"
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    data = {"callback_query_id": callback_query_id}
    if text:
        data["text"] = text

    try:
        response = http_client.post(url, headers=headers, json=data)
        return response.status_code == 200
    except Exception as e:
        print(f"네트워크 오류: {str(e)}")
        return False


def send_photo(file_path: str, caption: str = "", token: str = None, chat_id: str = None) -> dict:
    """텔레그램으로 이미지 전송 (인라인 표시).

    token/chat_id를 생략하면 config.py의 전역값을 쓴다(main.py 텔레그램 봇의 기존 동작).
    src/web/client.py는 웹 세션별로 사용자가 입력한 값을 명시적으로 넘긴다.
    """
    token = token or telegram_token
    chat_id = chat_id or telegram_chat_id
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        with open(file_path, "rb") as f:
            data = {"chat_id": chat_id}
            if caption:
                data["caption"] = caption
            response = _req.post(url, data=data, files={"photo": f})
        body = response.json() if response.status_code == 200 else {}
        return {
            "status_code": response.status_code,
            "body": body,
            "success": response.status_code == 200 and body.get("ok", False),
        }
    except FileNotFoundError:
        return {"status_code": None, "body": {"error": "파일 없음"}, "success": False}
    except Exception as e:
        print(f"이미지 전송 오류: {e}")
        return {"status_code": None, "body": {"error": str(e)}, "success": False}


def send_document(file_path: str, caption: str = "", token: str = None, chat_id: str = None) -> dict:
    """텔레그램으로 파일(문서) 전송.

    token/chat_id를 생략하면 config.py의 전역값을 쓴다(main.py 텔레그램 봇의 기존 동작).
    src/web/client.py는 웹 세션별로 사용자가 입력한 값을 명시적으로 넘긴다.
    """
    token = token or telegram_token
    chat_id = chat_id or telegram_chat_id
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    try:
        with open(file_path, "rb") as f:
            data = {"chat_id": chat_id}
            if caption:
                data["caption"] = caption
            response = _req.post(url, data=data, files={"document": f})
        body = response.json() if response.status_code == 200 else {}
        return {
            "status_code": response.status_code,
            "body": body,
            "success": response.status_code == 200 and body.get("ok", False),
        }
    except FileNotFoundError:
        return {"status_code": None, "body": {"error": "파일 없음"}, "success": False}
    except Exception as e:
        print(f"파일 전송 오류: {e}")
        return {"status_code": None, "body": {"error": str(e)}, "success": False}


def print_send_result(response):
    print(f"\n{'=' * 60}")
    print("[텔레그램 메시지 전송]")
    print(f"{'=' * 60}")
    print(f"응답 코드: {response['status_code']}")
    print(f"전송 상태: {'[성공]' if response['success'] else '[실패]'}")
    print(f"응답 바디:\n{json.dumps(response['body'], indent=2, ensure_ascii=False)}")
