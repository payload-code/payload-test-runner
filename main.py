from initial_setup import setup
from selenium_management import (
    download_selenium_server,
    terminate_existing_selenium_processes,
    start_selenium_server,
)
from docker_management import exit_containers, restart_containers
from test_management import run_docker_tests, get_ip_address, print_payload_art, cleanup
from colorama import Fore
import os


def main():
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
