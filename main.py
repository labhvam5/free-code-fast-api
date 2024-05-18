import logging
import json
from fastapi import FastAPI, Request
from typing import Union
from fastapi.middleware.cors import CORSMiddleware
from redis_om import get_redis_connection, HashModel
import consumers
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

redis = get_redis_connection(
    host="redis-17094.c305.ap-south-1-1.ec2.redns.redis-cloud.com",
    port=17094,
    password="LvWMMxPiqjfDpcA5NXOAyIX74rw4U8LM",
    decode_responses=True
)


class Delivery(HashModel):
    budget: int = 0
    notes: str = ''

    class Meta:
        database = redis


class Event(HashModel):
    delivery_id: str = None
    type: str
    data: str

    class Meta:
        database = redis


@app.get('/deliveries/{pk}/status')
async def get_delivery_status(pk: str):
    logger.info(f"HEr si the key {pk}")
    state = redis.get(f"delviery:{pk}")
    if state:
        return json.loads(state)
    else:
        return {"status": "not found"}


@app.post("/deliveries/create")
async def create_delivery(request: Request):
    body = await request.json()  # Get the request body as JSON
    data = body.get('data', {})

    delivery = Delivery(
        budget=data.get('budget', 0),
        notes=data.get('notes', '')
    ).save()

    event = Event(
        delivery_id=delivery.pk,
        type=body['type'],
        data=json.dumps(data)
    ).save()

    state = consumers.create_delivery({}, event)

    redis.set(f"delviery:{delivery.pk}", json.dumps(state))

    return state


@app.get("/")
def read_root():
    return {"Hello": "World"}
