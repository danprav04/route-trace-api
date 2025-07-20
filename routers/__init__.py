# routers/__init__.py
from .auth import router as auth_router
from .route import router as route_router
from .user import router as user_router
from .command_routes.layer_two import router as command_router
