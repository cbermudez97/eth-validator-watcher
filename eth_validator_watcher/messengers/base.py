class Messenger:
    def send_message(self, message: str) -> None:
        raise NotImplementedError


class MultiMessenger(Messenger):
    def __init__(self, *messengers: Messenger) -> None:
        self.messengers = list(messengers)

    def send_message(self, message: str) -> None:
        for messenger in self.messengers:
            messenger.send_message(message)
