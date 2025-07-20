import ipaddress

import requests
import json
from requests.auth import HTTPBasicAuth
import warnings
from urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter('ignore', category=InsecureRequestWarning)

class SecureTrackAPI:
    def __init__(self, url="https://{sensitive-ip}/securetrack/api/",
                 username="{username-sensitive}", password="{password-sensitive}"):
        """
        Initialize the SecureTrackAPI class.

        Args:
            url (str): The URL of the API endpoint.
            username (str): The username for authentication.
            password (str): The password for authentication.
        """

        self.url = url
        self.username = username
        self.password = password

        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.username, self.password)

    def get_firewall_with_interface_ip(self, interface_ip):
        firewalls = self.get_firewalls()
        for firewall in firewalls:
            interfaces = self.get_firewall_interfaces(firewall['id'])
            for interface in interfaces:
                if 'ip' in interface and interface['ip'] == interface_ip:
                    firewall['interfaces'] = interfaces
                    return firewall

    def get_firewalls_with_interfaces(self):
        firewalls = self.get_firewalls()
        for firewall in firewalls:
            interfaces = self.get_firewall_interfaces(firewall['id'])
            firewall['interfaces'] = interfaces

        return firewalls

    def get_firewall_interfaces(self, firewall_id):
        response = self.session.get(self.url + f'devices/{firewall_id}/interfaces.json', verify=False)
        if response.status_code == 200:
            return response.json()['interfaces']['interface']
        else:
            response = self.session.get(self.url + f'devices/topology_interfaces.json?mgmtId={firewall_id}', verify=False)
            if response.status_code == 200:
                return response.json()['interface']
            else:
                raise Exception("Failed to retrieve data: {}".format(response.text))

    def get_firewalls(self):
        return [device for device in self.get_devices()['device'] if 'fw' in device['name'].lower()]

    def get_devices(self):
        response = self.session.get(self.url + 'devices.json', verify=False)
        if response.status_code == 200:
            return response.json()['devices']
        else:
            raise Exception("Failed to retrieve data: {}".format(response.text))

    # @staticmethod
    # def extract_main_route_v2(route):
    #     traffic_allowed = route['path_calc_results']['traffic_allowed']
    #     route = route['path_calc_results']['device_info']
    #     main_route = []
    #
    #     main_route.append(route[0])
    #
    #     curr_index = 0
    #     while
    #
    #     return {"main_route": main_route, "traffic_allowed": traffic_allowed}

    @staticmethod
    def extract_main_route(route, destination_ip, src_vrf):

        traffic_allowed = route['path_calc_results']['traffic_allowed']
        route = route['path_calc_results']['device_info']

        if not route or len(route) == 0:
            return {"main_route": [], "traffic_allowed": traffic_allowed}

        main_route = []

        first_devices = []
        for hop in route:
            for incoming_interface in hop['incomingInterfaces']:
                if 'incomingVrf' in incoming_interface:
                    if src_vrf and not incoming_interface['incomingVrf'] == src_vrf:
                        continue

                    first_devices.append(hop)

        first_device = first_devices[0]
        main_route.append(first_device)

        next_hop_name = ''
        next_hop = first_device
        is_route_finished = False
        while next_hop_name != 'DIRECTLY_CONNECTED':
            if 'cloud' in next_hop_name.lower():
                break

            for next_device in next_hop['nextDevices']:
                if next_device['name'] == 'DIRECTLY_CONNECTED':
                    next_hop_name = 'DIRECTLY_CONNECTED'
                    is_route_finished = True

                for device_route in next_device['routes']:
                    network = ipaddress.ip_network(device_route['routeDestination'], strict=False)
                    ip_address = ipaddress.ip_address(destination_ip)
                    if ip_address in network:
                        next_hop_name = next_device['name']

            if is_route_finished:
                break

            for hop in route:
                if hop['name'] == next_hop_name:
                    next_hop = hop

            main_route.append(next_hop)

        return {"main_route": main_route, "traffic_allowed": traffic_allowed}

    def get_topology_path(self, src, dst, service="any"):
        """
        Get the topology path from the API.

        Args:
            src (str): The source IP address.
            dst (str): The destination IP address.
            service (str, optional): The service type. Defaults to "any".

        Returns:
            dict: The JSON response from the API.
        """
        params = {
            "src": src,
            "dst": dst,
            "service": service,
        }
        response = self.session.get(self.url+'topology/path.json', params=params, verify=False)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("Failed to retrieve data: {}".format(response.text))

    def get_topology_path_json(self, src, dst, service="any"):
        """
        Get the topology path from the API and return it as a JSON string.

        Args:
            src (str): The source IP address.
            dst (str): The destination IP address.
            service (str, optional): The service type. Defaults to "any".

        Returns:
            str: The JSON response from the API as a string.
        """
        data = self.get_topology_path(src, dst, service)
        return json.dumps(data, indent=4)

    def get_firewall_info(self, data):
        """
        Get the firewall information from the topology path data.

        Args:
            data (dict): The topology path data.

        Returns:
            dict: The firewall information.
        """
        firewall_info = {}
        for device in data["path_calc_results"]["device_info"]:
            if device["type"] == "mgmt":
                firewall_info["name"] = device["name"]
                firewall_info["vendor"] = device["vendor"]
                firewall_info["incoming_interfaces"] = device["incomingInterfaces"]
                firewall_info["next_devices"] = device["nextDevices"]
                firewall_info["bindings"] = device["bindings"]
                break
        return firewall_info

    def get_firewall_destination(self, data):
        """
        Get the firewall destination from the topology path data.

        Args:
            data (dict): The topology path data.

        Returns:
            str: The firewall destination.
        """
        for device in data["path_calc_results"]["device_info"]:
            if device["type"] == "mgmt":
                for binding in device["bindings"]:
                    for rule in binding["rules"]:
                        if rule["destinations"]:
                            return rule["destinations"][0]
        return None

    def get_next_hop(self, src, dst, service="any"):
        """
        Get the next hop from the API.

        Args:
            src (str): The source IP address.
            dst (str): The destination IP address.
            service (str, optional): The service type. Defaults to "any".

        Returns:
            str: The next hop IP address.
        """
        data = self.get_topology_path(src, dst, service)
        for device in data["path_calc_results"]["device_info"]:
            if device["type"] == "mgmt":
                if "next_devices" in device and device["next_devices"]:
                    for next_device in device["next_devices"]:
                        if "routes" in next_device and next_device["routes"]:
                            for route in next_device["routes"]:
                                return route["nextHopIp"]
        return None


# Example usage
if __name__ == "__main__":
    api = SecureTrackAPI(username="your_username", password="your_password")
    src = "{sensitive-ip}"
    dst = "{sensitive-ip}"
    data = api.get_topology_path(src, dst)
    print("\nFirewall Information:")
    print(json.dumps(api.get_firewall_info(data), indent=4))
    print("\nNextHop Information:")
    print(json.dumps(api.get_next_hop(src, dst), indent=4))
