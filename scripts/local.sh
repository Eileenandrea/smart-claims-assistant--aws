#!/bin/bash

# Source user bashrc so aliases and PATH entries are available in non-interactive shells
if [ -f "$HOME/.bashrc" ]; then
  source "$HOME/.bashrc"
fi

# Try to find sam (support sam, sam.cmd, sam.exe)
SAM="$(command -v sam 2>/dev/null || command -v sam.cmd 2>/dev/null || command -v sam.exe 2>/dev/null)"
# Fallback: search PATH directories for sam.cmd
if [ -z "$SAM" ]; then
  IFS=':' read -ra PATHDIRS <<< "$PATH"
  for d in "${PATHDIRS[@]}"; do
    if [ -x "$d/sam.cmd" ]; then
      SAM="$d/sam.cmd"
      break
    fi
  done
fi

if [ -z "$SAM" ]; then
  echo "ERROR: 'sam' not found in PATH. Install AWS SAM CLI or add it to your PATH." >&2
  exit 1
fi

"$SAM" build && "$SAM" local start-api
