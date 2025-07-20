import time
import paramiko
import telnetlib

class DeviceConnectionError(Exception):
    def __init__(self, message="Seems like there is no connection to the device."):
        self.message = message
        super().__init__(self.message)

class Session:
    def __init__(self, hostname, username, password, fallback_username='{login-sensitive}', fallback_password='{password-sensitive}', port=22, telnet_port=23, immediately_connect=True):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.fallback_username = fallback_username
        self.fallback_password = fallback_password
        self.port = port
        self.telnet_port = telnet_port

        self.ssh_client = None
        self.telnet_client = None
        if immediately_connect:
            self.connect()

    def __repr__(self):
        return f"Session object for: {self.hostname}"

    def connect(self):
        # Attempt to connect using SSH
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(self.hostname, self.port, self.username, self.password)
            return True
        except (TimeoutError, paramiko.AuthenticationException, paramiko.SSHException):
            # Attempt to connect with fallback credentials if primary credentials fail
            try:
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh_client.connect(self.hostname, self.port, self.fallback_username, self.fallback_password)
                print(f"Primary credentials failed. Connected using fallback credentials for {self.hostname}.")
                return True
            except (TimeoutError, paramiko.AuthenticationException, paramiko.SSHException):
                raise DeviceConnectionError

    def execute_command(self, command):
        if self.ssh_client:
            if not self.ssh_client.get_transport():
                self.connect()
            if not self.ssh_client.get_transport().is_active():
                self.connect()

            try:
                channel = self.ssh_client.get_transport().open_session()
                channel.exec_command(command)

                while not channel.exit_status_ready():
                    time.sleep(0.2)

                return channel.recv(64500).decode('utf-8')

            except Exception as e:
                print(f"Error executing command: {str(e)}")

        elif self.telnet_client:
            try:
                self.telnet_client.write(command.encode('ascii') + b"\n")
                time.sleep(0.5)  # Wait for the command to complete
                return self.telnet_client.read_eager().decode('utf-8')
            except Exception as e:
                print(f"Error executing command: {str(e)}")

        return None

    def close_connection(self):
        if self.ssh_client:
            self.ssh_client.close()
        elif self.telnet_client:
            self.telnet_client.close()
        else:
            print('Neither SSH nor Telnet connection is active.')