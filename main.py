import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from utils.init_db import init_db
from utils.ws_manager import kitchen_ws
from routers import (
    miniapp_auth,
    miniapp_categories,
    miniapp_dishes,
    miniapp_cart,
    miniapp_upload,
    miniapp_orders,
    miniapp_ai,
    admin_auth,
    admin_dishes,
    admin_categories,
    admin_users,
    admin_orders,
    admin_stats,
)

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Register routers
app.include_router(miniapp_auth.router)
app.include_router(miniapp_categories.router)
app.include_router(miniapp_dishes.router)
app.include_router(miniapp_cart.router)
app.include_router(miniapp_upload.router)
app.include_router(miniapp_orders.router)
app.include_router(miniapp_ai.router)
app.include_router(admin_auth.router)
app.include_router(admin_dishes.router)
app.include_router(admin_categories.router)
app.include_router(admin_users.router)
app.include_router(admin_orders.router)
app.include_router(admin_stats.router)


@app.websocket("/ws/kitchen")
async def kitchen_websocket(ws: WebSocket):
    await kitchen_ws.connect(ws)
    try:
        while True:
            # Keep connection alive, wait for client pings
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        kitchen_ws.disconnect(ws)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"message": "OrderingMini API", "version": "1.0.0"}
