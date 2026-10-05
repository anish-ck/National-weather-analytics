import asyncio, json, logging, os
from aiokafka import AIOKafkaConsumer
from app.schemas.events import VerificationRequest
from app.services.pipeline import verify_and_store

logger = logging.getLogger(__name__)

async def consume_raw_events():
    """Consumer group for source adapters; failures are isolated per message."""
    while True:
        consumer = AIOKafkaConsumer("weather.raw", bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"), group_id="weather-processors", enable_auto_commit=False, value_deserializer=lambda b: json.loads(b.decode()))
        try:
            await consumer.start()
            async for message in consumer:
                try:
                    await verify_and_store(VerificationRequest(**message.value))
                    await consumer.commit()
                except Exception as exc:
                    logger.exception("event_id=%s stage=consumer status=failed error=%s", message.value.get("event_id"), exc)
                    # Continue rather than allowing one bad report to stop the stream.
                    await consumer.commit()
        except asyncio.CancelledError: raise
        except Exception as exc:
            logger.warning("Kafka consumer reconnecting: %s", exc); await asyncio.sleep(3)
        finally:
            try: await consumer.stop()
            except Exception: pass
