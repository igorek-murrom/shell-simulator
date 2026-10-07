#!/usr/bin/env bash
set -u

printf "exit\n" | ./run.sh

printf "exit\n" | ./run.sh \
    --vfs "vfs/minimal.json"

./run.sh \
    --script "scripts/stage2_error.txt"

./run.sh \
    --vfs "vfs/minimal.json" \
    --script "scripts/stage2_error.txt"