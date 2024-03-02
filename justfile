#!/usr/bin/env just --justfile
# Just is a replacement for Make. It's focused on running project-specific instead
# of building C code, so it's easier to work with. It's available in almost all
# package libraries, e.g., `brew install just`.
#
# Quick Start: https://just.systems/man/en/chapter_18.html

default:
    @just --list

# Ensure that sam is installed
setup-poetry:
    poetry install

# Setup pre-commit hooks
setup-pre-commit:
    pre-commit install

# Run the minimal setup commands required for CI
setup-ci: setup-poetry setup-pre-commit

# Must be run after you've followed the "Setup" instruction in README.md.
setup: setup-ci

# Develop the web server
web-dev *args:
    poetry run uvicorn webserver:app --reload

# Check project for style problems or errors
lint:
    pre-commit run --all-files

lint-python: lint-python-type lint-python-poetry

lint-python-type:
    poetry run pyright

lint-python-poetry:
    poetry check
