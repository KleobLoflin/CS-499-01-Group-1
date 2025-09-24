code to run it in gitbash
python -m game.app

needed assets to run
pip install pytmx
pip install pygames

## Basic protocol for merging a feature branch into main in bash:
# Start on your feature branch
git checkout <feature_branch>
git fetch origin

# Make sure both branches are up to date locally
git pull --ff-only origin <feature_branch>
git checkout main
git pull --ff-only origin main

# Rebase the feature branch onto the latest main
git checkout <feature_branch>
git rebase origin/main

(If conflicts: fix files, `git add <file>`, then `git rebase --continue`.
To bail out: `git rebase --abort`.)

# Fast-forward merge into main
git checkout main
git merge --ff-only <feature_branch>

# Push the updated main
git push origin main

# (Optional) delete the feature branch
git branch -d <feature_branch>
git push origin --delete <feature_branch>
