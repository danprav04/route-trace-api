from tracer.routetrace.CiscoDeviceConnection import Session as SessionSSH

def get_vlans(device: SessionSSH):
    return device.execute_command('show vlan')
