from network.paramiko_connection_CiscoDevices import create_device, AuthenticationException

testing_device = '{sensitive-ip}'


def verify_g(username: str, password: str):
    try:
        create_device(testing_device, username, password)
        return True
    except AuthenticationException:
        return False
