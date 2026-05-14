# QMT Data API

This repository is intended for building a QMT/xtquant data gateway that runs on the machine bound to QMT and exposes controlled APIs for other machines.

## Git Workflow

All changes should follow a branch-based workflow:

1. Start from `main`.
2. Create a feature branch for each change.
3. Commit only reviewed, intentional files.
4. Push the branch to the remote repository.
5. Open a pull request for review and merge.

Large local market data, cache files, logs, credentials, and QMT runtime artifacts should stay out of Git.
