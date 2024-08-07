import os
import json
import subprocess
from colorama import Fore

from config import CONFIG_FILE as config_file

docker_compose_dir = None

def load_config():
    """Load configuration from a JSON file."""
    global docker_compose_dir
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
            docker_compose_dir = config.get("docker_compose_dir")

def save_config():
    """Save configuration to a JSON file."""
    config = {"docker_compose_dir": docker_compose_dir}
    with open(config_file, "w") as f:
        json.dump(config, f)

def setup():
    """Initial setup to ensure all configurations are set."""
    load_config()

    if not docker_compose_dir:
        print(Fore.GREEN + "Welcome to Payload WebApp Test Automation Setup!")
        configure_docker_compose_dir()

def configure_docker_compose_dir():
    """Prompt the user to configure the docker compose directory."""
    global docker_compose_dir
    while True:
        docker_compose_dir = input(
            "Enter the absolute path to your payload-webapp docker-compose directory: "
        ).strip()
        if not os.path.isdir(docker_compose_dir):
            print(
                Fore.RED + f"Directory '{docker_compose_dir}' does not exist or is invalid. Please try again."
            )
        else:
            break
    save_config()
    print(Fore.GREEN + "Setup completed successfully!")

def get_docker_compose_dir():
    """Get the docker compose directory from the configuration."""
    load_config()
    return docker_compose_dir

def check_java_exists():
    """Ensure that Java exists on the host system."""
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("Java has been detected.")
            print(result.stderr.splitlines()[0])
            return True
        else:
            print("Java is not installed.")
            return False
    except FileNotFoundError:
        print("Java is not installed.")
        return False
