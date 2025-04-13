import pytest
from pydantic import ValidationError, SecretStr
from pishro_lib.git.models.repository import GitRepository


def test_valid_name():
    """Test that a valid name passes validation."""
    repo = GitRepository(name="valid_name-123", url="https://example.com/repo.git")
    assert repo.name == "valid_name-123"


def test_invalid_name():
    """Test that an invalid name raises a ValidationError."""
    with pytest.raises(ValidationError, match="Invalid repository name format"):
        GitRepository(name="invalid name!", url="https://example.com/repo.git")


def test_valid_url():
    """Test that a valid URL passes validation."""
    repo = GitRepository(name="valid_repo", url="https://example.com/repo.git")
    assert repo.url == "https://example.com/repo.git"


def test_invalid_url():
    """Test that an invalid URL raises a ValidationError."""
    with pytest.raises(ValidationError, match="Invalid git repository URL format"):
        GitRepository(name="valid_repo", url="invalid-url")


def test_invalid_url_missing_protocol():
    """Test that a URL missing the protocol raises a ValidationError."""
    with pytest.raises(ValidationError, match="Invalid git repository URL format"):
        GitRepository(name="valid_repo", url="example.com/repo.git")


def test_invalid_url_missing_git_suffix():
    """Test that a URL missing the '.git' suffix raises a ValidationError."""
    with pytest.raises(ValidationError, match="Invalid git repository URL format"):
        GitRepository(name="valid_repo", url="https://example.com/repo")


def test_invalid_url_invalid_characters():
    """Test that a URL with invalid characters raises a ValidationError."""
    with pytest.raises(ValidationError, match="Invalid git repository URL format"):
        GitRepository(name="valid_repo", url="https://example.com/repo.git?invalid")


def test_invalid_url_empty_string():
    """Test that an empty URL raises a ValidationError."""
    with pytest.raises(ValidationError, match="Invalid git repository URL format"):
        GitRepository(name="valid_repo", url="")


def test_invalid_url_whitespace():
    """Test that a URL with only whitespace raises a ValidationError."""
    with pytest.raises(ValidationError, match="Invalid git repository URL format"):
        GitRepository(name="valid_repo", url="   ")


def test_invalid_url_ftp_protocol():
    """Test that a URL with an unsupported protocol (e.g., FTP) raises a ValidationError."""
    with pytest.raises(ValidationError, match="Invalid git repository URL format"):
        GitRepository(name="valid_repo", url="ftp://example.com/repo.git")


def test_clone_url_with_authentication():
    """Test that the clone URL is correctly generated with authentication."""
    repo = GitRepository(
        name="auth_repo",
        url="https://example.com/repo.git",
        username="user",
        token=SecretStr("token123"),
    )
    assert repo.get_clone_url() == "https://user:token123@example.com/repo.git"


def test_clone_url_without_authentication():
    """Test that the original URL is returned when no authentication is provided."""
    repo = GitRepository(name="no_auth_repo", url="https://example.com/repo.git")
    assert repo.get_clone_url() == "https://example.com/repo.git"
