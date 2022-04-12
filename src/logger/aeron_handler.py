from aeron import Publisher
from logging import StreamHandler


class AeronHandler(StreamHandler):
    def __init__(self, channel, stream_id):
        super().__init__()
        self.aeron_publisher = Publisher(channel, stream_id)

    def emit(self, record):
        msg = self.format(record)
        self.aeron_publisher.offer(msg)


