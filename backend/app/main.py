"""FlowSync FastAPI Application entrypoint."""

import asyncio
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.endpoints import router as api_router
from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, init_db
from backend.app.services.traffic_service import TrafficService
from backend.app.services.websocket_manager import ws_manager
from iot.mqtt.client import FlowSyncMQTTClient

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger("flowsync.api")

mqtt_client: FlowSyncMQTTClient | None = None
broadcast_task: asyncio.Task | None = None


async def live_traffic_broadcast_loop():
    """Background task to broadcast real-time traffic updates via WebSocket."""
    while True:
        try:
            if ws_manager.active_connections:
                db = SessionLocal()
                try:
                    intersections = TrafficService.get_all_intersections(db)
                    payload = {
                        "event_type": "traffic.live_update",
                        "timestamp": asyncio.get_event_loop().time(),
                        "intersections": [
                            {
                                "id": i.id,
                                "name": i.name,
                                "status": i.status,
                                "current_mode": i.current_mode or "initial",
                                "mode": i.current_mode or "initial",
                                "current_phase": i.current_phase or 0,
                                "phase": i.current_phase or 0,
                                "current_state": i.current_state or "GGggrrrrGGGg",
                                "state": i.current_state or "GGggrrrrGGGg",
                                "vehicle_count": i.vehicle_count or 0,
                                "vehicles": i.vehicle_count or 0,
                                "queue_length": i.queue_length or 0,
                                "queue": i.queue_length or 0,
                                "location_x": i.location_x or 0.0,
                                "location_y": i.location_y or 0.0,
                            }
                            for i in intersections
                        ],
                    }
                    await ws_manager.broadcast(payload)
                finally:
                    db.close()
        except Exception as exc:
            logger.debug("Broadcast loop tick exception: %s", exc)

        await asyncio.sleep(1.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global mqtt_client, broadcast_task

    logger.info("Initializing FlowSync Database...")
    init_db()

    # Optional MQTT client connection for backend listener
    logger.info("Starting background MQTT subscriber...")
    try:
        mqtt_client = FlowSyncMQTTClient(
            client_id="flowsync_fastapi_backend",
            broker_host=settings.MQTT_BROKER_HOST,
            broker_port=settings.MQTT_BROKER_PORT,
        )
        mqtt_connected = mqtt_client.connect(timeout=1.0)
        if not mqtt_connected:
            logger.warning("Mosquitto broker not detected on %s:%s. Running in standalone API mode.", settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT)
    except Exception as exc:
        logger.warning("MQTT setup skipped (%s). Backend running in degraded mode.", exc)

    # Start WebSocket live broadcaster
    broadcast_task = asyncio.create_task(live_traffic_broadcast_loop())

    yield

    # Shutdown
    if broadcast_task:
        broadcast_task.cancel()
    if mqtt_client:
        mqtt_client.disconnect()
    logger.info("FlowSync Backend shutdown complete.")


app = FastAPI(
    title="FlowSync Traffic Management API",
    description="IoT-based adaptive traffic signal and emergency vehicle priority system.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# WebSocket live updates
@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep socket alive and receive any client ping
            data = await websocket.receive_text()
            logger.debug("Received WebSocket message: %s", data)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as exc:
        logger.debug("WebSocket error: %s", exc)
        ws_manager.disconnect(websocket)


@app.get("/")
def root():
    return {
        "project": "FlowSync",
        "description": "Adaptive Traffic Signal and Emergency Priority System",
        "documentation": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
    }
