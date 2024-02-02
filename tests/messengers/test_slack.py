from eth_validator_watcher.messengers import slack


class WebClient:
    def __init__(self, token: str):
        assert token == "my_slack_token"

    def chat_postMessage(self, channel: str, text: str):
        assert channel == "MY CHANNEL"
        assert text == "MY TEXT"


slack.WebClient = WebClient  # type: ignore


def test_slack() -> None:
    slack_notifier = slack.Slack("MY CHANNEL", "my_slack_token")
    slack_notifier.send_message("MY TEXT")
