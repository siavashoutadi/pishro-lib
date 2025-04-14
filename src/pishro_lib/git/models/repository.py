from pydantic import BaseModel, field_validator, SecretStr
from typing import Optional
import re


class GitRepository(BaseModel):
    """
    A model representing a Git repository.

    Attributes:
        name (str): The name of the repository. Must contain only alphanumeric characters, "-" and "_".
        url (str): The URL of the repository. Must be a valid Git URL.
        branch (str): The branch to use in the repository. Defaults to "main".
        username (Optional[str]): The username for authentication (if required).
        token (Optional[SecretStr]): The token for authentication (if required).
    """

    name: str
    url: str
    branch: str = "main"
    username: Optional[str] = None
    token: Optional[SecretStr] = None

    @field_validator("name")
    def validate_name(cls, v):
        """
        Validate the name format to ensure it only contains alphanumeric characters, "-" and "_".

        Args:
            v (str): The name to validate.

        Returns:
            str: The validated name.

        Raises:
            ValueError: If the name format is invalid.
        """
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Invalid repository name format. Only alphanumeric characters, '-' and '_' are allowed."
            )
        return v

    @field_validator("url")
    def validate_url(cls, v):
        """
        Validate the URL format and ensure it is a valid Git repository URL.

        Args:
            v (str): The URL to validate.

        Returns:
            str: The validated URL.

        Raises:
            ValueError: If the URL format is invalid.
        """
        if not re.match(r"^https?://.*\.git$|^git@.*:.*.git$", v):
            raise ValueError(
                "Invalid git repository URL format. Example of valid url 'https://github.com/org/example.repo"
            )
        return v

    def get_clone_url(self) -> str:
        """
        Generate the appropriate clone URL based on authentication.

        If both `username` and `token` are provided, the method generates an
        authenticated HTTPS URL. Otherwise, it returns the original URL.

        Returns:
            str: The clone URL for the repository.

        Example:
            repo = GitRepository(
                name="example-repo",
                url="https://example.com/repo.git",
                username="user",
                token=SecretStr("token123")
            )
            clone_url = repo.get_clone_url()
            print(clone_url)  # Outputs: https://user:token123@example.com/repo.git
        """
        if self.username and self.token:
            # Convert HTTP URL to authenticated URL
            if self.url.startswith("https://"):
                return self.url.replace(
                    "https://",
                    f"https://{self.username}:{self.token.get_secret_value()}@",
                )
        return self.url
