import subprocess
import sys
from pathlib import Path


def get_project_dir() -> Path:
    return Path(__file__).parent.resolve()


def main() -> None:
    project_dir = get_project_dir()

    print("Starting the FastMCP application...", file=sys.stderr)

    cmd = [
        "uv",
        "run",
        "--directory",
        str(project_dir),
        "fastmcp",
        "run",
        "app/main.py",
    ]

    print(f"Executing: {' '.join(cmd)}", file=sys.stderr)

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
