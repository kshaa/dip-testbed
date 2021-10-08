import os


def script_relative_path(relative_path: str) -> str:
    dirname = os.path.dirname(__file__)
    return os.path.join(dirname, relative_path)
