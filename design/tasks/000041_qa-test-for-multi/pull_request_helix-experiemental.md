# Add QA marker file for multi-repo PR history test

## Summary
Adds `qa/multi-repo-pr-history-20261001.txt` containing the single line `helix-experiemental`. This is part of a QA test for multi-repository PR history, where each participating repository carries an identically named marker file identifying itself. No other files were changed.

## Testing
Verified the file contents match the repository name, confirmed `git status` shows a clean working tree, and pushed branch `feature/000041-qa-test-for-multi` (commit `264ad23`) to origin.
