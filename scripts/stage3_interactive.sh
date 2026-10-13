#!/usr/bin/env bash
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

for source in minimal several deep; do
    printf 'ls /\ncd /\nunknown\nls "two words.txt"\nexit\n' |
        ./run.sh --vfs "vfs/$source.json"
done
