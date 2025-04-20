import pynetbox
import serial
import serial.tools.list_ports
import time

def get_switch_commands():
    nb = pynetbox.api('NETBOX_URL', token='NETBOX_API_TOKEN')
    device = nb.dcim.devices.get(3) # Fill in device id
    if device:
        switch_commands = device.custom_fields.get('SwitchConfig')
        if switch_commands is not None:
            print(f"SwitchConfig: {switch_commands}")
            return switch_commands
        else:
            print("Custom field 'SwitchConfig' not found.")
    else:
        print("Device with ID 3 not found.")
    return None

def get_available_com_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"Found port: {port.device}")
        return port.device
    return None

def send_command(ser, command, wait_time=1):
    ser.write((command + '\n').encode())
    time.sleep(wait_time)
    response = ser.read(ser.in_waiting).decode()
    return response

def configure_switch(ser, commands):
    response = send_command(ser, '', wait_time=2)
    print(response)
    response = send_command(ser, 'no', wait_time=2)
    print(response)
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
            response = send_command(ser, full_command, wait_time=2)
        else:
            if command:
                response = send_command(ser, command, wait_time=2)
        print(response)
        i += 1
    return response

def reset_switch(ser):
    response = send_command(ser, 'erase startup-config', wait_time=5)
    print(response)

    # Hit enter to confirm erase
    response = send_command(ser, '', wait_time=5)
    print(response)
    
    response = send_command(ser, 'reload', wait_time=5)
    print(response)

    # Hit enter to confirm reload
    response = send_command(ser, '', wait_time=5)
    print(response)
    
    return response

def connect_to_switch_via_serial(com_port, commands):
    try:
        ser = serial.Serial(com_port, baudrate=9600, timeout=1)
        choice = input("Do you want to configure the switch or reset it? (configure/reset): ").strip().lower()
        if choice == 'configure':
            response = configure_switch(ser, commands)
        elif choice == 'reset':
            response = reset_switch(ser)
        else:
            print("Invalid choice. Exiting.")
            ser.close()
            return None
        ser.close()
        print(f"Output: {response}")
        return response
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Example usage
switch_commands = get_switch_commands()
if switch_commands:
    com_port = get_available_com_port()
    if com_port:
        connect_to_switch_via_serial(com_port, switch_commands)
    else:
        print("No available COM port found.")
else:
    print("Switch configuration not found.")