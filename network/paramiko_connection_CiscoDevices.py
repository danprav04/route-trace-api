import time
import paramiko

AuthenticationException = paramiko.AuthenticationException


class SessionSSH:
    def __init__(self, hostname, username, password, port=22, immediately_connect=True):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port

        self.ssh_client = None
        if immediately_connect:
            self.connect()

    def __repr__(self):
        return f"SessionSSH object for: {self.hostname}"

    def connect(self):
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.ssh_client.connect(self.hostname, self.port, self.username, self.password)

    def execute_command(self, command):
        if not self.ssh_client or not self.ssh_client.get_transport().is_active():
            self.connect()

        try:
            channel = self.ssh_client.get_transport().open_session()
            channel.exec_command(command)

            while not channel.exit_status_ready():
                time.sleep(0.2)

            return channel.recv(64500).decode('utf-8')

        except Exception as e:
            print(f"Error executing command: {str(e)}")

        return None

    def close_connection(self):
        if self.ssh_client:
            self.ssh_client.close()
        else:
            print('SSH connection is not active.')


def create_device(ip, username, password):
    return SessionSSH(hostname=ip, username=username, password=password)

