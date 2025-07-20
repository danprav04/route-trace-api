from pydantic import BaseModel
from datetime import datetime


class UserG(BaseModel):
    username: str
    password: str

    def __hash__(self):
        return hash((self.username, self.password))


class RouteInit(BaseModel):
    source_ip: str
    destination_ip: str
    is_refresh: bool
    partial_route: bool
    start_vrf: str

class RouteDelete(BaseModel):
    source_ip: str
    destination_ip: str

class LogDelete(BaseModel):
    source_ip: str
    destination_ip: str
    log_id: int

class RouteResponse(BaseModel):
    route: list
    timestamp: datetime
