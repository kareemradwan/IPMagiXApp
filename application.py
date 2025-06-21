# Import the app object from app.py
from app import app

# This file is required by Azure App Service
# Azure will look for an application.py file with an app object
if __name__ == "__main__":
    app.run()
