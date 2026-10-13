#!/usr/bin/env bash
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

for source in minimal several deep; do
    ./run.sh --vfs "vfs/$source.json" \
        --script scripts/stage3_success.txt
done
