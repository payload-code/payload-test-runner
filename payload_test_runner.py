import subprocess
import psutil
import os
import signal
import time
import inquirer
import pickle
import requests
import json
from colorama import Fore, init as colorama_init
from art import text2art

colorama_init(autoreset=True)

config_file = "config.json"
docker_compose_dir = None
docker_process = None
cache_file = "test_cache.pkl"
selenium_server_url = "https://github.com/SeleniumHQ/selenium/releases/download/selenium-4.6.0/selenium-server-4.6.0.jar"
selenium_server_file = "selenium-server-4.6.0.jar"


def print_payload_art():
    art = text2art("PAYLOAD", font="isometric1")
    print(Fore.CYAN + art)


def load_config():
    global docker_compose_dir
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
            docker_compose_dir = config.get("docker_compose_dir")


def save_config():
    config = {"docker_compose_dir": docker_compose_dir}
    with open(config_file, "w") as f:
        json.dump(config, f)


def setup():
    global docker_compose_dir

    load_config()

    if docker_compose_dir:
        print(Fore.GREEN + f"Using existing configuration: {docker_compose_dir}")
        return

    print(Fore.GREEN + "Welcome to Payload WebApp Test Automation Setup!")
    docker_compose_dir = input(
        "Enter the absolute path to your payload-webapp docker-compose directory: "
    ).strip()
    if not os.path.isdir(docker_compose_dir):
        print(
            Fore.RED + f"Directory '{docker_compose_dir}' does not exist or is invalid."
        )
        setup()
        return
    save_config()
    print(Fore.GREEN + "Setup completed successfully!")


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


def get_ip_address():
    try:
        output = subprocess.check_output("ipconfig getifaddr en0", shell=True).decode()
        return output.strip()
    except subprocess.CalledProcessError:
        return None


def start_selenium_server(ip_address):
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


def run_docker_test(ip_address, test_choice):
    global docker_process
    test_argument = (
        "" if test_choice.lower() == "all" else f"-k {test_choice} --rebuild-db"
    )

    current_dir = os.getcwd()
    if docker_compose_dir not in current_dir:
        os.chdir(docker_compose_dir)

    command = f"DOCKER_HOST_IP={ip_address} docker-compose run --service-ports payload-webapp pdm run python -m gevent.monkey --module pytest tests -vv {test_argument}"
    docker_process = subprocess.Popen(command, shell=True)
    docker_process.wait()
    update_test_cache(test_choice)


def update_test_cache(test_choice):
    test_cache = load_test_cache()
    if test_choice not in test_cache:
        test_cache.append(test_choice)
    with open(cache_file, "wb") as f:
        pickle.dump(test_cache, f)


def load_test_cache():
    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            return pickle.load(f)
    return []


def run_docker_tests(ip_address, previous_test_choice=None):
    test_cache = load_test_cache()
    while True:
        choices = [
            "Run all tests",
            "Run specific test",
            "Rerun previous test",
            "View test logs",
            "Exit",
        ]
        if test_cache:
            choices.insert(3, "View test history")

        questions = [
            inquirer.List(
                "choice",
                message="What would you like to do?",
                choices=choices,
                default="Run all tests",
            ),
        ]
        answer = inquirer.prompt(questions)["choice"]

        if answer == "Run all tests":
            run_docker_test(ip_address, "all")
            previous_test_choice = "all"
        elif answer == "Run specific test":
            test_name = input("Enter the test name: ")
            run_docker_test(ip_address, test_name)
            previous_test_choice = test_name
        elif answer == "Rerun previous test" and previous_test_choice:
            run_docker_test(ip_address, previous_test_choice)
        elif answer == "View test logs":
            with open("selenium_log.txt", "r") as log_file:
                print(log_file.read())
        elif answer == "View test history":
            print("Test history:")
            for test in test_cache:
                print(f" - {test}")
        elif answer == "Exit":
            break
        else:
            print(Fore.RED + "No previous test to rerun.")


def send_sigint_to_docker_process():
    if docker_process:
        docker_process.send_signal(signal.SIGINT)


def cleanup(hub_process, node_process):
    send_sigint_to_docker_process()
    if hub_process:
        hub_process.terminate()
    if node_process:
        node_process.terminate()


if __name__ == "__main__":
    setup()
    download_selenium_server()

    hub_process, node_process = None, None
    try:
        print_payload_art()
        ip_address = get_ip_address()
        if ip_address:
            print(f"IP Address: {ip_address}")
            print(Fore.GREEN + "Starting Selenium Server...")
            hub_process, node_process = start_selenium_server(ip_address)
            if hub_process and node_process:
                print(Fore.GREEN + "Running Docker tests...")
                run_docker_tests(ip_address)
        else:
            print(Fore.RED + "Failed to find IP address.")
    finally:
        cleanup(hub_process, node_process)
