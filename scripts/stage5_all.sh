#!/usr/bin/env bash
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

./run.sh --vfs vfs/stage5.json --script scripts/stage5_success.txt

for script in scripts/stage5_*.txt; do
    case "$script" in
        *success.txt) continue ;;
    esac
    if ./run.sh --vfs vfs/stage5.json --script "$script"; then
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

printf 'rm missing\nls -lah\nrm -r tree\nrmdir empty\nls -lah\nexit\n' |
    ./run.sh --vfs vfs/stage5.json
printf 'Stage 5 scenarios passed.\n'
