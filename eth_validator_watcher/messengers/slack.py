import requests as r

from .base import Messenger


class Slack(Messenger):
    def __init__(self, channel: str, token: str) -> None:
        self.__channel = channel
        self.__token = token

    def send_message(self, message: str) -> None:
        response = r.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {self.__token}",
            },
            json={
                "channel": self.__channel,
                "text": message,
            },
        )
        if not response.ok:
            print(f"❗ Failed to send message to Slack: {response}")
