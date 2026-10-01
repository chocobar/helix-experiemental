# Add QA marker file for multi-repo PR history test

## Summary
Adds `qa/multi-repo-pr-history-20261001.txt` containing the single line `helix-collaboration`. This is part of a QA test for multi-repository PR history, where each participating repository carries an identically named marker file identifying itself. The feature branch was created from `main` and no other files were changed.

## Testing
Verified the file contents match the repository name, confirmed `git status` shows a clean working tree, and pushed branch `feature/000041-qa-test-for-multi` (commit `d6b790f`) to origin.
