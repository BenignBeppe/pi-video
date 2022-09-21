#! /usr/bin/env bash

flake8 $(git ls-tree --full-tree -r --name-only HEAD | egrep \.py$)
