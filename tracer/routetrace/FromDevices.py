from tracer.routetrace import command_result_parser
from tracer.routetrace.CiscoDeviceConnection import Session as SessionSSH
from tracer.routetrace.CheckPointFireWallConnection import CheckpointFirewall
from tracer.routetrace.command_result_parser import Suspicion8200, SDABorderSuspicion

dev_user = '{sensitive}'
dev_pass = '{sensitive}'

fw_username = '{sensitive}'
fw_password = '{sensitive}'

fw_username_1 = '{sensitive}'
fw_password_1 = '{sensitive}'


class WrongDeviceTypeSuspicion(Exception):
    def __init__(self, message="Previous exception could have been raised because of operations performed on a wrong device type."):
        self.message = message
        super().__init__(self.message)


def create_device(ip, connect=True):
    return SessionSSH(hostname=ip, username=dev_user, password=dev_pass, immediately_connect=connect)


def default_gateway_step(default_gateway, source_ip):
    vlan = command_result_parser.get_vlan_from_ip_int_brief(
        default_gateway.execute_command(f'sh ip int br | i {".".join(source_ip.split(".")[:3])}'))
    vrf = command_result_parser.get_vrf_from_run_int_vlan(
        default_gateway.execute_command(f'sh run int {vlan}'))
    mac, interface = command_result_parser.get_mac_interface_from_arp(
        default_gateway.execute_command(f'show arp vrf {vrf} | i {source_ip}'))

    return vrf, mac, vlan


def get_next_hop_ip_cdp(device, next_hop_interface):
    next_hop_ip, next_hop_hostname = command_result_parser.get_next_hop_from_cdp(
        device.execute_command(f'sh cdp n {next_hop_interface} d'))

    return next_hop_ip, next_hop_hostname


def get_next_hop_int_mac_address_table(device, mac):
    next_hop_interface = command_result_parser.get_next_hop_int_from_mac_table(
        device.execute_command(f'sh mac address-table address {mac}'))

    return next_hop_interface


def is_destination(device, next_hop_interface):
    switchport_mode = command_result_parser.get_switchport_mode(
        device.execute_command(f'sh run int {next_hop_interface}'))

    if switchport_mode == 'access':
        return True
    return False


def last_int_in_port_channel(device, interface):
    if interface.lower().startswith('po'):
        last_int = command_result_parser.get_last_int_in_port_channel(
            device.execute_command(f'sh int {interface}'))

        return last_int
    return interface


def get_nihul_ip(device, nihul_vlans):
    ip = command_result_parser.get_ip_of_nihul_vlan(
        device.execute_command(f'sh ip int b'), nihul_vlans)

    return ip


def get_nihul_vlans(device):
    nihul_vlans = command_result_parser.get_nihul_vlans_from_vrf(
        device.execute_command(f'sh vrf'))

    return nihul_vlans


def get_next_hop_hostname_cdp(device, next_hop_interface):
    next_hop_id = command_result_parser.get_next_hop_id_from_cdp(
        device.execute_command(f'sh cdp n {next_hop_interface} d'))

    return next_hop_id


def get_route_information_cef(device, vrf, destination_network):
    try:
        if vrf == 'default':
            nexthop_ip, mpls_label = command_result_parser.get_next_hop_ip_and_protocol_from_cef(
                device.execute_command(f'sh ip cef {destination_network}'))
        else:
            nexthop_ip, mpls_label = command_result_parser.get_next_hop_ip_and_protocol_from_cef(
                device.execute_command(f'sh ip cef vrf {vrf} {destination_network}'))
    except TypeError:
        raise WrongDeviceTypeSuspicion()

    return nexthop_ip, mpls_label


def get_route_information_route(device, vrf, destination_network):
    protocol, nexthop_ip = command_result_parser.get_next_hop_ip_and_protocol_from_route(
        device.execute_command(f'sh ip route vrf {vrf} {destination_network}'))

    return nexthop_ip


def get_mpls_next_hop_ip(device, mpls_label):
    nexthop_ip, next_label = command_result_parser.get_next_hop_ip_from_mpls_ldp(
        device.execute_command(f'sh mpls ldp forwarding local-label {mpls_label}'))

    if not nexthop_ip:
        nexthop_ip, next_label = command_result_parser.get_next_hop_ip_from_mpls_forwarding(
            device.execute_command(f'sh mpls forwarding labels {mpls_label}'))

    if not nexthop_ip:  # If XE
        lib_entry = command_result_parser.get_lib_entry_from_mpls_ldp_bindings(
            device.execute_command(f'sh mpls ldp bindings local-label {mpls_label}'))
        nexthop_ip, next_label = command_result_parser.get_next_hop_ip_and_protocol_from_cef(
            device.execute_command(f'sh ip cef {lib_entry}'))

    return nexthop_ip, next_label


def get_route_and_new_vrf_from_firewall(device, destination_network):
    device.close_connection()
    device = CheckpointFirewall(device.hostname, fw_username, fw_password, immediately_connect=False)
    device.connect()
    device.execute_command('clish')
    command_result = device.execute_command(f'show route destination {destination_network}')
    device.disconnect()

    nexthop_ip = command_result_parser.get_next_hop_ip_from_firewall(command_result)

    return nexthop_ip


def get_int_vrf_by_int_ip(device, nexthop_int_ip):
    interface = command_result_parser.get_next_int_of_int_ip_via_int_br(
        device.execute_command(f'sh ip int br | i {nexthop_int_ip}'))

    new_vrf = command_result_parser.get_vrf_from_run_int(
        device.execute_command(f'sh run int {interface} | i vrf'))

    device.close_connection()
    return new_vrf if new_vrf else 'default'


def get_fe_ip_from_lisp_eid_table(device, destination_network):
    protocol, nexthop_ip = command_result_parser.get_fe_ip_from_lisp_eid_table(
        device.execute_command(f'sh lisp eid-table vrf AH site | i {destination_network}'))

    return nexthop_ip


def get_route_information_traffic_eng(device, vrf, source_ip, destination_network):

    affinity_tag = command_result_parser.get_affinity_tag(
        device.execute_command(f'sh cef vrf {vrf} exact-route {source_ip} {destination_network}'))

    nexthop_ip, next_label = command_result_parser.get_nexthop_and_label_from_mpls_forwarding(
        device.execute_command(f'sh mpls forwarding tunnels name {affinity_tag}'))

    return nexthop_ip, next_label

