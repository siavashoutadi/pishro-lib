import shutil

from pathlib import Path
from typing import Dict

from ...git.services.repository_service import clone_repository
from ..models.application import Deploy, Service
from ...package.services.package_service import download_package
from ...installation.services.installation_service import install_from_local
from ...utils.docker_utils import wait_for_stack_services


def download_application(
    repository_name: str,
    application_name: str,
    version: str = "",
    destination: str = "./pishro-catalog",
) -> None:
    """
    Downloads a pishro application from the pishro repository.

    Args:
        repository_name (str): The name of the pishro repository.
        package_name (str): The name of the pishro application to download.
        version (str): The version of the pishro application to download.
        destination (str): The destination directory where the pishro application will be downloaded.
    """

    branch = f"{application_name}-{version}"
    if not version:
        branch = "main"

    with clone_repository(repository_name, branch) as repo_path:
        source_dir = Path(repo_path) / "applications" / application_name

        if not source_dir.exists():
            raise ValueError(
                f"Package '{application_name}' not found in repository '{repository_name}'"
            )
        destination_dir = Path(destination) / "applications" / application_name
        shutil.copytree(source_dir, destination_dir, dirs_exist_ok=True)

    deploy_yaml = destination_dir / "deploy.yaml"
    deploy_config = Deploy.from_yaml(deploy_yaml)

    package_destination = Path(destination) / "packages"
    for service_name, service in deploy_config.services.items():
        download_package(
            repository_name=repository_name,
            package_name=service.package,
            destination=package_destination,
            sub_directory="packages",
        )


def install_application(
    application_name: str,
    stack_name: str,
    environment: str = "production",
    catalog_path: Path = Path("./pishro-catalog"),
    verbose: bool = False,
) -> None:
    """
    Install an application using the provided parameters.
    Args:
        application_name (str): The name of the application to install.
        environment (str): The environment to install the application in.
        packages_path (Path): Path to the packages directory.
        verbose (bool): Enable verbose output.
    """

    _validate_application_structure(catalog_path, application_name, environment)

    deploy_config = _get_deploy_config(
        catalog_path=catalog_path, application_name=application_name
    )

    _deploy_services(
        deploy_config=deploy_config,
        catalog_path=catalog_path,
        application_name=application_name,
        stack_name=stack_name,
        environment=environment,
        verbose=verbose,
    )


def _get_deployment_order(
    services: Dict[str, Service],
    processed: set[str] = set(),
    result: list[str] = [],
    verbose: bool = False,
) -> list[str]:
    for service_name, service in services.items():
        if verbose:
            print(f"Processing dependencies for service '{service_name}'...")
        if service_name in processed:
            if verbose:
                print(f"Dependencies for service '{service_name}' already processed.")
            continue

        if not service.dependencies or all(
            dep in processed for dep in service.dependencies
        ):
            if verbose:
                print(
                    f"Service '{service_name}' has no dependencies or all are processed. Adding to deployment order."
                )
            result.append(service_name)
            processed.add(service_name)

            remaining_services = {
                name: svc for name, svc in services.items() if name not in processed
            }
            if remaining_services:
                if verbose:
                    print(
                        f"Remaining services to process: {', '.join(remaining_services.keys())}"
                    )
                _get_deployment_order(remaining_services, processed, result, verbose)

    return result


def _deploy_services(
    deploy_config: Deploy,
    catalog_path: Path,
    application_name: str,
    stack_name: str,
    environment: str,
    verbose: bool = False,
) -> None:
    deployment_order = _get_deployment_order(deploy_config.services, verbose=verbose)

    for service_name in deployment_order:
        service = deploy_config.services[service_name]
        package_name = service.package

        package_values_path = _get_package_value_path(
            catalog_path=catalog_path,
            application_name=application_name,
            environment=environment,
            package_name=package_name,
        )
        value_files = [file for file in package_values_path.iterdir() if file.is_file()]
        package_stack_name = f"{stack_name}-{package_name}"

        if verbose:
            print(
                f"Installing service '{package_name}' with stack name '{package_stack_name}'..."
            )

        extra_context = {"application_stack_name": stack_name}

        install_from_local(
            stack_name=package_stack_name,
            packages_dir=catalog_path / "packages",
            package_name=package_name,
            override_values_file=value_files,
            verbose=verbose,
            extra_context=extra_context,
        )

        wait_for_stack_services(package_stack_name, verbose=verbose)


def _validate_application_structure(
    catalog_path: Path, application_name: str, environment: str
) -> None:
    """
    Validate the structure of the application directory.
    """
    if not catalog_path.exists():
        raise ValueError(f"Catalog path '{catalog_path}' does not exist.")

    if not _get_application_yaml_path(catalog_path, application_name).exists():
        raise ValueError(
            f"Application YAML file '{_get_application_yaml_path(catalog_path, application_name)}' does not exist."
        )

    if not _get_application_path(catalog_path, application_name).exists():
        raise ValueError(
            f"Applications directory '{catalog_path / 'applications'}' does not exist."
        )

    if not _get_deploy_yaml_path(catalog_path, application_name).exists():
        raise ValueError(
            f"Deploy YAML file '{_get_deploy_yaml_path(catalog_path, application_name)}' does not exist."
        )

    deploy_config = _get_deploy_config(
        catalog_path=catalog_path, application_name=application_name
    )

    env_path = _get_environment_path(catalog_path, application_name, environment)

    if not env_path.exists():
        raise ValueError(f"Environment directory '{env_path}' does not exist.")

    for _, service in deploy_config.services.items():
        package_path = _get_package_path(catalog_path, service.package)
        if not package_path.exists():
            raise ValueError(f"Package '{package_path}' does not exist.")

        package_value_path = env_path / service.package
        if not package_value_path.exists():
            raise ValueError(
                f"Package value directory '{package_value_path}' does not exist."
            )


def _get_application_path(catalog_path: Path, application_name: str) -> Path:
    """
    Get the path to the application directory.
    """
    applications_path = catalog_path / "applications" / application_name
    return applications_path


def _get_application_yaml_path(catalog_path: Path, application_name: str) -> Path:
    """
    Get the path to the application.yaml file.
    """
    application_yaml_path = (
        _get_application_path(catalog_path, application_name) / "application.yaml"
    )
    return application_yaml_path


def _get_deploy_yaml_path(catalog_path: Path, application_name: str) -> Path:
    """
    Get the path to the deploy.yaml file.
    """
    deploy_yaml_path = (
        _get_application_path(catalog_path, application_name) / "deploy.yaml"
    )
    return deploy_yaml_path


def _get_deploy_config(catalog_path: Path, application_name: str) -> Deploy:
    return Deploy.from_yaml(_get_deploy_yaml_path(catalog_path, application_name))


def _get_package_path(catalog_path: Path, package_name: str) -> Path:
    """
    Get the path to the package directory.
    """
    packages_path = catalog_path / "packages" / package_name
    return packages_path


def _get_environment_path(
    catalog_path: Path, application_name: str, environment: str
) -> Path:
    """
    Get the path to the environment directory.
    """
    environment_path = (
        _get_application_path(catalog_path, application_name)
        / "environments"
        / environment
    )
    return environment_path


def _get_package_value_path(
    catalog_path: Path, application_name: str, environment: str, package_name: str
):
    env_path = _get_environment_path(
        catalog_path=catalog_path,
        application_name=application_name,
        environment=environment,
    )
    package_value_path = env_path / package_name
    return package_value_path
