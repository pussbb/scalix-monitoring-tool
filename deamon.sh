#!/bin/bash
function get_real_path() {
    [ -n "$(type -p realpath)" ] && $(type -p realpath) "$1" || $(type -p readlink) -f "$1"
}
REAL_SCRIPT_PATH=$(get_real_path `dirname $0`)

source "$REAL_SCRIPT_PATH/.venv/bin/activate"

python "$REAL_SCRIPT_PATH/main.py" -d 
