# Working on QuickUMLS

QuickUMLS matches phrases in biomedical text to UMLS concepts, and this guide
explains how to develop, test, and submit changes to the project.

## Worktrees and pull requests

Use `git worktree list` to find the main checkout and set `GIT_DIRECTORY` to its
root. From that root, place each independent change in its own worktree under
`"../$(basename "${GIT_DIRECTORY}").worktrees"`. Name the worktree and branch
after the feature or fix. When removing a worktree, use the path from the listing.

Identify the upstream remote with `git remote -v` and its default branch with
`git remote show <remote>`. Fetch the remote and start from the tip of its
default branch, or from the dependency branch for stacked work. Commit and push
the topic branch, then open one draft pull request per worktree against its base.
Describe the change, link relevant issues, and report test results and any gaps.

## Design principles

- Keep matching rules in `quickumls/core.py`. The server exposes the same matcher
  as the Python API, and the spaCy component passes it a parsed `Doc`.
- Normalize terms for lookup while keeping `start` and `end` as character offsets
  in the original text. Group candidate concepts by the span they match.
- Keep the installer and matcher in sync on language, case, Unicode normalization,
  and database backend. Preserve the LevelDB fallback for indexes that predate
  the backend flag.
- Use SimString to find candidate terms and `CuiSemTypesDB` to look up their
  concept identifiers (CUIs) and semantic types. Keep LevelDB and UnQLite access
  inside that wrapper.

## Tests and data

Test through the affected public API. Use fictional terms and CUIs in tests and
examples, and keep licensed UMLS files and their derived indexes in an ignored
local directory. If the checkout has a `tests/` directory, run
`python -m unittest discover -s tests -v` from the worktree root.
