# Working on QuickUMLS

Use a separate Git worktree for each independent change. Keep worktrees under `~/Code/QuickUMLS.worktrees/` and name topic branches `codex/<topic>`. Start from the current `origin/master` unless a change depends on another branch. For example, from the main checkout:

```sh
git fetch origin
git worktree add -b codex/matcher-fix ~/Code/QuickUMLS.worktrees/matcher-fix origin/master
cd ~/Code/QuickUMLS.worktrees/matcher-fix
```

Keep changes compact and exercise the public API that users call. Use the fictional fixtures for routine tests and examples. Keep licensed UMLS files and derived indexes in an ignored local directory. Run the repository tests from the worktree with `python -m unittest discover -s tests -v`, using a Python environment that imports that checkout.

Commit and push the topic branch, then open one **draft pull request per worktree** against `master` (or its dependency branch for stacked work). Describe the behavior change, link relevant issues, and report what you tested and any remaining gaps.
