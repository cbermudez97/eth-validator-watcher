from .base import Messenger
from slack_sdk import WebClient


class Slack(Messenger):
    def __init__(self, channel: str, token: str) -> None:
        self.__channel = channel
        self.__client = WebClient(token=token)

    def send_message(self, message: str) -> None:
        response = self.__client.chat_postMessage(channel=self.__channel, text=message)
        if not response["ok"]:
            print(f"❗ Failed to send message to Slack: {response}")
