import requests as r

from .base import Messenger


class Telegram(Messenger):
    def __init__(self, token: str, chat_id: str) -> None:
        self.__token = token
        self.__chat_id = chat_id

    def send_message(self, message: str) -> None:
        r.post(
            f"https://api.telegram.org/bot{self.__token}/sendMessage",
            data={"chat_id": self.__chat_id, "text": message},
        )
