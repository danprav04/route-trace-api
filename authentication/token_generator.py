from enum import Enum

import jwt
from datetime import datetime, timedelta


ALGORITHM = 'HS256'


def generate_token(secret_key, username, password):
    to_encode = {'username': username, 'password': password}
    return jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)


class TokenErrors(Enum):
    Expired = 0
    Invalid = 1


def verify_token(secret_key, token: str):
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return TokenErrors.Expired
    except jwt.InvalidTokenError:
        return TokenErrors.Invalid
