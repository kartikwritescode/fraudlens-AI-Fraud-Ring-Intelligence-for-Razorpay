"""
CLI entrypoint alias for generator.py
Supports: python -m services.simulator.generate --transactions 50000 --rings 10 --seed 42
"""

from services.simulator.generator import main

if __name__ == "__main__":
    main()
