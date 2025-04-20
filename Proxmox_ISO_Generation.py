import pynetbox
import paramiko
import toml

def get_device_info_from_netbox(device_name):
    # Connect to NetBox with token authentication
    nb = pynetbox.api('https://xbrq8986.cloud.netboxapp.com/', token='#7xuQlP#DFg7Mq)#hqf8(o2KSCj9pQvuGGcGXjze')

    # Search for the device by name
    device = nb.dcim.devices.get(name=device_name)

    if device:
        # Extract custom fields
        fqdn = device.custom_fields.get('fqdn')
        disk_list = device.custom_fields.get('disk_list')
        raid = device.custom_fields.get('raid')
        filesystem = device.custom_fields.get('filesystem')
        return device, fqdn, disk_list, raid, filesystem
    else:
        print(f"Device '{device_name}' not found in NetBox.")
        return None, None, None

def create_answer_file(device_name, fqdn, disk_list, root_password, filesystem, raid):
    if isinstance(disk_list, str):
        disk_list = eval(disk_list)
    disk_list = [disk.strip() for disk in disk_list if disk.strip()]

    toml_string = f"""
[global]
keyboard = "en-us"
country = "fr"
fqdn = "{fqdn}"
mailto = "mail@no.com"
timezone = "Europe/Brussels"
root_password = "{root_password}"

[network]
source = "from-dhcp"

[disk-setup]
filesystem = "{filesystem}"
disk_list = {disk_list}
{filesystem}.raid = "{raid}"
"""

    file_name = f"{device_name}_answer.toml"
    with open(file_name, "w") as file:
        file.write(toml_string.strip())

    print(f"{file_name} file created successfully.")


def upload_and_execute_on_remote(device_name):
    # SSH connection details
    ssh_ip = "192.168.0.21"
    ssh_user = "root"
    ssh_password = "12345678"
    remote_path = f"/home/answer/{device_name}_answer.toml"  # Include device name in the answer file name
    iso_remote_path = f"/var/lib/vz/template/iso/{device_name}_proxmox-ve_8.3-1-auto-from-iso.iso"  # Include device name in the ISO file name
    iso_local_path = f"D:/ISO's/{device_name}_proxmox-ve_8.3-1-auto-from-iso.iso"  # Save ISO locally with device name

    try:
        # Establish SSH connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_ip, username=ssh_user, password=ssh_password)

        # Create the /home/answer directory
        ssh.exec_command("mkdir -p /home/answer")

        # Upload the answer.toml file
        sftp = ssh.open_sftp()
        sftp.put(f"{device_name}_answer.toml", remote_path)
        sftp.close()
        print(f"{device_name}_answer.toml uploaded successfully.")

        # Execute the Proxmox command
        command = f"proxmox-auto-install-assistant prepare-iso /var/lib/vz/template/iso/proxmox-ve_8.3-1.iso --fetch-from iso --answer-file {remote_path} --output {iso_remote_path}"
        stdin, stdout, stderr = ssh.exec_command(command)
        print(stdout.read().decode())
        print(stderr.read().decode())

        # Download the generated ISO file
        sftp = ssh.open_sftp()
        print(f"Downloading ISO from {iso_remote_path} to {iso_local_path}...")
        sftp.get(iso_remote_path, iso_local_path)
        sftp.close()
        print("ISO file downloaded successfully.")

        # Close the SSH connection
        ssh.close()
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    # Step 1: Ask the user for a list of device names
    device_names = input("Enter the names of the devices in NetBox (separated by a semicolon ';'): ").strip().split(";")

    # Step 2: Ask the user for the root password (used for all devices)
    root_password = input("Enter the root password for all devices: ")

    # Step 3: Process each device
    for device_name in device_names:
        device_name = device_name.strip()  # Remove any extra whitespace
        if not device_name:
            continue  # Skip empty device names

        # Step 4: Get the device info from NetBox
        device, fqdn, disk_list, raid, filesystem = get_device_info_from_netbox(device_name)

        if device:
            # Step 5: Print the device info and ask for confirmation
            print(f"Device Info:\nName: {device.name}\nFQDN: {fqdn}\nDisk List: {disk_list}, \nRAID: {raid}, \nFilesystem: {filesystem}")
            confirm = input(f"Is this the correct device for '{device_name}'? (yes/no): ").strip().lower()

            if confirm == "yes":
                print(fqdn, disk_list, root_password, filesystem, raid)

                # Step 6: Create the answer.toml file
                create_answer_file(device_name, fqdn, disk_list, root_password, filesystem, raid)

                # Step 7: Upload the file and execute the command on the remote server
                upload_and_execute_on_remote(device_name)
            else:
                print(f"Skipping device '{device_name}'.")
        else:
            print(f"Device '{device_name}' not found in NetBox. Skipping.")

if __name__ == "__main__":
    main()