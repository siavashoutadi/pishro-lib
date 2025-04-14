import json
import os
import shutil
import tempfile
import docker
import time
from datetime import datetime, timedelta

from pishro_lib.git.models.repository import GitRepository
from typing import List
from docker.types import SecretReference

# Secret name prefix for repository configurations
REPO_SECRET_PREFIX = "pishro_repo_"
docker_client = docker.from_env()
try:
    info = docker_client.info()
    if "Swarm" not in info or not info["Swarm"].get("ControlAvailable"):
        raise RuntimeError(
            "Docker is not in swarm mode. Please initialize swarm mode first."
        )
except Exception as e:
    raise RuntimeError(f"Failed to connect to Docker daemon: {str(e)}")


def _get_docker_secret_name(name: str) -> str:
    """
    Generate a docker secret name for the repository based on its name.

    Args:
        name (str): The name of the repository.

    Returns:
        str: The formatted secret name.

    Example:
        secret_name = _get_docker_secret_name("example-repo")
        print(secret_name)  # Output: pishro_repo_example-repo
    """
    return f"{REPO_SECRET_PREFIX}{name}"


def add_repository(repo: GitRepository) -> None:
    """
    Add a new repository to the system.

    Args:
        repo (GitRepository): The repository object to be added.

    Returns:
        None

    Example:
        repo = GitRepository(name="example-repo", url="https://github.com/example-org/example-repo.git")
        add_repository(repo)
    """
    remove_repository(repo.name)

    repo_data = repo.model_dump()
    if repo.token:
        repo_data["token"] = repo.token.get_secret_value()
    secret_data = json.dumps(repo_data).encode("utf-8")
    docker_client.secrets.create(
        name=_get_docker_secret_name(repo.name),
        data=secret_data,
        labels=repo.model_dump(exclude={"username", "token"}),
    )


def remove_repository(name: str) -> None:
    """
    Remove a repository from the system by its name.

    Args:
        name (str): The name of the repository to be removed.

    Returns:
        None

    Example:
        remove_repository("example-repo")
    """
    secret_name = _get_docker_secret_name(name)
    try:
        existing_secret = docker_client.secrets.get(secret_name)
        existing_secret.remove()
    except docker.errors.NotFound:
        pass


def list_repositories() -> List[GitRepository]:
    """
    List all repositories currently in the system.

    Returns:
        List[GitRepository]: A list of all repository objects.

    Example:
        repositories = list_repositories()
        for repo in repositories:
            print(repo.name, repo.url)
    """
    secrets = docker_client.secrets.list(filters={"name": REPO_SECRET_PREFIX})
    repositories: list[GitRepository] = []
    for secret in secrets:
        secret_data = secret.attrs["Spec"]["Labels"]
        repositories.append(GitRepository(**secret_data))
    return repositories


def get_repository(name: str) -> GitRepository:
    """
    Get details of a specific repository by its name.

    Args:
        name (str): The name of the repository to retrieve.

    Returns:
        GitRepository: The repository object with the specified name.

    Example:
        repo = get_repository("example-repo")
        print(repo.name, repo.url)
    """
    secret_name = _get_docker_secret_name(name)
    try:
        secret = docker_client.secrets.get(secret_name)
    except docker.errors.NotFound:
        raise Exception(f"Repository '{name}' not found.")

    secret_data = secret.attrs["Spec"]["Labels"]

    temp_dir = tempfile.mkdtemp()
    temp_file_name = "s"
    temp_file = os.path.join(temp_dir, temp_file_name)

    secret_reference = SecretReference(
        secret_id=secret.id,
        secret_name=secret_name,
        filename=f"/run/secrets/{secret_name}",
    )

    service = docker_client.services.create(
        image="alpine:latest",
        command=["cp", f"/run/secrets/{secret_name}", f"/host-mount/{temp_file_name}"],
        secrets=[secret_reference],
        mode=docker.types.ServiceMode("replicated-job"),
        log_driver="json-file",
        mounts=[docker.types.Mount(target="/host-mount", source=temp_dir, type="bind")],
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
                    if not secret_value:
                        raise Exception(
                            f"Failed to retrieve secret value for '{name}'."
                        )
                    secret_data.update(json.loads(secret_value))
                    break
                elif task["Status"]["State"] in ["failed", "rejected"]:
                    raise Exception(f"Service task failed: {task['Status']['Err']}")
            time.sleep(1)
        else:
            raise Exception("Timeout waiting for service to complete")
    finally:
        service.remove()
        shutil.rmtree(temp_dir)

    return GitRepository(**secret_data)
