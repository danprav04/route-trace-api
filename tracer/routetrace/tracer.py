from Tufin.Tufin import SecureTrackAPI
from tracer.routetrace.command_result_parser import TrafficEngSuspicion
from tracer.routetrace.models import MacTraceHop, RouteTraceHop
from tracer.routetrace import FromDatabase
from tracer.routetrace import FromDevices
from tracer.routetrace import converter


class Tracer:
    def __init__(self, log, username, password, datalake=None, tufin=None):
        self.log = log
        self.username = username
        self.password = password
        self.datalake = datalake or FromDatabase.create_connection_instance()
        self.tufin = tufin or SecureTrackAPI()

    def find_route(self, source_ip, destination_ip):
        FromDevices.dev_user = self.username
        FromDevices.dev_pass = self.password

        source_dg_ip, hostname = FromDatabase.get_default_gateway(self.datalake, endpoint_ip=source_ip)
        destination_dg_ip, hostname = FromDatabase.get_default_gateway(self.datalake, endpoint_ip=destination_ip)

        if not source_dg_ip:
            return []

        if not destination_dg_ip:
            destination_dg_ip = ".".join(destination_ip.split('.')[:-1])

        dg_to_source_trace, src_vrf = self.find_lan_route_to_endpoint(source_ip, source_dg_ip)
        dg_to_dg_trace = self.find_wan_route_dg_to_dg(source_dg_ip, destination_ip, src_vrf, destination_dg_ip, hostname)

        dg_to_destination_trace = []
        if destination_dg_ip:
            dg_to_destination_trace, dest_vrf = self.find_lan_route_to_endpoint(destination_ip, destination_dg_ip)

        final_route = dg_to_source_trace[::-1] + dg_to_dg_trace + dg_to_destination_trace

        final_route = self.clean_route(final_route)

        return final_route

    def find_route_wan_to_lan(self, source_ip, source_vrf, destination_ip):
        FromDevices.dev_user = self.username
        FromDevices.dev_pass = self.password

        destination_dg_ip, hostname = FromDatabase.get_default_gateway(self.datalake, endpoint_ip=destination_ip)
        dg_to_dg_trace = self.find_wan_route_dg_to_dg(source_ip, destination_ip, source_vrf, destination_dg_ip, hostname)
        dg_to_destination_trace, dest_vrf = self.find_lan_route_to_endpoint(destination_ip, destination_dg_ip)

        return self.clean_route(dg_to_destination_trace[::-1] + dg_to_dg_trace[::-1])[::-1]

    @staticmethod
    def clean_route(route):
        cleaned_route = []
        for index, device in enumerate(route):
            if len(route) > index+1:
                if not device.ip == route[index+1].ip:
                    cleaned_route.append(device)
            else:
                cleaned_route.append(device)

        return cleaned_route

    def find_wan_route_dg_to_dg(self, source_ip, source_dg, destination_network, vrf, destination_dg_ip, hostname):
        FromDevices.dev_user = self.username
        FromDevices.dev_pass = self.password
        route = []

        if self.route_trace(route=route,
                            source_ip=source_ip,
                            ip=source_dg,
                            destination_network=destination_network,
                            vrf=vrf,
                            destination_dg_ip=destination_dg_ip,
                            nexthop_hostname=hostname,
                            ):
            return route

    def route_trace(self, route, source_ip, ip, destination_network, vrf, destination_dg_ip, mpls_label=None, nexthop_int_ip=None, passed_firewall=None, nexthop_hostname=''):
        try:

            if nexthop_int_ip == destination_network:
                return True

            route.append(RouteTraceHop(ip, destination_network, vrf, destination_dg_ip, mpls_label, nexthop_int_ip, passed_firewall, nexthop_hostname))
            self.log(f"Route: {route[-1]}")

            nexthop_hostname = ''

            if len(route) > 3 and ip == route[-3].ip and ip == route[-5]:
                return True

            hop = FromDevices.create_device(ip, connect=False)

            passed_firewall = False
            try:
                try:
                    hop.connect()
                except Exception as e:
                    raise FromDevices.WrongDeviceTypeSuspicion

                if mpls_label:
                    nexthop_int_ip, mpls_label = FromDevices.get_mpls_next_hop_ip(hop, mpls_label)
                else:
                    nexthop_int_ip, mpls_label = FromDevices.get_route_information_cef(hop, vrf, destination_network)
            except FromDevices.WrongDeviceTypeSuspicion:
                try:
                    nexthop_int_ip = FromDevices.get_route_and_new_vrf_from_firewall(hop, destination_network)
                    passed_firewall = True
                    route[-1].type = 'firewall'
                except Exception as e:
                    print(str(e))
                    return True
            except FromDevices.SDABorderSuspicion:
                hop.connect()
                nexthop_int_ip = FromDevices.get_fe_ip_from_lisp_eid_table(hop, destination_network)
            except TrafficEngSuspicion:
                nexthop_int_ip, mpls_label = FromDevices.get_route_information_traffic_eng(hop, vrf, source_ip, destination_network)

            if nexthop_int_ip == 'end':
                return True

            try:
                nexthop_ip, nexthop_hostname = FromDatabase.get_nihul_ip_by_int_ip(self.datalake, nexthop_int_ip)
            except FromDatabase.DataBaseError:
                firewall = self.tufin.get_firewall_with_interface_ip(nexthop_int_ip)
                if firewall:
                    nexthop_ip = firewall['ip']
                    nexthop_hostname = firewall['name']
                else:
                    nexthop_ip = nexthop_int_ip

            if passed_firewall or vrf == 'default':
                try:
                    vrf = FromDevices.get_int_vrf_by_int_ip(FromDevices.create_device(nexthop_ip), nexthop_int_ip)
                except Exception as e:
                    self.log(str(e))
                    return True

            return self.route_trace(route, source_ip, nexthop_ip, destination_network, vrf, destination_dg_ip, mpls_label, nexthop_int_ip, passed_firewall, nexthop_hostname)
        except Exception as e:
            self.log(str(e))
            return True

    def find_lan_route_to_endpoint(self, endpoint_ip, dg_ip):
        FromDevices.dev_user = self.username
        FromDevices.dev_pass = self.password
        try:
            gateway_device_id, endpoint_mac, interface, vrf = FromDatabase.get_next_hop_id_mac_by_arp_ip(self.datalake, dg_ip, endpoint_ip)
            next_hop_interface = converter.get_int_from_subint_if_subint(interface)

            mac_route = []
            if self.mac_trace(mac_route, dg_ip, gateway_device_id, endpoint_mac, next_hop_interface):
                return mac_route, vrf
        except Exception as e:
            self.log(str(e))
            return [], ''

    def mac_trace(self, mac_route, ip, id_, mac, next_hop_interface, next_hop_int_ip=None):
        try:
            device = FromDevices.create_device(ip)

            if not next_hop_interface:
                next_hop_interface = FromDevices.get_next_hop_int_mac_address_table(device, mac)
                next_hop_interface = FromDatabase.get_first_int_if_portchannel(self.datalake, id_, next_hop_interface) or FromDevices.last_int_in_port_channel(device, next_hop_interface)

            mac_route.append(MacTraceHop(ip, id_, mac, next_hop_int_ip, next_hop_interface))
            self.log(f"Mac: {mac_route[-1]}")

            if FromDatabase.is_destination(self.datalake, id_, next_hop_interface):
                return True

            next_hop_int_ip, next_hop_id = FromDevices.get_next_hop_ip_cdp(device, next_hop_interface)
            next_hop_ip = FromDatabase.get_nihul_ip_by_int_ip(self.datalake, next_hop_int_ip)[0]

            next_hop_interface = None
            return self.mac_trace(mac_route, next_hop_ip, next_hop_id, mac, next_hop_interface, next_hop_int_ip)
        except Exception as e:
            self.log(str(e))
            return True
