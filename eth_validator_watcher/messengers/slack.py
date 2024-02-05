import re
import requests as r

from .base import Messenger


class Slack(Messenger):
    def __init__(self, channel: str, token: str) -> None:
        self.__channel = channel
        self.__token = token

    def __update_mrkdwn_links(self, message: str) -> str:
        return re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            r"<\2|\1>",
            message,
        )

    def send_message(self, message: str) -> None:
        message = self.__update_mrkdwn_links(message)
        response = r.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {self.__token}",
            },
            json={
                "channel": self.__channel,
                "text": message,
                "unfurl_links": False,
            },
        )
        if not response.ok:
            print(f"❗ Failed to send message to Slack: {response}")
