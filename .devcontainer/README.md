Devcontainer for ArmaDocker

Quick start

- Open this folder in VS Code and choose "Reopen in Container" from the command palette.
- The container installs runtime dependencies and `python-dotenv`.
- To verify, run:

```bash
python launch.py
```

Notes
- If you need additional Python packages, add a `requirements.txt` to the repo and update `postCreateCommand` in `devcontainer.json`.
