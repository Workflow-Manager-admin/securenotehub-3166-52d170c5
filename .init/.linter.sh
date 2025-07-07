#!/bin/bash
cd /home/kavia/workspace/code-generation/securenotehub-3166-52d170c5/notes_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

