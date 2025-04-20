import pynetbox
import paramiko
import time

def get_switch_commands():
    # Connect to NetBox with token authentication
    nb = pynetbox.api('NETBOX_URL', token='NETBOX_TOKEN')

    # Get the device (switch) by ID
    device = nb.dcim.devices.get(3)  # Adjust with the correct device ID

    # Check if the device was found
    if device:
        # Get the custom field 'SwitchConfig'
        switch_commands = device.custom_fields.get('SwitchConfig')
        primary_ip = device.primary_ip4.address.split('/')[0] if device.primary_ip4 else None
        if switch_commands is not None and primary_ip is not None:
            print(f"SwitchConfig: {switch_commands}")
            print(f"Primary IPv4: {primary_ip}")
            return switch_commands, primary_ip
        else:
            print("Custom field 'SwitchConfig' or Primary IPv4 address not found.")
    else:
        print("Device with ID 3 not found.")
    return None, None

def send_command(ssh, command, wait_time=1):
    stdin, stdout, stderr = ssh.exec_command(command)
    time.sleep(wait_time)
    response = stdout.read().decode()
    return response

def configure_switch(ssh, commands):
    # Commenting out the configuration commands for now
    # command_list = commands.split('\n')
    # i = 0
    # while i < len(command_list):
    #     command = command_list[i].strip()
    #     if command.startswith('banner motd'):
    #         banner_command = [command]
    #         i += 1
    #         while i < len(command_list) and not command_list[i].strip().endswith('#'):
    #             banner_command.append(command_list[i])
    #             i += 1
    #         if i < len(command_list):
    #             banner_command.append(command_list[i])
    #         full_command = '\n'.join(banner_command)
    #         response = send_command(ssh, full_command, wait_time=2)
    #     else:
    #         if command:
    #             response = send_command(ssh, command, wait_time=2)
    #     print(response)
    #     i += 1
    response = send_command(ssh, 'sho run', wait_time=2)
    print(response)
    return response

def reset_switch(ssh):
    response = send_command(ssh, 'erase startup-config', wait_time=5)
    print(response)

    # Hit enter to confirm erase
    response = send_command(ssh, '', wait_time=5)
    print(response)
    
    response = send_command(ssh, 'reload', wait_time=5)
    print(response)

    # Hit enter to confirm reload
    response = send_command(ssh, '', wait_time=5)
    print(response)
    
    return response

def connect_to_switch_via_ssh(ip_address, commands):
    try:
        username = input("Enter the username: ")
        password = input("Enter the password: ")
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip_address, username=username, password=password)
        choice = input("Do you want to configure the switch or reset it? (configure/reset): ").strip().lower()
        if choice == 'configure':
            response = configure_switch(ssh, commands)
        elif choice == 'reset':
            response = reset_switch(ssh)
        else:
            print("Invalid choice. Exiting.")
            ssh.close()
            return None
        ssh.close()
        print(f"Output: {response}")
        return response
    except paramiko.AuthenticationException:
        print("Authentication failed, please verify your credentials.")
        return None
    except paramiko.SSHException as sshException:
        print(f"Unable to establish SSH connection: {sshException}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Example usage
switch_commands, primary_ip = get_switch_commands()
if switch_commands and primary_ip:
    connect_to_switch_via_ssh(primary_ip, switch_commands)
else:
    print("Switch configuration or Primary IPv4 address not found.")