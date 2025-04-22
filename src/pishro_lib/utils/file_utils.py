from pathlib import Path


def write_file(file_path: Path, content: str, verbose: bool = False) -> None:
    """
    Write content to a file at the specified path.

    Args:
        path (Path): The path to the file.
        content (str): The content to write to the file.
        verbose (bool): If True, print the content to the console.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as file:
        if verbose:
            print(f"\n##### {file_path} #####")
            if "secret" in str(file_path):
                print("******")
            else:
                print(content)
        file.write(content)
