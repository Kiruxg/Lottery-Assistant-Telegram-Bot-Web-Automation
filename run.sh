#!/bin/bash
# Lottery Assistant - Linux/Mac Shell Script
# Quick launcher for common tasks

case "$1" in
    test)
        echo "Running system tests..."
        python main.py test
        ;;
    check)
        echo "Running jackpot check..."
        python main.py check
        ;;
    schedule)
        echo "Starting scheduled monitoring..."
        python main.py schedule
        ;;
    setup)
        echo "Running setup..."
        python setup.py
        ;;
    *)
        echo "Usage:"
        echo "  ./run.sh test      - Test all components"
        echo "  ./run.sh check     - Run a single check"
        echo "  ./run.sh schedule  - Start scheduled monitoring"
        echo "  ./run.sh setup     - Run setup checks"
        exit 1
        ;;
esac
