import requests as r

from .base import Messenger


class Telegram(Messenger):
    def __init__(self, chat_id: str, token: str) -> None:
        self.__token = token
        self.__chat_id = chat_id

    def send_message(self, message: str) -> None:
        response = r.post(
            f"https://api.telegram.org/bot{self.__token}/sendMessage",
            json={
                "chat_id": self.__chat_id,
                "text": message,
                "parse_mode": "Markdown",
            },
        )
        if not response.ok:
            print(f"❗ Failed to send message to Telegram: {response}")
