import os
import sys
import argparse
from colorama import Fore

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
sys.path.append(project_root)

from initial_setup import setup
from selenium_management import (
    download_selenium_server,
    terminate_existing_selenium_processes,
    start_selenium_server,
)
from docker_management import exit_containers, restart_containers
from test_management import run_docker_tests, get_ip_address, print_payload_art, cleanup, run_docker_test
from config import CONFIG_FILE as config_file

def main():
    print("Starting Payload Test Runner...")

    parser = argparse.ArgumentParser(description='Payload Test Runner')
    parser.add_argument('test_name', nargs='?', help='The name of the test to run')
    args = parser.parse_args()

    if args.test_name:
        run_specific_test(args.test_name)
    else:
        run_gui_interface()

def run_specific_test(test_name):
    setup()
    download_selenium_server()

    hub_process, node_process = None, None
    try:
        print_payload_art()
        ip_address = get_ip_address()
        if ip_address:
            print(f"IP Address: {ip_address}")
            selenium_server = start_selenium_server()
            exit_containers()
            if selenium_server:
                print(Fore.GREEN + f"Running Docker test '{test_name}'...")
                run_docker_test(ip_address, test_name)
        else:
            print(Fore.RED + "Failed to find IP address.")
    finally:
        cleanup(selenium_server)

def run_gui_interface():
    setup()
    download_selenium_server()

    hub_process, node_process = None, None
    try:
        print_payload_art()
        ip_address = get_ip_address()
        if ip_address:
            print(f"IP Address: {ip_address}")
            selenium_server = start_selenium_server()
            exit_containers()
            if selenium_server:
                print(Fore.GREEN + "Running Docker tests...")
                run_docker_tests(ip_address)
        else:
            print(Fore.RED + "Failed to find IP address.")
    finally:
        cleanup(selenium_server)

if __name__ == "__main__":
    main()
