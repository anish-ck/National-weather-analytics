import asyncio, json, logging, os
from aiokafka import AIOKafkaProducer
from sources.mock_source import MockSource

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

async def main():
    broker = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    producer = AIOKafkaProducer(bootstrap_servers=broker, value_serializer=lambda v: json.dumps(v).encode())
    while True:
        try:
            await producer.start(); break
        except Exception as exc:
            logging.warning("Kafka not ready: %s", exc); await asyncio.sleep(3)
    source = MockSource(); interval = int(os.getenv("MOCK_INTERVAL_SECONDS", "20"))
    try:
        while True:
            for report in source.collect():
                await producer.send_and_wait("weather.raw", report)
                logging.info("event_id=%s stage=collected status=published", report["event_id"])
            await asyncio.sleep(interval)
    finally: await producer.stop()

if __name__ == "__main__": asyncio.run(main())
