"""
\file aeron_handler.py
\author github:khanbekov, telegram:qoddrysdaim
\brief В файле объявлен обработчик логов, отправляющий логи по Aeron
\data 2022.04.11
"""
from aeron import Publisher
from logging import StreamHandler


class AeronHandler(StreamHandler):
    def __init__(self, channel, stream_id):
        super().__init__()
        self.aeron_publisher = Publisher(channel, stream_id)

    def emit(self, record):
        msg = self.format(record)
        self.aeron_publisher.offer(msg)


