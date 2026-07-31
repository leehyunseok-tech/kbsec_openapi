"""텔레그램 메시지 수신 (getUpdates 폴링). 브로커 무관."""

from config.config import telegram_token
from src.utils.http_client import http_client


def get_updates(offset=0):
    """
    텔레그램 최신 메시지 수신

    Args:
        offset: 처리된 메시지 이후부터 수신

    Returns:
        dict: API 응답
    """
    url = f"https://api.telegram.org/bot{telegram_token}/getUpdates"
    params = {"offset": offset, "timeout": 30}

    try:
        response = http_client.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        return {"ok": False, "result": []}
    except Exception as e:
        print(f"네트워크 오류: {str(e)}")
        return {"ok": False, "result": []}


def parse_message(message_data):
    """
    메시지 데이터 파싱

    Args:
        message_data: 메시지 객체

    Returns:
        dict: {'text': str, 'chat_id': int, 'update_id': int, 'sender': str} 또는 None
    """
    try:
        if "message" in message_data and "text" in message_data["message"]:
            message = message_data["message"]
            return {
                "text": message["text"],
                "chat_id": message["chat"]["id"],
                "update_id": message_data["update_id"],
                "sender": message.get("from", {}).get("first_name", "사용자"),
            }
    except (KeyError, TypeError):
        pass
    return None


def parse_callback_query(update):
    """
    인라인 버튼 탭(callback_query) 파싱 — 확인/선택 프롬프트에 버튼으로 응답했을 때 온다.

    Args:
        update: getUpdates 응답의 개별 update 객체

    Returns:
        dict: {'data': str, 'chat_id': int, 'callback_query_id': str, 'update_id': int, 'sender': str} 또는 None
    """
    try:
        if "callback_query" in update:
            cq = update["callback_query"]
            return {
                "data": cq.get("data", ""),
                "chat_id": cq["message"]["chat"]["id"],
                "callback_query_id": cq["id"],
                "update_id": update["update_id"],
                "sender": cq.get("from", {}).get("first_name", "사용자"),
            }
    except (KeyError, TypeError):
        pass
    return None
