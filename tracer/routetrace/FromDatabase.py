from pprint import pprint

from tracer.routetrace import command_result_parser
from tracer.routetrace.trino_connect import TrinoDatalake, HttpError
from time import sleep


class DataBaseError(Exception):
    def __init__(self, message="Couldn't find requested information in the database."):
        self.message = message
        super().__init__(self.message)


def error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except IndexError:
            raise DataBaseError
        except HttpError:
            try:
                sleep(8)
                result = func(*args, **kwargs)
            except HttpError or IndexError:
                sleep(12)
                result = func(*args, **kwargs)
        return result

    return wrapper


def create_connection_instance():
    return TrinoDatalake()


def get_default_gateway(datalake, endpoint_ip):
    try:
        return get_default_gateway_regular(datalake, endpoint_ip)
    except DataBaseError:
        try:
            return get_default_gateway_extended(datalake, endpoint_ip)
        except DataBaseError:
            try:
                return get_default_gateway_by_segment(datalake, endpoint_ip)
            except DataBaseError:
                return None


@error_handler
def get_default_gateway_regular(datalake, endpoint_ip):
    default_gateway = datalake.exec_query(f"""
                                select device_ip, device_id
                                from network."crawler-arp-table"
                                where ip='{endpoint_ip}' and vrf != 'default'
                                order by timestamp desc
                                    """)

    default_gateway_ip = default_gateway[0][0][0]
    hostname = default_gateway[0][0][1]

    return default_gateway_ip, hostname


@error_handler
def get_default_gateway_extended(datalake, endpoint_ip):
    default_gateway = datalake.exec_query(f"""
                                select device_ip, device_id
                                from network."crawler-arp-table"
                                where ip='{endpoint_ip}'
                                order by timestamp desc
                                    """)

    default_gateway_ip = default_gateway[0][0][0]
    hostname = default_gateway[0][0][1]

    return default_gateway_ip, hostname


@error_handler
def get_default_gateway_access_only(datalake, endpoint_ip):
    default_gateway_ip = datalake.exec_query(f"""
                                select gateway_device_ip
                                from network."v_site_arps_from_up_access_interfaces"
                                where endpoint_ip='{endpoint_ip}'
                                order by arp_timestamp
                                    """)

    default_gateway_ip = default_gateway_ip[0][0][0]

    return default_gateway_ip


@error_handler
def get_next_hop_int_by_mac_table(datalake, from_ip, mac):
    next_hop_interface = datalake.exec_query(f"""
                                select interface
                                from network."crawler-mac-table"
                                where device_ip='{from_ip}' and mac='{mac}'
                                order by timestamp desc
                                    """)

    next_hop_interface = next_hop_interface[0][0][0]

    return next_hop_interface


@error_handler
def default_gateway_step(datalake, dg_ip, endpoint_ip):
    result = datalake.exec_query(f"""
                                    select device_id, vrf, mac, interface
                                    from network."crawler-arp-table"
                                    where device_ip='{dg_ip}' and ip='{endpoint_ip}'
                                    order by timestamp
                                        """)[0][0]

    device_id = result[0]
    vrf = result[1]
    mac = result[2]
    interface_or_vlan = result[3]

    return device_id, vrf, mac, interface_or_vlan


@error_handler
def get_next_hop_ip_cdp(datalake, id_, next_hop_interface):
    id_ = remove_services(id_)

    result = datalake.exec_query(f"""
                                        select remote_ipv4, remote_device_id
                                        from network."crawler-cdp-lldp"
                                        where local_device_id='{id_}' and local_int like '%{next_hop_interface}%'
                                        order by timestamp
                                            """)

    result = result[0][0]

    remote_ipv4 = result[0]
    remote_device_id = result[1]

    return remote_ipv4, remote_device_id


@error_handler
def remove_services(next_hop_id):
    n_h_id = ''
    is_before_services = True

    for part in next_hop_id.split('.'):
        if part.lower() == 'services':
            is_before_services = False

        if is_before_services:
            n_h_id += f'.{part}'

    return n_h_id.strip('.')


@error_handler
def get_nihul_ip(datalake, next_hop_id):
    next_hop_id = remove_services(next_hop_id)

    ip = datalake.exec_query(f"""
                                select ipv4
                                from network."v_spectrum_network_devices"
                                where device_id like '%{next_hop_id}%'
                                order by timestamp
                                    """)[0][0][0]

    return ip


@error_handler
def get_device_id_by_nihul_ip(datalake, ip):
    id_ = datalake.exec_query(f"""
                                select device_id
                                from network."spectrum-devices"
                                where ipv4='{ip}'
                                order by timestamp
                                    """)

    id_ = id_[0][0][0]

    return id_


@error_handler
def get_device_id(datalake, ip):
    id_ = datalake.exec_query(f"""
                                select device_id
                                from network."static-device-tags"
                                where ipv4='{ip}'
                                order by timestamp
                                    """)

    id_ = id_[0][0][0]

    return id_


@error_handler
def is_destination(datalake, id_, next_hop_interface):
    id_ = remove_services(id_)

    next_hop_interface = ''.join(ch for ch in next_hop_interface if ch.isdigit() or ch == '/' or ch == '.')

    conf = datalake.exec_query(f"""
                                select config_running
                                from network."crawler-interface-config"
                                where interface like '%{next_hop_interface}%' and device_id like '%{id_}%'
                                order by timestamp
                                    """)

    conf = conf[0][0][0]

    if command_result_parser.get_switchport_mode(conf) == 'access':
        return True
    return False


@error_handler
def first_int_in_port_channel(datalake, id_, interface):
    if not interface.lower().startswith('po'):
        return interface

    id_ = remove_services(id_)

    physical_interface = datalake.exec_query(f"""
                                select phyinterface
                                from network."crawler-device-portchannels"
                                where pointerface='{interface}' and device_id like '%{id_}%'
                                order by timestamp
                                    """)

    physical_interface = physical_interface[0][0][0]

    return physical_interface


@error_handler
def get_next_hop_int_by_arp_access_mac(datalake, from_ip, mac):
    next_hop_device_id = datalake.exec_query(f"""
                                    select connected_device_id
                                    from network."v_site_arps_from_up_access_interfaces"
                                    where gateway_device_ip='{from_ip}' and endpoint_mac='{mac}'
                                    order by arp_timestamp
                                        """)

    next_hop_device_id = next_hop_device_id[0][0][0]

    return next_hop_device_id


@error_handler
def get_next_hop_int_by_arp_access_ip(datalake, from_ip, endpoint_ip):
    res = datalake.exec_query(f"""
                                select gateway_device_id, endpoint_mac
                                from network."v_site_arps_from_up_access_interfaces"
                                where gateway_device_ip='{from_ip}' and endpoint_ip='{endpoint_ip}'
                                order by arp_timestamp
                                    """)

    res = res[0][0]
    gateway_device_id = res[0]
    endpoint_mac = res[1]

    return gateway_device_id, endpoint_mac


@error_handler
def get_next_hop_id_mac_by_arp_ip(datalake, from_ip, endpoint_ip):
    res = datalake.exec_query(f"""
                                select device_id, mac, interface, vrf
                                from network."crawler-arp-table"
                                where device_ip='{from_ip}' and ip='{endpoint_ip}'
                                order by timestamp desc
                                    """)

    res = res[0][0]
    gateway_device_id = res[0]
    endpoint_mac = res[1]
    interface = res[2]
    vrf = res[3]

    return gateway_device_id, endpoint_mac, interface, vrf


@error_handler
def get_route_information(datalake, ip, vrf, destination_network):
    res = datalake.exec_query(f"""
                                select nexthop, vrf, network
                                from network."crawler-route-table"
                                where device_ip='{ip}' and vrf='{vrf}'
                                order by timestamp
                                    """)

    res = res[0][0]
    nexthop_ip = res[0]

    return nexthop_ip


@error_handler
def get_neighbor_ip_by_id(datalake, ip, interface):
    remote_device_ip = datalake.exec_query(f"""
                                select remote_device_ip, local_device_int
                                from network."v_network_device_interfaces_neighbors"
                                where local_device_ip='{ip}'
                                order by timestamp
                                    """)

    remote_device_ip = remote_device_ip[0][0]

    return remote_device_ip


@error_handler
def get_nihul_ip_by_int_ip(datalake, nexthop_int_ip):
    nexthop = datalake.exec_query(f"""
                                    select ipv4, device_id
                                    from network."crawler-device-interface-inventory"
                                    where int_ip='{nexthop_int_ip}'
                                    order by timestamp DESC
                                        """)

    nexthop = nexthop[0][0]
    nexthop_ip = nexthop[0]
    hostname = nexthop[1]

    return nexthop_ip, hostname


def get_default_gateway_by_segment(datalake, segment: str):
    def change_last_ip_part(seg, last_part):
        return '.'.join(seg.split(".")[:3]) + f'.{last_part}'

    try:
        ip, hostname = get_nihul_ip_by_int_ip(datalake, change_last_ip_part(segment, '254'))
    except DataBaseError:
        ip, hostname = get_nihul_ip_by_int_ip(datalake, change_last_ip_part(segment, '1'))

    return ip, hostname


@error_handler
def get_first_int_if_portchannel(datalake, id_, interface):
    if not interface.lower().startswith('po'):
        return interface

    phyinterface = datalake.exec_query(f"""
                                    select phyinterface
                                    from network."crawler-device-portchannels"
                                    where device_id='{id_}' and pointerface='{interface}'
                                    order by timestamp
                                        """)[0]

    if not phyinterface:
        return None

    phyinterface = phyinterface[0][0]

    return phyinterface


@error_handler
def get_ip_by_device_name(datalake, name):
    ip = datalake.exec_query(f"""
                                    select ipv4
                                    from network."crawler-devices"
                                    where device_id='{name}'
                                    order by timestamp
                                        """)[0][0][0]

    return ip

@error_handler
def get_device_name_by_ip(datalake, ip):
    """
    Retrieves the device name associated with a given IP address from the

    Args:
        datalake (object): The datalake object used for querying.
        ip (str): The IP address to look up.

    Returns:
        str: The device name associated with the given IP address.
    """

    device_name = datalake.exec_query(f"""
                                    select device_id
                                    from network."crawler-devices"
                                    where ipv4='{ip}'
                                    order by timestamp desc
                                    limit 1
                                """)[0][0][0]

    return device_name
