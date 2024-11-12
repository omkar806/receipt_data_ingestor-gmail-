from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from src.routers import receipt_radar_router, total_messages_router , get_attachments, app_usage, card_data
import contextlib


@contextlib.contextmanager
def no_ssl_verification():
    import httpx
    Client = httpx.Client
    httpx.Client = lambda *args, **kwargs: Client(*args, verify=False, **kwargs)
    yield
    httpx.Client = Client
    
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["DELETE", "GET", "POST", "PUT"],
    allow_headers=["*"],
)

app.include_router(receipt_radar_router.router)
app.include_router(total_messages_router.router)
app.include_router(get_attachments.router)
app.include_router(app_usage.router)
app.include_router(card_data.router)

@app.get("/")
async def test():
    return {"Message":"Application is Working!"}
