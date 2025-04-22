import tempfile
import yaml

import docker as dockerclient
from python_on_whales import docker
from pathlib import Path
from typing import Optional


from ...package.services.package_service import generate_deployment_package


def install_from_local(
    stack_name: str,
    packages_dir: Path,
    package_name: str,
    override_values_file: Optional[Path] = None,
    verbose: bool = False,
) -> None:
    package_path = packages_dir / package_name
    with tempfile.TemporaryDirectory() as temp_dir:
        destination = Path(temp_dir)
        generate_deployment_package(
            stack_name=stack_name,
            package_path=package_path,
            destination=destination,
            override_values_file=override_values_file,
            verbose=verbose,
        )

        docker_client = dockerclient.from_env()
        config_dir = destination / "config"
        if config_dir.exists():
            for directory in Path(config_dir).iterdir():
                if directory.is_dir():
                    config_files = list(directory.glob("*"))

                    if len(config_files) > 1:
                        raise ValueError(
                            f"Multiple files or folders found in config directory: '{directory}'. Expected only one file."
                        )

                    config_name = f"{stack_name}-{directory.name}"
                    for config_file in config_files:
                        if config_file.is_file():
                            filters = {"name": config_name}
                            if not docker_client.configs.list(filters=filters):
                                docker.config.create(config_name, config_file)
                        else:
                            raise ValueError(
                                f"Config file is not a file: {config_file}"
                            )

        with open(_get_stack_file(destination), "r") as f:
            data = yaml.safe_load(f)
            for net, _ in data.get("networks", {}).items():
                existing_net = docker_client.networks.list(filters={"name": net})
                if not existing_net:
                    docker_client.networks.create(
                        net, driver="overlay", attachable=True
                    )

        docker.stack.deploy(
            stack_name,
            compose_files=_get_stack_file(destination),
            prune=True,
            with_registry_auth=True,
        )


def _get_stack_file(stack_dir: Path) -> Path:
    """
    Get the stack file from the given directory. The stack file can be either
    'stack.yaml' or 'stack.yml'. If both files exist, raise an error.
    """
    stack_files = [stack_dir / "stack.yaml", stack_dir / "stack.yml"]
    existing_stack_files = [
        stack_file for stack_file in stack_files if stack_file.exists()
    ]

    if len(existing_stack_files) > 1:
        raise ValueError(
            "Both 'stack.yaml' and 'stack.yml' exist. Only one is expected."
        )
    elif not existing_stack_files:
        raise ValueError("No stack file found.")
    else:
        return existing_stack_files[0]
