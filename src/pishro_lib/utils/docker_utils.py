import os
from pathlib import Path
import tempfile
import secrets
import json
import time
import docker
import shutil


from datetime import datetime, timedelta
from docker.models.secrets import Secret
from docker.models.services import Service
from docker.types import SecretReference, ServiceMode, Mount


docker_client = docker.from_env()


class DockerSecretNotFoundError(Exception):
    pass


class DockerValueNotFoundError(Exception):
    pass


class DockerServiceTaskFailed(Exception):
    pass


class DockerServiceCompletionTimeoutError(Exception):
    pass


class DockerSecretFailedException(Exception):
    pass


def get_docker_secret(secret_name: str) -> Secret:
    try:
        secret = docker_client.secrets.get(secret_name)
        return secret
    except docker.errors.NotFound:
        raise DockerSecretNotFoundError(f"Secret '{secret_name}' not found in Docker.")


def get_secret_value(secret_name: str) -> str:
    docker_secret = get_docker_secret(secret_name)

    if docker_secret:
        secret_labels = docker_secret.attrs["Spec"]["Labels"]

    temp_dir = tempfile.mkdtemp()
    temp_file_name = "s"
    temp_file = os.path.join(temp_dir, temp_file_name)

    secret_reference = SecretReference(
        secret_id=docker_secret.id,
        secret_name=secret_name,
        filename=f"/run/secrets/{secret_name}",
    )

    service: Service = docker_client.services.create(
        image="alpine:latest",
        command=["cp", f"/run/secrets/{secret_name}", f"/host-mount/{temp_file_name}"],
        secrets=[secret_reference],
        mode=ServiceMode("replicated-job"),
        log_driver="json-file",
        mounts=[Mount(target="/host-mount", source=temp_dir, type="bind")],
    )

    start_time = datetime.now()
    timeout = timedelta(seconds=3)
    try:
        while datetime.now() - start_time < timeout:
            service.reload()
            tasks = service.tasks()
            if tasks:
                task = tasks[0]
                if task["Status"]["State"] == "complete":
                    with open(temp_file, "r") as f:
                        secret_value = f.read().strip()
                        return secret_value
                    if not secret_value:
                        raise DockerValueNotFoundError(
                            f"Failed to retrieve secret value for '{secret_name}'."
                        )
                    secret_labels.update(json.loads(secret_value))
                    break
                elif task["Status"]["State"] in ["failed", "rejected"]:
                    raise DockerServiceTaskFailed(
                        f"Service task failed: {task['Status']['Err']}"
                    )
            time.sleep(1)
        else:
            raise DockerServiceCompletionTimeoutError(
                "Timeout waiting for service to complete"
            )
    finally:
        service.remove()
        shutil.rmtree(temp_dir)


def create_docker_secret(secret_name: str, secret_value: str) -> None:
    try:
        docker_client.secrets.create(
            name=secret_name,
            data=secret_value.encode("utf-8"),
        )
    except docker.errors.APIError as e:
        raise DockerSecretFailedException(
            f"Failed to create secret '{secret_name}': {e}"
        )


def generate_random_docker_secret(secret_name: str, secret_lenght: int = 32) -> str:
    try:
        return get_secret_value(secret_name)
    except DockerSecretNotFoundError:
        secret_value = secrets.token_hex(secret_lenght)
        create_docker_secret(secret_name=secret_name, secret_value=secret_value)
        return secret_value


def create_secret_from_env(secret_name: str, env_name: str) -> str:
    try:
        return get_secret_value(secret_name)
    except DockerSecretNotFoundError:
        secret_value = os.environ[env_name]
        if secret_value is None:
            raise DockerValueNotFoundError(
                f"Environment variable '{env_name}' not found."
            )
        create_docker_secret(secret_name, secret_value)
        return secret_value


def create_secret_from_file(secret_name: str, env_file_path: Path) -> str:
    try:
        return get_secret_value(secret_name)
    except DockerSecretNotFoundError:
        if not env_file_path.exists():
            raise FileNotFoundError(f"Environment file '{env_file_path}' not found.")

        with open(env_file_path, "r") as env_file:
            secret_value = env_file.read().strip()

        if not secret_value:
            raise DockerValueNotFoundError(
                f"There is no value in the environment file '{env_file_path}'."
            )

        create_docker_secret(secret_name, secret_value)
        return secret_value
