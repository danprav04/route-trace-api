from typing import Callable, Any
from functools import wraps

from authentication.token_generator import verify_token
from routers.auth import secret_hex


def token_required(f: Callable) -> Callable:
    @wraps(f)
    async def decorated_function(*args: Any, **kwargs: Any):
        request: Request = kwargs.get('request')
        if not request:
            raise HTTPException(401, detail='Request object not found.')

        token = request.headers.get('token')
        if not token:
            raise HTTPException(401, detail='Token not found in headers.')

        user = verify_token(secret_hex, token)
        if user == TokenErrors.Expired:
            raise HTTPException(401, detail='Expired token.')
        if user == TokenErrors.Invalid:
            raise HTTPException(401, detail='Invalid token.')

        kwargs['user'] = user
        return await f(*args, **kwargs)

    return decorated_function
