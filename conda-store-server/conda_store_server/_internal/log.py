import logging


class RedactingFormatter(logging.Formatter):
    """A logging formatter which redacts items on the blocklist."""

    def __init__(self, *args, blocklist):
        if blocklist is None:
            blocklist = []

        self.blocklist = blocklist
        super().__init__(*args)

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        for item in self.blocklist:
            message = message.replace(item, "*" * len(item))
        return message
