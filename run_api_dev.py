#!/usr/bin/env python3
"""
Development API runner with SQLite database
"""
import os
import sys
import subprocess

# Set environment variables for development
os.environ['DATABASE_URL'] = 'sqlite:///./quick_commerce_deals.db'
os.environ['USE_SQLITE'] = 'true'
os.environ['SKIP_REDIS'] = 'true'
os.environ['ENVIRONMENT'] = 'development'

def setup_database():
    """Setup SQLite database if it doesn't exist"""
    if not os.path.exists('quick_commerce_deals.db'):
        print("Setting up development database...")
        try:
            subprocess.run([sys.executable, 'setup_dev_database.py'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to setup database: {e}")
            return False
    else:
        print("Database already exists, skipping setup...")
    return True

def run_api():
    """Run the FastAPI application"""
    print("Starting Quick Commerce Deals API in development mode...")
    print("Database: SQLite")
    print("Redis: Disabled")
    print("URL: http://localhost:8000")
    print("-" * 50)
    
    try:
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except ImportError:
        print("uvicorn not found, trying with python -m uvicorn")
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])

if __name__ == "__main__":
    if setup_database():
        run_api()
    else:
        print("Failed to setup database. Exiting.")
        sys.exit(1)