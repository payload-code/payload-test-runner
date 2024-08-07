import os
import subprocess
import platform
import inquirer
import pickle
from art import text2art
from colorama import Fore
from docker_management import restart_containers, get_exited_containers
from initial_setup import get_docker_compose_dir
from config import DOCKER_COMPOSE_CMD

cache_file = "test_cache.pkl"


def print_payload_art():
    art = text2art("PAYLOAD", font="random")
    print(Fore.CYAN + art)


def run_docker_tests(ip_address, previous_test_choice=None):
    test_cache = load_test_cache()
    while True:
        choices = [
            "Run all tests",
            "Run specific test",
            "Rerun previous test",
            "Exit",
        ]

        if test_cache:
            choices.insert(3, "View test history")
        if get_exited_containers():
            choices.append("Exit and restart exited containers")

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
        elif answer == "View test history":
            print("Test history:")
            for test in test_cache:
                print(f" - {test}")
        elif answer == "Exit and restart exited containers":
            restart_containers()
            break
        elif answer == "Exit":
            break
        else:
            print(Fore.RED + "Invalid choice. Please select again.")

        test_cache = load_test_cache()


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


def run_docker_test(ip_address, test_choice):
    global docker_process
    test_argument = (
        "" if test_choice.lower() == "all" else f"-k {test_choice} --rebuild-db"
    )

    current_dir = os.path.abspath(os.getcwd())
    docker_compose_abs = os.path.abspath(get_docker_compose_dir())

    if current_dir != docker_compose_abs:
        print(Fore.YELLOW + "Changing directory to docker-compose directory")
        os.chdir(docker_compose_abs)

    command = f"DOCKER_HOST_IP={ip_address} {DOCKER_COMPOSE_CMD} run --service-ports payload-webapp pdm run python -m gevent.monkey --module pytest tests -vv {test_argument}"
    docker_process = subprocess.Popen(command, shell=True)
    docker_process.wait()

    os.chdir(current_dir)

    update_test_cache(test_choice)


def get_ip_address():
    system = platform.system()
    if system == "Darwin":  # macOS
        try:
            output = (
                subprocess.check_output("ipconfig getifaddr en0", shell=True)
                .decode()
                .strip()
            )
            return output
        except subprocess.CalledProcessError:
            return None
    elif system == "Windows":
        try:
            output = (
                subprocess.check_output("ipconfig | findstr IPv4", shell=True)
                .decode()
                .strip()
            )
            ip_address = output.split(":")[-1].strip()
            return ip_address
        except subprocess.CalledProcessError:
            return None
    elif system == "Linux":
        return '172.17.0.1'
    else:
        print(f"Unsupported operating system: {system}")
        return None


def cleanup(hub_process):
    if hub_process:
        hub_process.terminate()
