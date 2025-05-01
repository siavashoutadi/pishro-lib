import shutil
import yaml

from pathlib import Path
from typing import Dict, List, Optional

from ...utils.jinja_utils import JinjaEnvironment
from ...utils.file_utils import write_file

from ..models.package import EnvironmentVariable, Package
from ...git.services.repository_service import clone_repository


def download_package(
    repository_name: str,
    package_name: str,
    version: str = "",
    destination: Path | str = "./packages/",
    sub_directory: str = "",
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
        if sub_directory:
            source_dir = Path(repo_path) / sub_directory / package_name
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


def init_package(package_path: Path, package_name: str) -> None:
    """
    Initializes a new package by creating the necessary directory structure
    and populating it with rendered template files.

    Args:
        package_path (Path): The path where the package directory will be created.
        package_name (str): The name of the package to be used in the templates.
    """
    package_path.mkdir(parents=True, exist_ok=True)

    template_dir = Path(__file__).parent.parent / "templates" / "package"

    jinja_env = JinjaEnvironment(template_dir=template_dir)

    context = {"package_name": package_name}
    for template_file in template_dir.rglob("*"):
        if template_file.is_file() and not template_file.name.startswith("."):
            relative_path = template_file.relative_to(template_dir)
            rendered_path = jinja_env.render_string(str(relative_path), context=context)
            destination_file = package_path / rendered_path

            rendered_content = jinja_env.render_template(
                template_name=str(relative_path),
                context=context,
            )

            write_file(destination_file, rendered_content)


def generate_deployment_package(
    stack_name: str,
    package_path: Path,
    destination: Path,
    override_values_file: Optional[Path] | Optional[list[Path]],
    verbose: bool = False,
    extra_context: Dict = {},
) -> None:
    """
    Generates a deployment package for a given stack.
    Args:
        stack_name (str): The name of the stack.
        package_path (Path): The path to the package directory.
        destination (Path): The destination directory for the generated package.
        override_values_file (Optional[Path]) | Optional[list[Path]]: The path to the override values file.
        verbose (bool): Whether to print verbose output.
    """
    _validate_package_structure(package_path)

    values, env_vars, secret_vars = _get_values(
        stack_name=stack_name,
        package_path=package_path,
        override_values_file=override_values_file,
        extra_context=extra_context,
    )
    values["stack_name"] = stack_name

    template_dir = package_path / "templates"

    jinja_env = JinjaEnvironment(template_dir=template_dir)

    service_name = values.get("service", {}).get("name")
    if not service_name:
        raise ValueError(
            f"Service name not found in values.yaml for stack '{stack_name}'"
        )

    jinja_env.add_environment_globals(service_name, env_vars)
    jinja_env.add_secret_globals(service_name, secret_vars)

    for template_file in template_dir.rglob("*"):
        if template_file.is_file() and not template_file.name.startswith("."):
            relative_path = template_file.relative_to(template_dir)
            destination_file = destination / relative_path

            rendered = jinja_env.render_template(
                template_name=str(relative_path), context=values
            )

            write_file(destination_file, rendered, verbose=verbose)


def _get_values(
    stack_name: str,
    package_path: Path,
    override_values_file: Optional[Path] | Optional[list[Path]] = None,
    extra_context: Dict = {},
) -> tuple[Dict, Dict, Dict]:
    _validate_package_structure(package_path)
    _validate_override_values_files(override_values_file)

    values_file = package_path / "values.yaml"
    values_file_content, default_envs, default_secrets = _parse_values(
        stack_name=stack_name, values_file=values_file, extra_context=extra_context
    )

    if not override_values_file:
        return (values_file_content, default_envs, default_secrets)

    if isinstance(override_values_file, Path):
        override_values_content, override_envs, override_secrets = _parse_values(
            stack_name=stack_name,
            values_file=override_values_file,
            extra_context=extra_context,
        )

        values = _deep_merge_values(values_file_content, override_values_content)
        env_vars = _deep_merge_values(default_envs, override_envs)
        env_secrets = _deep_merge_values(default_secrets, override_secrets)

        return (values, env_vars, env_secrets)

    if isinstance(override_values_file, list):
        for override_file in sorted(override_values_file):
            override_values_content, override_envs, override_secrets = _parse_values(
                stack_name=stack_name,
                values_file=override_file,
                extra_context=extra_context,
            )

            values = _deep_merge_values(values_file_content, override_values_content)
            env_vars = _deep_merge_values(default_envs, override_envs)
            env_secrets = _deep_merge_values(default_secrets, override_secrets)

        return (values, env_vars, env_secrets)


def _parse_values(
    stack_name: str, values_file: Path, extra_context: Dict = {}
) -> tuple[Dict, Dict, Dict]:
    extra_context.update({"stack_name": stack_name})
    jinja_env = JinjaEnvironment(template_dir=values_file.parent)
    file = jinja_env.render_template(
        template_name=str(values_file.name), context=extra_context
    )
    values_file_content = yaml.safe_load(file) or {}
    env_values = values_file_content.get("environments", {})
    values_file_content.pop("environments", None)

    env_vars = {}
    env_secrets = {}
    for name, config in env_values.items():
        env_var = EnvironmentVariable(**config)
        if env_var.isSecret:
            env_secrets[name] = EnvironmentVariable(**config)
        else:
            env_vars[name] = EnvironmentVariable(**config)
    return values_file_content, env_vars, env_secrets


def _deep_merge_values(default_values: Dict, override_values: Dict) -> Dict:
    merged = default_values.copy()

    for key, value in override_values.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge_values(merged[key], value)
        else:
            merged[key] = value

    return merged


def _validate_package_structure(package_path: Path) -> None:
    required_files = [
        package_path / "package.yaml",
        package_path / "values.yaml",
    ]

    for file in required_files:
        if not file.exists():
            raise FileNotFoundError(
                f"Required file '{file}' not found in package directory '{package_path}'."
            )

    stack_files = [
        package_path / "templates" / "stack.yaml",
        package_path / "templates" / "stack.yml",
    ]

    if not any(file.exists() for file in stack_files):
        raise FileNotFoundError(
            f"Neither 'stack.yaml' nor 'stack.yml' found in package directory '{package_path}/templates'."
        )


def _validate_override_values_files(
    override_values_file: Optional[Path] | Optional[list[Path]] = None,
) -> None:
    if override_values_file:
        if isinstance(override_values_file, Path):
            if not override_values_file.exists() or not override_values_file.is_file():
                raise FileNotFoundError(
                    f"Override values file '{override_values_file}' is invalid or does not exist"
                )
        else:
            for override_file in override_values_file:
                if not override_file.exists() or not override_file.is_file():
                    raise FileNotFoundError(
                        f"Override values file '{override_file}' is invalid or does not exist"
                    )
