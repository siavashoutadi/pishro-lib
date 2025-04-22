import secrets

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Dict
from .docker_utils import (
    generate_random_docker_secret,
    create_secret_from_env,
    create_secret_from_file,
)


class JinjaEnvironment:
    """
    A class to encapsulate the creation and management of a Jinja2 environment.
    """

    def __init__(self, template_dir: Path):
        """
        Initializes the JinjaEnvironment with a Jinja2 environment.

        Args:
            template_dir (Path): The directory containing Jinja2 templates.
        """
        self.environment = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        self.environment.globals["random_docker_secret"] = generate_random_docker_secret
        self.environment.globals["docker_secret_from_env"] = create_secret_from_env
        self.environment.globals["docker_secret_from_file"] = create_secret_from_file
        self.environment.globals["random_secret"] = generate_random_secret

    def get_environment(self) -> Environment:
        """
        Returns the Jinja2 environment.

        Returns:
            Environment: The configured Jinja2 environment.
        """
        return self.environment

    def render_template(self, template_name: str, context: Dict) -> str:
        """
        Renders a template with the given context.

        Args:
            template_name (str): The name of the template to render.
            context (Dict): The context to render the template with.

        Returns:
            str: The rendered template as a string.
        """
        template = self.environment.get_template(template_name)
        return template.render(context)

    def render_string(self, template_string: str, context: Dict) -> str:
        """
        Renders a string with the given context.

        Args:
            context (Dict): The context to render the string with.

        Returns:
            str: The rendered string.
        """
        return self.environment.from_string(template_string, context).render()

    def add_environment_globals(self, service_name: str, environments: Dict) -> None:
        """
        Adds global environment variables to the Jinja2 environment.

        Args:
            globals (Dict): A dictionary of global environment variables to add.
        """
        self.environment.globals["environments"] = {f"{service_name}": environments}

    def add_secret_globals(self, service_name: str, secrets: Dict) -> None:
        """
        Adds global secret variables to the Jinja2 environment.

        Args:
            globals (Dict): A dictionary of global secret variables to add.
        """

        self.environment.globals["secrets"] = {f"{service_name}": secrets}

    def add_environmens_secret_name(self, sha: str) -> None:
        """
        Adds global environment secret name to the Jinja2 environment.

        Args:
            globals (Dict): A dictionary of global environment secret name to add.
        """
        self.environment.globals["environments_secret_name"] = sha


def generate_random_secret(length: int = 16) -> str:
    """
    Generates a random secret string of the specified length.

    Args:
        length (int): The length of the secret string. Defaults to 16.

    Returns:
        str: A random secret string.
    """

    return secrets.token_hex(length)
