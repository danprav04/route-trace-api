from AI_parser.parser import parse_data


def get_vlan_from_ip_int_brief(ip_int_brief):
    return parse_data(ip_int_brief, 'vlan from ip int brief')[0]

def get_mac_interface_from_arp(arp):
    data = parse_data(arp, 'mac and interface from arp')
    return data[0], data[1]

def get_next_hop_from_cdp(cdp):
    data = parse_data(cdp, 'next hop ip and device id from cdp')
    return data[0], data[1]

def get_next_hop_int_from_mac_table(mac_table):
    return parse_data(mac_table, 'next hop interface from mac table')[0]

def get_switchport_mode(run_int):
    return parse_data(run_int, 'switchport mode from run int')[0]

def get_vrf_from_run_int_vlan(run_int_vlan):
    return parse_data(run_int_vlan, 'vrf from run int vlan')[0]

def get_last_int_in_port_channel(sh_int):
    return parse_data(sh_int, 'last int in port channel')[0]

def get_nihul_vlans_from_vrf(sh_vrf):
    return parse_data(sh_vrf, 'nihul vlans from vrf')

def get_ip_of_nihul_vlan(sh_ip_int, nihul_vlans):
    return parse_data(sh_ip_int, f'ip of nihul vlan {nihul_vlans}')[0]

def get_next_hop_id_from_cdp(cdp):
    return parse_data(cdp, 'next hop id from cdp')[0]

def get_next_hop_ip_and_protocol_from_cef(cef):
    data = parse_data(cef, """
    next hop ip and mpls label if exists from cef. 
    if there is no mpls label, get only the ip. 
    if there is mpls label, get the ip and the label. 
    No need for anything else other than this, 
    the output object should consist only of the ip and the label if its there.
    A route with mpls label must have the words label or labels in the row.
    Don't get the protocol
    """)[0]

    if len(data) == 2:
        return data[0], data[1]
    else:
        return data[0], None

def get_next_hop_ip_and_protocol_from_route(route):
    data = parse_data(route, 'next hop ip and protocol from route')
    if len(data) == 2:
        return data[0], data[1]
    else:
        return data[0], None

def get_next_hop_ip_from_mpls_ldp(mpls_ldp):
    data = parse_data(mpls_ldp, 'next hop ip from mpls ldp')
    if len(data) == 2:
        return data[0], data[1]
    else:
        return data[0], None

def get_lib_entry_from_mpls_ldp_bindings(mpls_ldp_bindings):
    return parse_data(mpls_ldp_bindings, 'lib entry from mpls ldp bindings')[0]

def get_next_hop_ip_from_firewall(fw_sh_route):
    return parse_data(fw_sh_route, 'next hop ip from firewall')[0]

def get_next_int_of_int_ip_via_int_br(int_br):
    return parse_data(int_br, 'next int of int ip via int br')[0]

def get_vrf_from_run_int(run_int):
    return parse_data(run_int, 'vrf from run int')[0]

def get_fe_ip_from_lisp_eid_table(lisp_eid_table):
    return parse_data(lisp_eid_table, 'fe ip from lisp eid table')[0]