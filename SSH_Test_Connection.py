import paramiko
import pynetbox

def get_switch_config():
    nb = pynetbox.api('NETBOX_URL', token='NETBOX_API_TOKEN')

    device = nb.dcim.devices.get(3)  # Adjust with the correct device ID

    if device:
        switch_config = device.custom_fields.get('SwitchConfigJson') # Adjust with correct custom field name
        if switch_config is not None:
            print(f"SwitchConfigJson: {switch_config}")
            return switch_config
        else:
            print("Custom field 'SwitchConfigJson' not found.")
    else:
        print("Device with ID 3 not found.")
    return None

def connect_to_switch(hostname, username, password, command):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, password=password)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        ssh.close()
        if error:
            print(f"Error: {error}")
        else:
            print(f"Output: {output}")
        return output
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Example usage
switch_config = get_switch_config()
if switch_config:
    hostname = switch_config.get("ip")
    if hostname:
        username = input("Enter username: ")
        password = input("Enter password: ")
        command = "show running-config"
        connect_to_switch(hostname, username, password, command)
    else:
        print("IP address not found in SwitchConfigJson.")