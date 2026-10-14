#!/usr/bin/env bash
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

./run.sh --vfs vfs/stage4.json --script scripts/stage4_success.txt

for script in scripts/stage4_*.txt; do
    case "$script" in
        *success.txt) continue ;;
    esac
    if ./run.sh --vfs vfs/stage4.json --script "$script"; then
        printf 'Expected failure: %s\n' "$script" >&2
        exit 1
    else
        status=$?
        if [ "$status" -ne 1 ]; then
            printf 'Unexpected exit code: %s\n' "$status" >&2
            exit 1
        fi
    fi
done

printf 'cd folder/deep\nls ..\ncd /missing\nwhoami\nexit\n' |
    ./run.sh --vfs vfs/stage4.json
printf 'Stage 4 scenarios passed.\n'
