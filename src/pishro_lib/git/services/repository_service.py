from pishro_lib.git.models.repository import GitRepository
from typing import List


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
    print("Add new repository")


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
    print("Remove repository")


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
    print("List all repositories")
    return []


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
    print("Get repository details")
    return GitRepository(
        name=name,
        url="https://example.com/repo.git",
    )
