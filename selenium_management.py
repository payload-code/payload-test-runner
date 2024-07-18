import subprocess
import psutil
import requests
import time
import signal
import os
from colorama import Fore

selenium_server_url = "https://github.com/SeleniumHQ/selenium/releases/download/selenium-4.6.0/selenium-server-4.6.0.jar"
selenium_server_file = "selenium-server-4.6.0.jar"


def download_selenium_server():
    if not os.path.exists(selenium_server_file):
        print(
            Fore.YELLOW + f"Downloading Selenium Server from {selenium_server_url}..."
        )
        response = requests.get(selenium_server_url)
        if response.status_code == 200:
            with open(selenium_server_file, "wb") as f:
                f.write(response.content)
            print(Fore.GREEN + "Selenium Server downloaded successfully.")
        else:
            print(Fore.RED + "Failed to download Selenium Server.")


def terminate_existing_selenium_processes():
    print(Fore.YELLOW + "Terminating existing Selenium processes...")
    for process in psutil.process_iter(["pid", "cmdline"]):
        cmdline = process.info.get("cmdline", [])
        if cmdline and ("java" in cmdline or "selenium" in cmdline):
            print(f"Terminating process {process.info['pid']} with cmdline {cmdline}")
            psutil.Process(process.info["pid"]).terminate()


def start_selenium_server(ip_address):
    print(Fore.GREEN + "Starting Selenium Server...")
    jar_file = selenium_server_file
    hub_command = f"java -jar {jar_file} standalone"
    node_command = f"java -jar {jar_file} node --hub http://{ip_address}:4444"

    terminate_existing_selenium_processes()

    print(Fore.GREEN + "Starting Selenium Hub...")
    hub_process = subprocess.Popen(
        hub_command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )

    time.sleep(5)

    if hub_process.poll() is not None:
        print(Fore.RED + "Failed to start Selenium Hub. Output:")
        print(hub_process.stdout.read().decode())
        return None, None

    print(Fore.GREEN + "Starting Selenium Node...")
    node_process = subprocess.Popen(
        node_command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )

    start_time = time.time()
    timeout = 30  # seconds

    while time.time() - start_time < timeout:
        hub_output = hub_process.stdout.readline().decode().strip()
        if hub_output:
            print(f"Hub Output: {hub_output}")

        node_output = node_process.stdout.readline().decode().strip()
        if node_output:
            print(f"Node Output: {node_output}")

        if hub_process.poll() is None and node_process.poll() is None:
            break

        time.sleep(1)

    if hub_process.poll() is not None or node_process.poll() is not None:
        print(Fore.RED + "Failed to start Selenium Node. Output:")
        if hub_process.poll() is not None:
            print(hub_process.stdout.read().decode())
        if node_process.poll() is not None:
            print(node_process.stdout.read().decode())
        return None, None

    print(Fore.GREEN + "Selenium processes started, checking status...")

    for process in psutil.process_iter(["pid", "cmdline"]):
        cmdline = process.info.get("cmdline", [])
        if cmdline and "java" in cmdline and jar_file in cmdline:
            print(
                f"Selenium process running: PID {process.info['pid']} with cmdline {cmdline}"
            )

    return hub_process, node_process
