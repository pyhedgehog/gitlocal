#!/bin/bash
ln -fs "$(dirname "$0")/gitlocal.py" /usr/local/bin/gitlocal
git config --global --replace-all alias.local '!gitlocal'
