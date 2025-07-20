# routers/auth.py
from fastapi import APIRouter, HTTPException
from AI_parser.parser import parse_data
import tracer.routetrace.FromDevices as FromDevices
from network.commands.layer_two import get_vlans
from network.paramiko_connection_CiscoDevices import SessionSSH

router = APIRouter()

@router.get('/vlans/{ip}')
def get_vlans_of_default_gateway(ip: str):
    device = SessionSSH(hostname=ip, username='', password='', immediately_connect=True)
    return parse_data(device.execute_command('show vlan'), 'number, name and status of the vlans')
