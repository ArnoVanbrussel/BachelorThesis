import pynetbox
import paramiko
import time

# Connect to NetBox with token authentication
nb = pynetbox.api('NETBOX_URL', token='NETBOX_TOKEN')

def get_switch_info(device_id):
    device = nb.dcim.devices.get(device_id)
    if device:
        switch_commands = device.custom_fields.get('SwitchConfig')
        primary_ip = device.primary_ip4.address.split('/')[0] if device.primary_ip4 else None
        if switch_commands is not None and primary_ip is not None:
            print(f"\nDevice {device_id} - IP: {primary_ip}")
            return {'id': device_id, 'ip': primary_ip, 'commands': switch_commands}
        else:
            print(f"\nDevice {device_id}: Missing 'SwitchConfig' or Primary IPv4.")
    else:
        print(f"\nDevice {device_id} not found.")
    return None

def send_command(ssh, command, wait_time=1):
    stdin, stdout, stderr = ssh.exec_command(command)
    time.sleep(wait_time)
    return stdout.read().decode()

def configure_switch(ssh, commands):
    command_list = commands.split('\n')
    i = 0
    while i < len(command_list):
        command = command_list[i].strip()
        if command.startswith('banner motd'):
            banner_command = [command]
            i += 1
            while i < len(command_list) and not command_list[i].strip().endswith('#'):
                banner_command.append(command_list[i])
                i += 1
            if i < len(command_list):
                banner_command.append(command_list[i])
            full_command = '\n'.join(banner_command)
            response = send_command(ssh, full_command, wait_time=2)
        else:
            if command:
                response = send_command(ssh, command, wait_time=2)
        print(response)
        i += 1
    response = send_command(ssh, 'sho run', wait_time=2)
    print(response)
    return response

def reset_switch(ssh):
    print(send_command(ssh, 'erase startup-config', wait_time=5))
    print(send_command(ssh, '', wait_time=5))  # Confirm erase
    print(send_command(ssh, 'reload', wait_time=5))
    print(send_command(ssh, '', wait_time=5))  # Confirm reload

def connect_and_act(switch, username, password, action):
    try:
        print(f"\nConnecting to {switch['ip']} (Device {switch['id']})...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(switch['ip'], username=username, password=password)

        if action == 'configure':
            configure_switch(ssh, switch['commands'])
        elif action == 'reset':
            reset_switch(ssh)
        ssh.close()
        print(f"Done with device {switch['id']}")
    except paramiko.AuthenticationException:
        print("Authentication failed.")
    except paramiko.SSHException as e:
        print(f"SSH error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def main():
    ids_input = input("Enter device IDs (separated by semicolons): ")
    device_ids = [id.strip() for id in ids_input.split(';') if id.strip().isdigit()]
    
    if not device_ids:
        print("No valid device IDs provided.")
        return

    switches = []
    for device_id in device_ids:
        info = get_switch_info(int(device_id))
        if info:
            switches.append(info)

    if not switches:
        print("No valid switch configurations found.")
        return

    username = input("Enter SSH username: ")
    password = input("Enter SSH password: ")
    action = input("Do you want to configure or reset the switches? (configure/reset): ").strip().lower()

    if action not in ('configure', 'reset'):
        print("Invalid action.")
        return

    for switch in switches:
        connect_and_act(switch, username, password, action)

if __name__ == "__main__":
    main()