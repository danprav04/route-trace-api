# routers/route.py
from copy import deepcopy
from enum import Enum

from fastapi import APIRouter, HTTPException, Request, Query

from Tufin.Tufin import SecureTrackAPI
from authentication.token_generator import verify_token, TokenErrors
from database.models import RouteTypes
from models import RouteInit, RouteDelete
from database import database as db
from routers.auth import secret_hex
from tracer.routetrace import FromDatabase
from tracer.routetrace.tracer import Tracer
import json

import asyncio
from typing import List

router = APIRouter()

# Get Default Gateway
@router.get('/get-default-gateway/')
async def get_default_gateway(request: Request,
                              ip: str = Query(...)):
    """
    Get the default gateway of an IP address.

    Args:
    - ip (str): The IP address.

    Returns:
    - The default gateway of the IP address.
    """
    token = request.headers['token']

    user = verify_token(secret_hex, token)
    if user == TokenErrors.Expired:
        raise HTTPException(401, detail='Expired token.')
    if user == TokenErrors.Invalid:
        raise HTTPException(401, detail='Invalid token.')

    datalake = FromDatabase.create_connection_instance()
    default_gateway = await asyncio.to_thread(FromDatabase.get_default_gateway, datalake, ip)
    return default_gateway[0]

# Get MAC Trace
@router.get('/get-mac-trace/')
async def get_mac_trace(request: Request,
                        ip: str = Query(...),
                        dg: str = Query(None)):
    """
    Get the MAC trace from an IP address to its default gateway.

    Args:
    - ip (str): The IP address.
    - dg (str): The default gateway.

    Returns:
    - The MAC trace from the IP address to its default gateway.
    """
    token = request.headers['token']

    user = verify_token(secret_hex, token)
    if user == TokenErrors.Expired:
        raise HTTPException(401, detail='Expired token.')
    if user == TokenErrors.Invalid:
        raise HTTPException(401, detail='Invalid token.')

    datalake = FromDatabase.create_connection_instance()
    tufin = SecureTrackAPI()

    if not dg:
        dg = await asyncio.to_thread(FromDatabase.get_default_gateway, datalake, ip)
        if dg:
            dg = dg[0]

    tracer = Tracer(print, user["username"], user["password"], datalake, tufin)

    mac_trace, vrf = await asyncio.to_thread(tracer.find_lan_route_to_endpoint, ip, dg)

    trace = [hop.to_dict(index) for index, hop in enumerate(mac_trace)]

    for hop in trace:
        hop['hostname'] = hop['id_']

    db.add_route(dg, ip, trace, RouteTypes.Layer2, user["username"])

    return trace


# Get Route Trace
@router.get('/get-route-trace/')
async def get_route_trace(request: Request,
                          source_ip: str = Query(...),
                          destination_ip: str = Query(...),
                          source_dg: str = Query(...),
                          destination_dg: str = Query(...)):
    """
    Get the route trace from a source IP to a destination IP.

    Args:
    - source_ip (str): The source IP address.
    - destination_ip (str): The destination IP address.
    - source_dg_name (str): The name of the source data group.
    - source_dg_id (str): The ID of the source data group.
    - destination_dg_name (str): The name of the destination data group.
    - destination_dg_id (str): The ID of the destination data group.

    Returns:
    - The route trace from the source IP to the destination IP.
    """
    token = request.headers['token']

    user = verify_token(secret_hex, token)
    if user == TokenErrors.Expired:
        raise HTTPException(401, detail='Expired token.')
    if user == TokenErrors.Invalid:
        raise HTTPException(401, detail='Invalid token.')

    datalake = FromDatabase.create_connection_instance()
    tufin = SecureTrackAPI()
    tracer = Tracer(print, user["username"], user["password"], datalake, tufin)

    device_id, vrf, mac, interface_or_vlan = await asyncio.to_thread(
        FromDatabase.default_gateway_step,
        datalake,
        source_dg,
        source_ip
    )

    source_name = await asyncio.to_thread(FromDatabase.get_device_name_by_ip, datalake, source_dg)

    route_trace = await asyncio.to_thread(tracer.find_wan_route_dg_to_dg,
                                          source_ip,
                                          source_dg,
                                          destination_ip,
                                          vrf,
                                          destination_dg,
                                          source_name
                                          )

    route = [hop.to_dict(index) for index, hop in enumerate(route_trace)]

    db.add_route(source_ip, destination_ip, route, RouteTypes.Layer3, user["username"])

    return route


@router.get('/get-all-routes')
def get_all_routes(request: Request):
    token = request.headers['token']
    user = verify_token(secret_hex, token)
    if user == TokenErrors.Expired:
        raise HTTPException(401, detail='Expired token.')
    if user == TokenErrors.Invalid:
        raise HTTPException(401, detail='Invalid token.')

    routes = db.get_all_routes_with_user()
    return routes


@router.get('/get-user-routes')
def get_user_routes(request: Request):
    token = request.headers['token']
    user = verify_token(secret_hex, token)
    if user == TokenErrors.Expired:
        raise HTTPException(401, detail='Expired token.')
    if user == TokenErrors.Invalid:
        raise HTTPException(401, detail='Invalid token.')

    routes = db.get_user_routes_with_user(user["username"])
    return routes


@router.get('/get-search-routes')
def get_user_routes(request: Request,
                    search_string: str = None,
                    route_type: str = None,
                    limit: str = 10,
                    page: str = 1):

    token = request.headers['token']
    user = verify_token(secret_hex, token)
    if user == TokenErrors.Expired:
        raise HTTPException(401, detail='Expired token.')
    if user == TokenErrors.Invalid:
        raise HTTPException(401, detail='Invalid token.')

    routes = db.get_search_routes(search_string, route_type, user["username"], int(limit), int(page))
    return routes


@router.post('/delete-route')
def delete_route(route_delete: RouteDelete, request: Request):
    token = request.headers['token']
    source_ip = route_delete.source_ip
    destination_ip = route_delete.destination_ip

    user = verify_token(secret_hex, token)
    if user == TokenErrors.Expired:
        raise HTTPException(401, detail='Expired token.')
    if user == TokenErrors.Invalid:
        raise HTTPException(401, detail='Invalid token.')

    db.delete_route(source_ip, destination_ip)
    return {'message': 'Route deleted successfully'}


@router.get('/get-route-by-id/{route_id}')
def get_route_by_id(route_id: str, request: Request):
    if not route_id.isnumeric():
        raise HTTPException(422, detail='Id should be numeric.')
    route_id = int(route_id)
    token = request.headers['token']
    user = verify_token(secret_hex, token)
    if user == TokenErrors.Expired:
        raise HTTPException(401, detail='Expired token.')
    if user == TokenErrors.Invalid:
        raise HTTPException(401, detail='Invalid token.')

    route = db.get_route_by_id(route_id)
    if route is None:
        raise HTTPException(404, detail='Route not found.')
    return route
