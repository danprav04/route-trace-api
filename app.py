# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from authentication.token_generator import generate_token, verify_token, TokenErrors
import secrets

import routers
from routers.auth import secret_hex

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

TESTING_SECRET_KEY = secret_hex
SECRET_KEY = TESTING_SECRET_KEY
# SECRET_KEY = secrets.token_hex(16)

app.include_router(routers.auth_router)
app.include_router(routers.route_router)
app.include_router(routers.user_router)
app.include_router(routers.command_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="{sensitive-ip}", port=7000)
