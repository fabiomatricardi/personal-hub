# GitHub Commands

## Git Basics
```
git init                    # Initialize repo
git clone <url>             # Clone remote repo
git add .                   # Stage all changes
git commit -m "message"     # Commit with message
git push                    # Push to remote
git pull                    # Pull from remote
```

## Branching
```
git branch                  # List branches
git branch <name>           # Create branch
git checkout <name>         # Switch branch
git checkout -b <name>      # Create and switch
git merge <branch>          # Merge branch into current
git branch -d <name>        # Delete branch
```

## History
```
git log --oneline           # Compact log
git log -5                  # Last 5 commits
git diff                    # Unstaged changes
git diff --staged           # Staged changes
git show                    # Last commit details
```

## Undoing
```
git reset HEAD <file>       # Unstage file
git checkout -- <file>      # Discard changes
git revert <commit>         # Revert a commit
git reset --hard <commit>   # Reset to commit (destructive)
```
