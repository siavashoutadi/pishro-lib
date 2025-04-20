import shutil

from pathlib import Path

from ..models.package import Package
from ...git.services.repository_service import clone_repository
from typing import List


def download_package(
    repository_name: str,
    package_name: str,
    version: str = "",
    destination: str = "./packages/",
) -> None:
    """
    Downloads a pishro package from the pishro repository.

    Args:
        repository_name (str): The name of the pishro repository.
        package_name (str): The name of the pishro package to download.
        version (str): The version of the pishro package to download.
        destination (str): The destination directory where the pishro package will be downloaded.
    """

    branch = f"{package_name}-{version}"
    if not version:
        branch = "main"

    with clone_repository(repository_name, branch) as repo_path:
        source_dir = Path(repo_path) / package_name
        if not source_dir.exists():
            raise ValueError(
                f"Package '{package_name}' not found in repository '{repository_name}'"
            )
        destination_dir = Path(destination) / package_name
        shutil.copytree(source_dir, destination_dir, dirs_exist_ok=True)


def get_packages(repository_name: str) -> List[Package]:
    """
    Get all packages in the repository.

    Args:
        repository_name (str): The name of the repository.

    Returns:
        List[Package]: A list of Package objects.
    """
    with clone_repository(repository_name, "main") as repo_path:
        packages: list[Package] = []

        for item in Path(repo_path).iterdir():
            if (
                item.is_dir()
                and not item.name.startswith("_")
                and not item.name.startswith(".")
            ):
                package_yaml = item / "package.yaml"
                if package_yaml.exists():
                    package = Package.from_yaml(yaml_file=package_yaml)
                    packages.append(package)

        return packages


def get_package(repository_name: str, package_name: str) -> Package:
    """
    Get a specific package in the repository.

    Args:
        repository_name (str): The name of the repository.
        package_name (str): The name of the package to get.

    Returns:
        Package: A Package object.
    """
    with clone_repository(repository_name, "main") as repo_path:
        for item in Path(repo_path).iterdir():
            if (
                item.is_dir()
                and not item.name.startswith("_")
                and not item.name.startswith(".")
            ):
                package_yaml = item / "package.yaml"
                if package_yaml.exists():
                    package = Package.from_yaml(yaml_file=package_yaml)
                    if package.name == package_name:
                        return package
        raise ValueError(
            f"Package '{package_name}' not found in repository '{repository_name}'"
        )
