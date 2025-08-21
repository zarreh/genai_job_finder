#!/usr/bin/env python3
"""
Launcher script for the GenAI Job Finder Streamlit application
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Launch the Streamlit application"""
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    app_path = script_dir / "app.py"
    
    # Check if the app file exists
    if not app_path.exists():
        print(f"Error: app.py not found at {app_path}")
        sys.exit(1)
    
    # Launch Streamlit
    try:
        print("Starting GenAI Job Finder...")
        print(f"App will be available at: http://localhost:8501")
        print("Press Ctrl+C to stop the application")
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(app_path),
            "--server.address", "localhost",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\nApplication stopped.")
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
