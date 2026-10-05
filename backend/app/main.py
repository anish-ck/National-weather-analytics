import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.kafka.consumer import consume_raw_events

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(consume_raw_events())
    yield
    task.cancel()

app = FastAPI(title="National Weather Intelligence API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
