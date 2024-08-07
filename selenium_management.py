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


def start_selenium_server():
    print(Fore.GREEN + "Starting Selenium Server...")
    jar_file = selenium_server_file
    command = f"java -jar {jar_file} standalone"

    terminate_existing_selenium_processes()

    print(Fore.GREEN + "Starting Selenium...")
    process = subprocess.Popen(
        command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )


    start_time = time.time()
    timeout = 30  # seconds

    while time.time() - start_time < timeout:
        hub_output = process.stdout.readline().decode().strip()
        if hub_output:
            print(f"Hub Output: {hub_output}")

        if process.poll() is None:
            break

        time.sleep(1)

    if process.poll() is not None:
        print(Fore.RED + "Failed to start Selenium. Output:")
        if process.poll() is not None:
            print(process.stdout.read().decode())
        return None, None

    print(Fore.GREEN + "Selenium process started, checking status...")

    for process in psutil.process_iter(["pid", "cmdline"]):
        cmdline = process.info.get("cmdline", [])
        if cmdline and "java" in cmdline and jar_file in cmdline:
            print(
                f"Selenium process running: PID {process.info['pid']} with cmdline {cmdline}"
            )

    return process
