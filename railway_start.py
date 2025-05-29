#!/usr/bin/env python3
"""
Railway startup script for Finance Assistant
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the Streamlit app for Railway deployment"""
    
    # Set Railway-specific environment variables
    os.environ['STREAMLIT_SERVER_PORT'] = os.environ.get('PORT', '8501')
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
    os.environ['STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION'] = 'false'
    
    # Use the streamlit_app.py in the root directory
    app_path = Path(__file__).parent / "streamlit_app.py"
    
    if not app_path.exists():
        print(f"❌ Error: {app_path} not found!")
        sys.exit(1)
    
    print(f"🚀 Starting Finance Assistant on Railway...")
    print(f"📁 App location: {app_path}")
    print(f"🌐 Port: {os.environ.get('PORT', '8501')}")
    
    # Start Streamlit
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', str(app_path),
        '--server.address', '0.0.0.0',
        '--server.port', os.environ.get('PORT', '8501'),
        '--server.headless', 'true',
        '--browser.gatherUsageStats', 'false',
        '--server.enableCORS', 'false',
        '--server.enableXsrfProtection', 'false'
    ]
    
    print(f"🔧 Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 