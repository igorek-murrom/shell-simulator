#!/usr/bin/env bash
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

expect_error() {
    if "$@"; then
        printf 'Expected failure, but emulator succeeded.\n' >&2
        exit 1
    else
        status=$?
        if [ "$status" -ne 1 ]; then
            printf 'Unexpected exit code: %s\n' "$status" >&2
            exit 1
        fi
    fi
}

for source in minimal several deep; do
    for scenario in unknown ls_error cd_error exit_error syntax_error; do
        expect_error ./run.sh --vfs "vfs/$source.json" \
            --script "scripts/stage3_$scenario.txt"
    done
done

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf -- "$TEMP_DIR"' EXIT
printf 'not JSON\n' > "$TEMP_DIR/invalid.json"
printf '{"type":"directory","name":"/","children":{}}\n' \
    > "$TEMP_DIR/tree.json"
printf '{"type":"directory","name":"/","children":[' \
    > "$TEMP_DIR/base64.json"
printf '{"type":"file","name":"bad","encoding":"base64",' \
    >> "$TEMP_DIR/base64.json"
printf '"content":"!!!"}]}\n' >> "$TEMP_DIR/base64.json"

for source in missing invalid tree base64; do
    expect_error ./run.sh --vfs "$TEMP_DIR/$source.json" \
        --script scripts/stage3_success.txt
done
expect_error ./run.sh --vfs vfs/minimal.json \
    --script "$TEMP_DIR/missing.txt"
