# AI Sandbox Makefile

.PHONY: help install run test clean format lint docs

# Default target
help:
	@echo "AI Sandbox - Available commands:"
	@echo "  install    - Install Python dependencies"
	@echo "  run        - Run the interactive simulation"
	@echo "  core       - Run core simulation (1000 ticks)"
	@echo "  train-pop  - Train population RL agent"
	@echo "  train-dip  - Train diplomacy RL agent"
	@echo "  test       - Run test suite"
	@echo "  format     - Format code with black"
	@echo "  lint       - Run linting checks"
	@echo "  clean      - Clean up generated files"
	@echo "  docs       - View documentation"

# Install dependencies
install:
	pip install -r requirements.txt

# Run commands
run:
	python main.py

core:
	python main.py core 1000

# Training commands
train-pop:
	python train_rl_agent.py --target-pop 300 --episodes 100

train-dip:
	python train_diplomacy_rl.py --episodes 50 --max-ticks 200

# Testing and quality
test:
	python -m pytest tests/ -v

format:
	black .

lint:
	flake8 . --max-line-length=88 --extend-ignore=E203,W503
	mypy . --ignore-missing-imports

# Cleanup
clean:
	rm -rf __pycache__/
	rm -rf */__pycache__/
	rm -rf .mypy_cache/
	rm -rf .pytest_cache/
	rm -rf artifacts/plots/*.png
	rm -rf artifacts/data/*.json
	rm -rf artifacts/data/*.csv
	rm -rf world_data/
	rm -rf persistence/
	rm -f *.log

# Documentation
docs:
	@echo "Opening documentation..."
	@start README.md || open README.md || xdg-open README.md