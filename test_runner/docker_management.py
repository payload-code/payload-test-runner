import subprocess
from colorama import Fore

docker_container_names = [
    "payload-webapp-payload-webapp-1",
    "payload-webapp-payload-scheduler-1",
    "payload-webapp-payload-worker-1",
]

exited_containers = []


def is_container_running(container_name):
    try:
        output = subprocess.check_output(
            f"docker inspect --format='{{{{.State.Running}}}}' {container_name}",
            shell=True,
        ).decode()
        return output.strip() == "true"
    except subprocess.CalledProcessError:
        return False


def restart_containers():
    print(Fore.GREEN + "Restarting containers...")
    for container_name in exited_containers:
        if not is_container_running(container_name):
            subprocess.run(f"docker start {container_name}", shell=True)
            print(f"Container {container_name} restarted.")
        else:
            print(f"Container {container_name} is already running.")
    print(Fore.GREEN + "Containers restarted successfully.")


def exit_containers():
    print(Fore.YELLOW + "Stopping existing containers...")
    for container_name in docker_container_names:
        if is_container_running(container_name):
            subprocess.run(f"docker stop {container_name}", shell=True)
            exited_containers.append(container_name)
            print(f"Container {container_name} stopped.")
        else:
            print(f"Container {container_name} is already stopped.")


def get_exited_containers():
    for container_name in docker_container_names:
        if not is_container_running(container_name):
            exited_containers.append(container_name)


def run_command_in_container(container_name, command):
    if is_container_running(container_name):
        try:
            print(Fore.CYAN + f"Running command in {container_name}: {command}")
            subprocess.run(f"docker exec {container_name} {command}", shell=True, check=True)
            print(Fore.GREEN + "Command executed successfully.")
        except subprocess.CalledProcessError as e:
            print(Fore.RED + f"Failed to execute command: {e}")
    else:
        print(Fore.RED + f"Container {container_name} is not running.")
