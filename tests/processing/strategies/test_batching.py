import time
from datetime import datetime
from typing import Any, MutableSequence, Sequence
from unittest.mock import patch

from arroyo.backends.local.backend import LocalBroker as Broker
from arroyo.backends.local.backend import LocalConsumer
from arroyo.commit import IMMEDIATE
from arroyo.processing.processor import StreamProcessor
from arroyo.processing.strategies.batching import (
    AbstractBatchWorker,
    BatchProcessingStrategyFactory,
)
from arroyo.types import Message, Topic


class FakeWorker(AbstractBatchWorker[int, int]):
    def __init__(self) -> None:
        self.processed: MutableSequence[int] = []
        self.flushed: MutableSequence[Sequence[int]] = []

    def process_message(self, message: Message[int]) -> int:
        self.processed.append(message.payload)
        return message.payload

    def flush_batch(self, batch: Sequence[int]) -> None:
        self.flushed.append(batch)


class TestConsumer(object):
    def test_batch_size(self, broker: Broker[int]) -> None:
        topic = Topic("topic")
        broker.create_topic(topic, partitions=1)
        producer = broker.get_producer()
        for i in [1, 2, 3]:
            producer.produce(topic, i).result()

        consumer = broker.get_consumer("group")
        assert isinstance(consumer, LocalConsumer)

        worker = FakeWorker()
        batching_consumer = StreamProcessor(
            consumer,
            topic,
            BatchProcessingStrategyFactory(
                worker=worker,
                max_batch_size=2,
                max_batch_time=100,
            ),
            IMMEDIATE,
        )

        for _ in range(3):
            batching_consumer._run_once()

        batching_consumer._shutdown()

        assert worker.processed == [1, 2, 3]
        assert worker.flushed == [[1, 2]]
        assert consumer.commit_offsets_calls == 1
        assert consumer.close_calls == 1

    @patch("time.time")
    def test_batch_time(self, mock_time: Any, broker: Broker[int]) -> None:
        topic = Topic("topic")
        broker.create_topic(topic, partitions=1)
        producer = broker.get_producer()
        consumer = broker.get_consumer("group")
        assert isinstance(consumer, LocalConsumer)

        worker = FakeWorker()
        batching_consumer = StreamProcessor(
            consumer,
            topic,
            BatchProcessingStrategyFactory(
                worker=worker, max_batch_size=100, max_batch_time=2000
            ),
            IMMEDIATE,
        )

        mock_time.return_value = time.mktime(datetime(2018, 1, 1, 0, 0, 0).timetuple())

        for i in [1, 2, 3]:
            producer.produce(topic, i).result()

        for _ in range(3):
            batching_consumer._run_once()

        mock_time.return_value = time.mktime(datetime(2018, 1, 1, 0, 0, 1).timetuple())

        for i in [4, 5, 6]:
            producer.produce(topic, i).result()

        for _ in range(3):
            batching_consumer._run_once()

        mock_time.return_value = time.mktime(datetime(2018, 1, 1, 0, 0, 5).timetuple())

        for i in [7, 8, 9]:
            producer.produce(topic, i).result()

        for _ in range(3):
            batching_consumer._run_once()

        batching_consumer._shutdown()

        assert worker.processed == [1, 2, 3, 4, 5, 6, 7, 8, 9]
        assert worker.flushed == [[1, 2, 3, 4, 5, 6]]
        assert consumer.commit_offsets_calls == 1
        assert consumer.close_calls == 1
