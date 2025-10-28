"""
Initialize database - create all tables
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.config.database import init_db

if __name__ == "__main__":
    print("🗄️  Initializing database...")
    init_db()
    print("✅ Database initialized successfully!")
