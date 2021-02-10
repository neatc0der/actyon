class ActyonError(RuntimeError):
    pass


class ConsumerError(ActyonError):
    def __init__(self, consumer: "actyon.consumer.Consumer", msg: str, *args, **kwargs) -> None:
        super().__init__(msg, *args, **kwargs)
        self.consumer: "actyon.consumer.Consumer" = consumer


class ProducerError(ActyonError):
    def __init__(self, producer: "actyon.producer.Producer", msg: str, *args, **kwargs) -> None:
        super().__init__(msg, *args, **kwargs)
        self.producer: "actyon.producer.Producer" = producer
