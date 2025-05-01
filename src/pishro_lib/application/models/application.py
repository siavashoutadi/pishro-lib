import re
import yaml

from pathlib import Path
from typing import Optional, Dict
from builtins import ValueError, all, isinstance, list, str

from pydantic import BaseModel, field_validator, model_validator
from pydantic import BaseModel


class Application(BaseModel):
    """
    A model representing a pishro application.

    Attributes:
        name (str): The name of the package.
        version (str): The version of the package, following semantic versioning.
        description (Optional[str]): A brief description of the package.
        maintainers (Optional[list[str]]): A list of maintainers for the package.
        tags (Optional[list[str]]): A list of tags associated with the package.
    """

    name: str
    description: Optional[str] = ""
    maintainers: Optional[list[str]] = []
    tags: Optional[list[str]] = []

    @field_validator("name")
    def validate_name(cls, v):
        """
        Ensures the name contains only alphanumeric characters, hyphens ("-"), and underscores ("_").

        Args:
            v (str): The name to validate.

        Returns:
            str: The validated name.

        Raises:
            ValueError: If the name contains invalid characters.
        """
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Invalid package name format. Only alphanumeric characters, '-' and '_' are allowed."
            )
        return v

    @field_validator("description")
    def validate_description(cls, v):
        """
        Ensures the description is a string.

        Args:
            v (str): The description to validate.

        Returns:
            str: The validated description.

        Raises:
            ValueError: If the description is not a string.
        """
        if not isinstance(v, str):
            raise ValueError("Description must be a string.")
        return v

    @field_validator("maintainers")
    def validate_maintainers(cls, v):
        """
        Ensures the maintainers field is a list of strings.

        Args:
            v (list): The maintainers to validate.

        Returns:
            list: The validated maintainers.

        Raises:
            ValueError: If the maintainers field is not a list of strings.
        """
        if not isinstance(v, list) or not all(isinstance(i, str) for i in v):
            raise ValueError("Maintainers must be a list of strings.")
        return v

    @field_validator("tags")
    def validate_tags(cls, v):
        """
        Ensures the tags field is a list of strings containing only alphanumeric characters,
        spaces (" "), hyphens ("-"), and underscores ("_").

        Args:
            v (list): The tags to validate.

        Returns:
            list: The validated tags.

        Raises:
            ValueError: If the tags field contains invalid values.
        """
        if not isinstance(v, list) or not all(
            isinstance(i, str) and re.match(r"^[a-zA-Z0-9_ -]+$", i) for i in v
        ):
            raise ValueError(
                "Tags must be a list of strings containing valid characters."
            )
        return v

    @classmethod
    def from_yaml(cls, yaml_file: Path) -> "Application":
        """
        Creates a Package instance from a YAML file.

        Args:
            yaml_file (Path): Path to the YAML file.

        Returns:
            Package: A new Package instance with data from the YAML file.

        Raises:
            FileNotFoundError: If the YAML file doesn't exist.
            ValueError: If the YAML file is invalid or missing required fields.
            yaml.YAMLError: If there's an error parsing the YAML file.
        """
        if not yaml_file.exists():
            raise FileNotFoundError(f"YAML file not found: {yaml_file}")

        with yaml_file.open("r") as f:
            try:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    raise ValueError("YAML file must contain a dictionary")
                return cls(**data)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Error parsing YAML file: {e}")


class Service(BaseModel):
    package: str
    version: Optional[str] = ""
    repository: Optional[str] = ""
    dependencies: Optional[list[str]] = []

    @field_validator("package")
    def validate_package(cls, v):
        """
        Ensures the package name contains only alphanumeric characters, hyphens ("-"), and underscores ("_").

        Args:
            v (str): The package name to validate.

        Returns:
            str: The validated package name.

        Raises:
            ValueError: If the package name contains invalid characters.
        """
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Invalid package name format. Only alphanumeric characters, '-' and '_' are allowed."
            )
        return v

    @field_validator("version")
    def validate_version(cls, v):
        """
        Ensures the version is a string.

        Args:
            v (str): The version to validate.

        Returns:
            str: The validated version.

        Raises:
            ValueError: If the version is not a string.
        """
        if v and not isinstance(v, str):
            raise ValueError("Version must be a string.")
        return v

    @field_validator("repository")
    def validate_repository(cls, v):
        """
        Ensures the repository is a string.

        Args:
            v (str): The repository to validate.

        Returns:
            str: The validated repository.

        Raises:
            ValueError: If the repository is not a string.
        """
        if v and not isinstance(v, str):
            raise ValueError("Repository must be a string.")
        return v

    @field_validator("dependencies")
    def validate_dependencies(cls, v):
        """
        Ensures the dependencies field is a list of strings.

        Args:
            v (list): The dependencies to validate.

        Returns:
            list: The validated dependencies.

        Raises:
            ValueError: If the dependencies field is not a list of strings.
        """
        if not isinstance(v, list) or not all(isinstance(i, str) for i in v):
            raise ValueError("Dependencies must be a list of strings.")
        return v


class Deploy(BaseModel):
    services: Dict[str, Service]

    @model_validator(mode="after")
    def validate_service_dependencies(self) -> "Deploy":
        """
        Validates that all dependencies of the services match one of the keys in the services dictionary.

        Returns:
            Deploy: The validated Deploy instance.

        Raises:
            ValueError: If any dependency does not match a key in the services dictionary.
        """
        for service_name, service in self.services.items():
            for dependency in service.dependencies or []:
                if dependency not in self.services:
                    raise ValueError(
                        f"Service '{service_name}' has a dependency '{dependency}' "
                        f"that does not match any service in the services."
                    )
        return self

    @classmethod
    def from_yaml(cls, yaml_file: Path) -> "Deploy":
        if not yaml_file.exists():
            raise FileNotFoundError(f"YAML file not found: {yaml_file}")

        with yaml_file.open("r") as f:
            try:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    raise ValueError("YAML file must contain a dictionary")
                return cls(**data)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Error parsing YAML file: {e}")
