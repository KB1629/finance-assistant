#!/usr/bin/env python3
"""Run the Finance Assistant Streamlit app."""

import subprocess
import sys
from pathlib import Path

def main():
    """Run the Streamlit application."""
    app_path = Path(__file__).parent / "finance_assistant" / "streamlit_app" / "main.py"
    
    if not app_path.exists():
        print(f"❌ App file not found: {app_path}")
        sys.exit(1)
    
    print("🚀 Starting Finance Assistant...")
    print(f"📁 App location: {app_path}")
    print("🌐 Will open in your browser at http://localhost:8501")
    print("\n⌨️  Press Ctrl+C to stop\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(app_path),
            "--server.address", "localhost",
            "--server.port", "8501"
        ], check=True)
    except KeyboardInterrupt:
        print("\n✅ Finance Assistant stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 