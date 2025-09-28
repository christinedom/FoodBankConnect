# Makefile

# Default commit message
message ?= "Another commit"

push:
	git add .
	git commit -m $(message)
	git push
