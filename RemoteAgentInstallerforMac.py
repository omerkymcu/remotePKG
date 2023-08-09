#!/usr/bin/env python

import os
import sys
import subprocess
import ipaddress

def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    pkg_folder = os.path.join(dir_path, 'pkg_folder')

    agent = 0

    if not os.path.exists(pkg_folder):
        print("No 'pkg_folder' found. Please make sure the folder contains the desired pkg files.")
        sys.exit(2)

    print("The below entered credential will be used to install agent in remote machine(s) specified in the IP range.")

    username = input("Enter Username: ")
    password = input("Enter Password: ")
    ip_range = input("Enter IP range (e.g., 192.168.1.1/24): ")

    try:
        network = ipaddress.ip_network(ip_range)
    except ValueError:
        print("Invalid IP range format. Exiting...")
        sys.exit(2)

    print("Available pkg files:")
    pkg_files = [f for f in os.listdir(pkg_folder) if f.endswith(".pkg")]
    for i, pkg_file in enumerate(pkg_files):
        print(f"{i+1}. {pkg_file}")

    pkg_number = int(input("Enter the number of the pkg file you want to install: "))
    selected_pkg = pkg_files[pkg_number - 1]

    print("----------------------------------------------------------------------")
    for ip_address in network.hosts():
        sysName = str(ip_address)

        print(f"Trying to copy {selected_pkg} to {sysName} using {username} credentials")

        subprocess.run(['sshpass', '-p', password, 'scp', os.path.join(pkg_folder, selected_pkg), f"{username}@{sysName}:"], check=True)

        print("Successfully copied file. DC Agent installation initiated")

        try:
            subprocess.run(['sshpass', '-p', password, 'ssh', f"{username}@{sysName}", 'chmod', '755', selected_pkg], check=True)
        except subprocess.CalledProcessError:
            print(f"DC Agent chmod failed for {sysName}.")
        else:
            print(f"DC Agent chmod success for {sysName}.")

        installer_command = ["installer", "-pkg", selected_pkg, "-target", "/"]
        if username == "root":
            installer_command.insert(0, "ssh")
            installer_command.insert(1, f"{username}@{sysName}")
        else:
            print("Script will prompt for Password. Not need to enter password.")
            installer_command = [
                "sshpass", "-p", password, "ssh", f"{username}@{sysName}",
                f'echo "{password}" | sudo -S ' + ' '.join(installer_command)
            ]

        try:
            subprocess.run(installer_command, check=True)
        except subprocess.CalledProcessError:
            print(f"DC Agent installation failed for {sysName}.")
        else:
            print(f"DC Agent installation success for {sysName}.")

        subprocess.run(['sshpass', '-p', password, 'ssh', f"{username}@{sysName}", 'rm', '-f', selected_pkg], check=True)

        print(f"Temporary file removed from {sysName}")
        print("----------------------------------------------------------------------")

    sys.exit(0)

if __name__ == "__main__":
    main()
