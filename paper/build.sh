#!/bin/bash
# Build the submission PDF.
cd "$(dirname "$0")"
/opt/homebrew/bin/tectonic -X compile main.tex "$@"
