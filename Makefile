# Makefile

# Default commit message
message ?= "Another commit"

push:
	git add .
	git commit -m "$(message)"
	git push

log:
	git log > git-log.txt

status:
	git fetch
	git status
