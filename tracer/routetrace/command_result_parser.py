from tracer.routetrace.regex_patterns import mac_pattern, ip_pattern, interface_pattern, ip_with_prefix_pattern, int_or_subint_pattern
import re


def get_ip_vrf_from_route_vrf_all_ip(route_vrf_all_ip):

    routes = []

    words = route_vrf_all_ip.split()
    for i, word in enumerate(words):
        if re.match(pattern=ip_with_prefix_pattern, string=word):
            prefix = word.split('/')[1]
            routes.append((prefix, words[i-4]))

    routes.sort()
    return routes[0][1]


def get_mac_interface_from_arp(arp):

    return re.findall(pattern=rf'({mac_pattern}).*\s({interface_pattern})', string=arp.lower())[0][:2]


def get_next_hop_from_cdp(cdp):
    device_id = None
    ip = None

    for line in cdp.splitlines():
        line = line.strip()

        var = 'Device ID: '
        if line.startswith(var):
            device_id = line.lstrip(var)

        var = 'IPv4 address: '
        if line.startswith(var):
            ip = line.lstrip(var)

        var = 'IP address: '
        if line.startswith(var):
            ip = line.lstrip(var)

    return ip, device_id.replace('', '')


def get_next_hop_int_from_mac_table(mac_table):

    return re.findall(pattern=rf'\s{mac_pattern}.*\s({interface_pattern})\s', string=mac_table)[0][0]


def get_switchport_mode(run_int):
    lines = run_int.splitlines()
    for line in lines:
        if line.strip().startswith('switchport mode '):
            return re.findall(pattern=r'switchport mode (trunk|access)', string=line)[0]
    return None


def get_vlan_from_ip_int_brief(ip_int_brief):

    for word in ip_int_brief.split():
        if re.match(pattern=interface_pattern, string=word.lower()):
            return word


def get_vrf_from_run_int_vlan(run_int_vlan):
    for line in run_int_vlan.splitlines():
        if line.strip().startswith('ip vrf forwarding '):
            return line.split()[-1]
    return None


def get_last_int_in_port_channel(sh_int):
    for line in sh_int.splitlines():
        if line.strip().startswith('Members in this channel: '):
            return line.split()[-1]
    return None


def get_nihul_vlans_from_vrf(sh_vrf):
    in_vrf = False
    vlans = []

    for line in sh_vrf.splitlines():
        if in_vrf and len(line) > 1:
            vlans.append(line.split()[-1])
            in_vrf = False
        if line.strip().startswith('Nihul'):
            in_vrf = True

        if in_vrf:
            vlans.append(line.split()[-1])

    return vlans


def get_ip_of_nihul_vlan(sh_ip_int, nihul_vlans):
    for line in sh_ip_int.splitlines():
        for vlan in nihul_vlans:
            if line.strip().startswith(vlan.replace('Vl', 'Vlan')):
                return re.findall(pattern=rf'({ip_pattern})', string=line)[0]
    return None


def get_next_hop_id_from_cdp(cdp):
    for line in cdp.splitlines():
        if line.strip().startswith('Device ID: '):
            return line.split()[-1]
    return None


class SDABorderSuspicion(Exception):
    def __init__(self, message="Could be an SDA border, another behaviour required."):
        self.message = message
        super().__init__(self.message)


class TrafficEngSuspicion(Exception):
    pass


def get_next_hop_ip_and_protocol_from_cef(cef):
    lines = cef.splitlines()

    on_backup_route = False
    for line in lines:
        if not on_backup_route and 'backup' in line.split():
            on_backup_route = True
        elif on_backup_route and line.strip().startswith('via'):
            on_backup_route = False
        if on_backup_route:
            continue

        if 'Null0' in line:
            raise SDABorderSuspicion
        if line.strip().startswith('receive'):
            return 'end', None
        if re.match(pattern=rf'.*(next hop|nexthop)\s+{ip_pattern}', string=line):
            if lines.index(line) + 1 < len(lines) and 'label' in lines[lines.index(line) + 1]:
                if 'ImplNull' in lines[lines.index(line) + 1]:
                    raise TrafficEngSuspicion
                else:
                    continue

            next_hop = re.findall(pattern=rf'({ip_pattern})', string=line)[0]

            matches = re.findall(pattern=ip_pattern + r'.*(?:label \[(\d+)\|\d+\]|labels imposed {(\d+)|label (\d+)-)', string=line)
            mpls_label = next((val for val in matches[0] if val), None) if matches else None

            return next_hop, mpls_label

    return None


def get_next_hop_ip_and_protocol_from_route(route):
    protocol, nexthop_ips = None, []

    for line in route.splitlines():
        if re.match(pattern=rf'({ip_pattern})', string=line.split()[0]):
            nexthop_ips.append(re.findall(pattern=rf'({ip_pattern})', string=line)[0])

        if line.strip().startswith('Known via '):
            return re.findall(pattern=rf'Known via "(.+)"', string=line)[0]

    return protocol, nexthop_ips


def get_next_hop_ip_from_mpls_ldp(mpls_ldp):
    for line in mpls_ldp.splitlines():
        data = re.findall(pattern=rf'{ip_pattern}/.*\s(\d+|ImpNull)\s.*\s({ip_pattern})\s', string=line)
        if data:
            data = data[0]
            next_label = data[0]
            next_hop_ip = data[1]
            return next_hop_ip, next_label if next_label != 'ImpNull' else None
    return None, None


def get_next_hop_ip_from_mpls_forwarding(mpls_forwarding):
    for line in mpls_forwarding.splitlines():
        if re.search(pattern=ip_pattern, string=line):
            words = line.split()
            return words[5], words[1] if words[1] != 'Pop' else None
    return None, None


def get_lib_entry_from_mpls_ldp_bindings(mpls_ldp_bindings):
    for line in mpls_ldp_bindings.splitlines():
        if line.strip().startswith('lib entry: '):
            return re.findall(pattern=rf'({ip_pattern})', string=line)[0]
    return None


class Suspicion8200(Exception):
    def __init__(self, message="It probably leads to 8200 devices."):
        self.message = message
        super().__init__(self.message)


def get_next_hop_ip_from_firewall(fw_sh_route):
    for line in fw_sh_route.splitlines():
        if re.findall(pattern=rf'(is directly connected)', string=line):
            raise Suspicion8200
        next_hop_suspect = re.findall(pattern=rf'.\s+{ip_pattern}.*via ({ip_pattern})', string=line)
        if next_hop_suspect:
            return next_hop_suspect[0]
    return None


def get_next_int_of_int_ip_via_int_br(int_br):
    for line in int_br.splitlines():
        interface = re.findall(pattern=rf'({int_or_subint_pattern})\s+{ip_pattern}', string=line)
        if interface:
            return interface[0][0]
    return None


def get_vrf_from_run_int(run_int):
    for line in run_int.splitlines():
        if 'vrf' in line.lower() and not ('description' in line.lower()):
            return line.split()[-1]
    return None


def get_fe_ip_from_lisp_eid_table(lisp_eid_table):
    for line in lisp_eid_table.splitlines():
        if 'vrf' in line.lower():
            return line.split()[-1]
    return None


def get_affinity_tag(cef_exact_route):
    """
    Extracts the C1-10g-2-G4-U4-C4 string from the given cef_exact_route.

    Args:
        cef_exact_route (str): The input string containing the route information.

    Returns:
        str: The extracted C1-10g-2-G4-U4-C4 string or None if not found.
    """

    # Split the input string into lines
    lines = cef_exact_route.splitlines()

    # Initialize the result variable to None
    result = None

    # Iterate over each line
    for line in lines:
        # Use regex to search for the pattern in each line
        match = re.search(r'via\s+([A-Za-z0-9-]+)', line)

        # If a match is found, extract the first group (which contains the C1-10g-2-G4-U4-C4 string)
        if match:
            result = match.group(1)
            break

    return result


def get_next_hop_ip_and_label_from_mpls_forwarding(mpls_forwarding):
    """
    Extract next hop IP and port from MPLS forwarding string.

    Args:
        mpls_forwarding (str): MPLS forwarding string.

    Returns:
        tuple: Next hop IP and port, or None if not found.
    """
    # Split the string into lines
    lines = mpls_forwarding.splitlines()

    # Initialize variables to store the results
    next_hop_ip = None
    next_hop_label = None

    # Iterate over each line
    for line in lines:
        if 'TE:' in line:
            # Extract IP address
            ip_address = re.search(ip_pattern, line).group()
            next_hop_ip = ip_address

            # Extract second number
            numbers = [num for num in re.findall(r'\d+|pop', line.lower())]
            second_number = numbers[1]
            next_hop_label = second_number

            break

    # Return the extracted IP and port
    if next_hop_ip and next_hop_label:
        return next_hop_ip, None if next_hop_label.lower() == 'pop' else next_hop_label
    else:
        return None


def get_tunnel_id(mpls_traffic_eng):
    """
    Extracts the Tunnel-ID from the given mpls_traffic_eng.

    Args:
        mpls_traffic_eng (str): The input string containing the tunnel information.

    Returns:
        int: The extracted Tunnel-ID or None if not found.
    """

    # Split the input string into lines
    lines = mpls_traffic_eng.splitlines()

    # Initialize the result variable to None
    result = None

    # Iterate over each line
    for line in lines:
        # Use regex to search for the pattern in each line
        match = re.search(r'Tunnel-ID:\s+(\d+)', line)

        # If a match is found, extract the first group (which contains the Tunnel-ID)
        if match:
            result = int(match.group(1))
            break

    return result


def get_nexthop_and_label_from_mpls_forwarding(mpls_forwarding):
    """
    Extracts the MPLS label and next hop IP from the given MPLS forwarding table.

    Args:
    mpls_forwarding (str): The MPLS forwarding table text.

    Returns:
    tuple: A tuple containing the MPLS label and next hop IP.
    """
    lines = mpls_forwarding.splitlines()

    for line in lines:
        if re.search(ip_pattern, line):
            words = line.split()
            return words[3], words[1]

    return None, None
