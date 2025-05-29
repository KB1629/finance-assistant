import os
import sys

# Add the project root to path to enable imports
sys.path.insert(0, os.path.abspath("."))

# Import and run the main Streamlit app
from finance_assistant.streamlit_app.main import main

if __name__ == "__main__":
    main() 