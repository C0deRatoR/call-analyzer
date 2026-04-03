.PHONY: help setup test lint run

help:
	@echo "Makefile commands:"
	@echo "  make setup   - Install dependencies"
	@echo "  make test    - Run pytest suite"
	@echo "  make lint    - Run flake8 and mypy"
	@echo "  make run     - Run the Flask server"

setup:
	pip install -r requirements.txt

test:
	pytest tests/ -v --cov=src

lint:
	flake8 src/ tests/ --ignore=E501,W293,E221,E302,E402,W291,E128,E241,E226,W292,E305,E127
	mypy src/ --ignore-missing-imports

run:
	python src/app.py
