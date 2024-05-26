import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import create_app from the carquest package
from carquest import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
