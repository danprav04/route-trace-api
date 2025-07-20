import json


class MacTraceHop:
    def __init__(self, ip, id_, destination_mac, next_hop_int_ip, next_hop_interface):
        self.ip = ip
        self.id_ = id_
        self.destination_mac = destination_mac
        self.next_hop_int_ip = next_hop_int_ip
        self.next_hop_interface = next_hop_interface
        self.type = 'switch'

    def __repr__(self):
        return self.to_json()

    def to_dict(self, index: int = None):
        final = self.__dict__
        final['hop'] = index+1
        return final

    def to_json(self):
        return json.dumps(self.__dict__)


class RouteTraceHop:
    def __init__(self, ip, destination_network, vrf, destination_dg_ip, mpls_label, nexthop_int_ip, passed_firewall, hostname):
        self.ip = ip
        self.destination_network = destination_network
        self.vrf = vrf
        self.destination_dg_ip = destination_dg_ip
        self.mpls_label = mpls_label
        self.nexthop_int_ip = nexthop_int_ip
        self.passed_firewall = passed_firewall
        self.type = 'router'
        self.hostname = hostname

    def __repr__(self):
        return self.to_json()

    def to_dict(self, index: int = None):
        final = self.__dict__
        final['hop'] = index+1
        return final

    def to_json(self):
        return json.dumps(self.__dict__)
