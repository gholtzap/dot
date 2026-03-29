It's been a while - Git needs an update for the next generation of programmers.

Git is a great set of rails, but it's too complex for beginners. Vibe coders and the next generation would likely appreciate a simpler tool.

Dot is a simplified version of Git, using Git rails.

You can always default to git commands if you want- there is no lock-in here.

## How it works

### Push
```
dot push
```
~~# git add -A && git commit -m "2026-03-29 19:44 -- modified 2 files" && git push~~

### Save
```
dot save
```
~~# git add -A && git commit -m "2026-03-29 19:44 -- modified 2 files"~~


### Pull
```
dot pull
```
~~git pull --rebase~~


### Undo
```
dot undo
```

~~git revert HEAD --no-edit~~


### Fix the last save.
```
dot amend "better message"
```

~~git add -A && git commit --amend -m "better message"~~

### Throw away uncommitted changes.
```
dot discard
```

~~git checkout -- . && git clean -fd~~

### Add a file to .gitignore.
```
dot ignore .env
```
~~echo ".env" >> .gitignore~~

---

Anything else goes straight to git.
```
dot status
dot log --oneline
```
