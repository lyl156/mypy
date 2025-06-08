# 支援：效能參數、手動 offset、重試、批次、DLQ、graceful shutdown

import signal
import time
import logging
from confluent_kafka import Producer, Consumer, KafkaException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KafkaClient")


class KafkaProducerWrapper:
    def __init__(self, brokers: str, topic: str, dlq_topic: str = None):
        self.topic = topic
        self.dlq_topic = dlq_topic
        self.running = True
        self.producer = Producer({
            'bootstrap.servers': brokers,
            'acks': 'all',
            'retries': 3,
            'compression.type': 'snappy',
            'linger.ms': 50,
            'batch.size': 64 * 1024,
            'queue.buffering.max.messages': 100000
        })

        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def _delivery_callback(self, err, msg):
        if err:
            logger.error(f"\u274c Failed to deliver message: {err}")
            if self.dlq_topic:
                logger.warning("Sending to DLQ")
                self.produce(self.dlq_topic, msg.key(), msg.value())
        else:
            logger.info(f"\u2705 Delivered to {msg.topic()} [{msg.partition()}]")

    def produce(self, topic: str, key: str, value: str, max_retries=3):
        for attempt in range(max_retries):
            try:
                self.producer.produce(
                    topic=topic,
                    key=key,
                    value=value,
                    callback=self._delivery_callback
                )
                self.producer.poll(0)
                return
            except BufferError as e:
                logger.warning(f"Buffer full: retry {attempt + 1}")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(1)

    def send(self, key: str, value: str):
        self.produce(self.topic, key, value)

    def flush(self):
        logger.info("\ud83d\udce4 Flushing messages...")
        self.producer.flush()

    def shutdown(self, *args):
        if self.running:
            logger.info("\ud83d\uded1 Graceful shutdown")
            self.running = False
            self.flush()


class KafkaConsumerWorker:
    def __init__(self, brokers: str, group_id: str, topic: str, dlq_topic: str = None, batch_size=10):
        self.topic = topic
        self.dlq_topic = dlq_topic
        self.batch_size = batch_size
        self.running = True

        self.consumer = Consumer({
            'bootstrap.servers': brokers,
            'group.id': group_id,
            'enable.auto.commit': False,
            'auto.offset.reset': 'earliest',
            'max.poll.interval.ms': 300000
        })

        self.consumer.subscribe([self.topic])
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, *args):
        logger.info("\ud83d\uded1 Consumer shutting down...")
        self.running = False

    def process_messages(self, messages):
        for msg in messages:
            try:
                logger.info(f"\ud83d\udcc5 {msg.key()} => {msg.value().decode()}")
                # TODO: Replace with your business logic
            except Exception as e:
                logger.error(f"Processing failed: {e}")
                if self.dlq_topic:
                    p = KafkaProducerWrapper(self.consumer.config['bootstrap.servers'], self.dlq_topic)
                    p.send(msg.key(), msg.value())
            finally:
                self.consumer.commit(message=msg)

    def run(self):
        batch = []
        while self.running:
            msg = self.consumer.poll(1.0)
            if msg is None or msg.error():
                continue
            batch.append(msg)
            if len(batch) >= self.batch_size:
                self.process_messages(batch)
                batch.clear()

        self.consumer.close()


# 使用範例：
# producer = KafkaProducerWrapper("localhost:9092", "main-topic", dlq_topic="dlq-topic")
# consumer = KafkaConsumerWorker("localhost:9092", "my-group", "main-topic", dlq_topic="dlq-topic")
# consumer.run()
