from netmiko import ConnectHandler


class CheckpointFirewall:
    def __init__(self, ip, username, password, immediately_connect=True):
        self.device = {
            'device_type': 'checkpoint_gaia',
            'ip': ip,
            'username': username,
            'password': password
        }

        self.net_connect = None
        if immediately_connect:
            self.connect()

    def connect(self):
        self.net_connect = ConnectHandler(**self.device)

    def execute_command(self, command):
        if self.net_connect:
            output = self.net_connect.send_command_timing(command)
            return output
        else:
            print('Not connected to the firewall, run connect method first.')

    def disconnect(self):
        if self.net_connect:
            self.net_connect.disconnect()
