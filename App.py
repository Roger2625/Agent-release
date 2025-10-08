import tkinter as tk
from dotenv import load_dotenv
import os

# Absolute path to .env
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

from login import SimpleApp

from dashboard import start_dashboard

def handle_data(data, base_url):
    try:
        start_dashboard(data,base_url)
    except tk.TclError as e:
        print(f"Tkinter closed unexpectedly: {e}")

# Launch the app and pass the handler
SimpleApp(callback=handle_data)