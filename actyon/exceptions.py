from . import helpers


class ActyonError(RuntimeError):
    pass


class ConsumerError(ActyonError):
    def __init__(self, consumer: "helpers.consumer.Consumer", msg: str) -> None:
        super().__init__(msg)
        self.consumer: "helpers.consumer.Consumer" = consumer


class ProducerError(ActyonError):
    def __init__(self, producer: "helpers.producer.Producer", msg: str) -> None:
        super().__init__(msg)
        self.producer: "helpers.producer.Producer" = producer
