import re
import yaml

from pathlib import Path
from builtins import ValueError, all, isinstance, list, str
from pydantic import BaseModel, field_validator
from typing import Optional


class Package(BaseModel):
    """
    A model representing a pishro package.

    Attributes:
        name (str): The name of the package.
        version (str): The version of the package, following semantic versioning.
        description (Optional[str]): A brief description of the package.
        maintainers (Optional[list[str]]): A list of maintainers for the package.
        tags (Optional[list[str]]): A list of tags associated with the package.
    """

    name: str
    version: str
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

    @field_validator("version")
    def validate_version(cls, v):
        """
        Ensures the version follows semantic versioning (e.g., "1.0.0").

        Args:
            v (str): The version to validate.

        Returns:
            str: The validated version.

        Raises:
            ValueError: If the version does not follow the format "X.Y.Z".
        """
        if not re.match(r"^\d+\.\d+\.\d+$", v):
            raise ValueError(
                "Invalid version format. Version must be in the format 'X.Y.Z'."
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
    def from_yaml(cls, yaml_file: Path) -> "Package":
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
