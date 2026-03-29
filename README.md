It's been a while - Git needs an update for the next generation of programmers.

Git is a great set of rails, but it's too complex for beginners. Vibe coders and the next generation would likely appreciate a simpler tool.

Dot is a simplified version of Git, using Git rails.

You can always default to git commands if you want- there is no lock-in here.

## How it works

Save your work.
```
dot save "fix login bug"
```

Push it to the remote.
```
dot push "shipped it"
```

Pull the latest changes.
```
dot pull
```

Undo the last save.
```
dot undo
```

Switch branches.
```
dot switch -c new-feature
```

Fix the last save.
```
dot amend "better message"
```

Throw away uncommitted changes.
```
dot discard
```

Add a file to .gitignore.
```
dot ignore .env
```

Anything else goes straight to git.
```
dot status
dot log --oneline
```
