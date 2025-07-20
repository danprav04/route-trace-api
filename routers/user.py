# routers/user.py
from fastapi import APIRouter, HTTPException, Request
from authentication.token_generator import verify_token, TokenErrors
from routers.auth import secret_hex

router = APIRouter()

@router.post('/get-user-routes')
def get_user_routes(request: Request):
    token = request.headers['token']
    user = verify_token(secret_hex, token)
    if user == TokenErrors.Expired:
        raise HTTPException(401, detail='Expired token.')
    if user == TokenErrors.Invalid:
        raise HTTPException(401, detail='Invalid token.')

    # Add logic to get user routes
    return {'message': 'User routes'}
