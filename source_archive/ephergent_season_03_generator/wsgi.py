"""WSGI entrypoint for Gunicorn.
Creates the Flask app using the production configuration.
"""
from ephergent_generator import create_app

# Create the app with 'production' config. Gunicorn will import this module and look for `app`.
app = create_app('production')

