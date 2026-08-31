# How to contribute to the Apple Health MCP Server

1. Fork the repository.
2. Clone your fork.
3. Make sure `uv` is installed.
4. Create a new branch for your contribution.
5. Develop changes.
6. Before pushing, run `make check` (lint + format check + type check) and `make format` to auto-fix what it can. First-time setup: `uv sync --group code-quality`. Optionally run `uv run pre-commit install` to run the same checks automatically on every commit.
7. Commit your changes and push the entire branch to the remote (`git push -u origin <local_branch_name>`). It will automatically create a Pull Request here.

Your contributions are more than welcome! :)
