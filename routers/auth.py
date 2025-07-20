# routers/auth.py
from fastapi import APIRouter, HTTPException
from authentication.token_generator import generate_token, verify_token, TokenErrors
from database.database import add_user
from models import UserG
from network.g_verification import verify_g
import secrets

router = APIRouter()

secret_hex = 'super-duper-secret'  # secrets.token_bytes(32)

@router.post('/verify-device-auth')
def verify_device_auth(user: UserG):
    if verify_g(user.username, user.password):
        token = generate_token(secret_hex, user.username, user.password)
        add_user(user.username)
        print(f'A token has been sent for {user.username}')
        return token
    raise HTTPException(401, detail='Unable to verify your user with a network device.')
