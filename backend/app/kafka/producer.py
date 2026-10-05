import asyncio, json, logging, os
from typing import Any

logger = logging.getLogger(__name__)

async def publish(topic: str, value: dict[str, Any]) -> None:
    """Best-effort Kafka publishing: HTTP MVP still completes when a broker is offline."""
    try:
        from aiokafka import AIOKafkaProducer
        producer = AIOKafkaProducer(bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"), value_serializer=lambda v: json.dumps(v, default=str).encode())
        await asyncio.wait_for(producer.start(), timeout=3)
        try: await producer.send_and_wait(topic, value)
        finally: await producer.stop()
    except Exception as exc:
        logger.warning("kafka_publish_failed topic=%s error=%s", topic, exc)
