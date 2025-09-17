import logging
from main import run_tribal_simulation, setup_logging

if __name__ == "__main__":
    setup_logging(logging.INFO)
    run_tribal_simulation(30)
