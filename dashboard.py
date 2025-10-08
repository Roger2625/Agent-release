# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, font, scrolledtext 
from PIL import Image, ImageTk, ImageDraw, ImageFont
import math
import time # Needed for debouncing via 'after'
import random
import requests
import subprocess
import threading
import sys
import os
import getpass
import socket
from dotenv import load_dotenv
load_dotenv()
from tkinter import filedialog, messagebox
import platform
import re
import json
import functools
import shutil
import tkinter.simpledialog
import login
import logging
from datetime import datetime


# --- Matplotlib Imports ---
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# ------------------------

# --- Download Imports ---
import io
import zipfile
from io import BytesIO
import threading
from zipfile import ZipFile
# ------------------------

# --chart--------------
from collections import Counter
from datetime import datetime
# ---------

# ---GTK for terminal-------
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
from gi.repository import Gtk, Vte, GLib, Gdk,GObject
import threading
import pexpect

from terminal_window import run_terminal_app

# --- Logging Setup ---
def setup_logging():
    """Setup logging to save debug logs to ~/.wingzai/logs/ with timestamps"""
    try:
        # Create logs directory
        logs_dir = os.path.expanduser("~/.wingzai/logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"dashboard_{timestamp}.log"
        log_path = os.path.join(logs_dir, log_filename)
        
        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)  # Also log to console
            ]
        )
        
        # Create logger for dashboard
        logger = logging.getLogger('dashboard')
        logger.info(f"Dashboard logging initialized. Log file: {log_path}")
        
        return logger
    except Exception as e:
        print(f"Failed to setup logging: {e}")
        return None

# Initialize logging
dashboard_logger = setup_logging()

def log_debug(message):
    """Log debug message to both file and console"""
    if dashboard_logger:
        dashboard_logger.debug(message)
    else:
        print(f"DEBUG: {message}")

def log_info(message):
    """Log info message to both file and console"""
    if dashboard_logger:
        dashboard_logger.info(message)
    else:
        print(f"INFO: {message}")

def log_warning(message):
    """Log warning message to both file and console"""
    if dashboard_logger:
        dashboard_logger.warning(message)
    else:
        print(f"WARNING: {message}")

def log_error(message):
    """Log error message to both file and console"""
    if dashboard_logger:
        dashboard_logger.error(message)
    else:
        print(f"ERROR: {message}")

# --- Utility function for safe folder names ---
def safe_name(name):
    import re
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', str(name))

def set_testcase_inprogress(agent_data, project_id, testcase_id):
    """
    Set the status of the given test case (subtype) to 'in progress' for the specified project.
    Returns True if the status was updated, False otherwise.
    """
    updated = False
    for project in agent_data.get("data", []):
        if project.get("project_id") == project_id:
            for subtype in project.get("subtypes_status", []):
                if subtype.get("id") == testcase_id:
                    if subtype.get("status", "").strip().lower() != "in progress":
                        subtype["status"] = "in progress"
                        updated = True
    return updated

def load_config():
    """
    Load configuration from 1.json file.
    Returns a dictionary with configuration data or default values if file doesn't exist.
    """
    # Try multiple possible locations for 1.json
    possible_paths = [
        os.path.expanduser('~/1.json'),  # Home directory (primary for .deb installation)
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '1.json'),  # Local directory (fallback)
    ]
    
    default_config = {
        "base_url": "https://wingzai.deltaphi.in/",
        "token": "",
        "testcase_id": "",
        "testcase_name": "",
        "machine_ip": "",
        "target_ip": "",
        "ssh_username": "",
        "ssh_password": ""
    }
    
    for config_file_path in possible_paths:
        try:
            if os.path.exists(config_file_path):
                with open(config_file_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    log_debug(f"Loaded config from: {config_file_path}")
                    return config
        except Exception as e:
            log_warning(f"Failed to load config from {config_file_path}: {e}")
            continue
    
    log_warning("Config file not found in any expected location, using default values")
    return default_config

def start_dashboard(agent_data,base_url):
    agent_id = agent_data.get("agentid")
    print("agent_data: ", agent_data)
    agent_name = agent_data.get("agent_name", "Agent")

    # Calculate To Do, In Progress, Completed counts before using them in the dashboard layout
    total_todo = 0
    total_in_progress = 0
    total_done = 0
    for project in agent_data.get("data", []):  
        for subtype in project.get("subtypes_status", []):
            status = subtype.get("status", "").strip().lower()
            if status in ("to-do", "todo"):
                total_todo += 1
            elif status in ("in progress", "progress"):
                total_in_progress += 1
            elif status in ("done", "completed"):
                total_done += 1

    done_percentage = int((total_done / (total_todo + total_in_progress + total_done)) * 100) if (total_todo + total_in_progress + total_done) > 0 else 0

    projects_data = []

    for item in agent_data.get("data", []):
        name = item.get("project_name", "Untitled Project")
        lead = item.get("authorizer", "Unknown")
        # Normalize status for dashboard bar calculation
        raw_status = item.get("progress", "Unknown").strip().lower()
        if raw_status in ("not yet started", "pending", "to-do", "todo"):
            status = "Not Yet Started"
        elif raw_status in ("in progress", "progress"):
            status = "In Progress"
        elif raw_status in ("done", "completed"):
            status = "Completed"
        else:
            status = "Not Yet Started"  # Default/fallback
        dut = item.get("dut_name", "Unknown")
        project_id = item.get("project_id")
        reporting_manager = item.get("reporting_manager", "Unknown")
        subtypes = item.get("subtypes_status", [])
        total = len(subtypes)
        done_count = sum(1 for s in subtypes if s.get("status", "").strip().lower() in ("done", "completed"))
        progress_val = int((done_count / total) * 100) if total > 0 else 0
        projects_data.append((name, lead, status, dut, reporting_manager, progress_val, subtypes, project_id, agent_id))



        # projects_data.append((name, "placeholder.com", status, dut, progress_val, reporting_manager))


    
    # --- Constants (Define colors and simple tuple fonts first) ---

    # --- NEW THEME BASED ON PROVIDED IMAGES ---

    # Backgrounds from Image 1 (Mytasky - Dark Theme)
    COLOR_SIDEBAR_BG = "#080808"        # Very dark grey for sidebar
    COLOR_CONTENT_BG = "#1A1A1A"        # Slightly darker grey for main content area

    # Panels, Charts, Text from Image 2 (Licenses/Environment - Dark Theme)
    COLOR_PANEL_BG = "#2C2C2E"          # Dark grey for panels/cards
    COLOR_PRIMARY = '#B95A30'           # Vibrant orange/brown (Activated Licenses, Standard Plan)
    COLOR_SECONDARY = '#2C2C2E'         # Muted blue (Pending Licenses, Pro Plan)
    COLOR_SECONDARY_TRIANGLE = '#4E7797'  
    COLOR_TERTIARY_PURPLE = '#8A6191'    # Purple (Enterprise Plan, Expiring) - Added for consistency
    COLOR_TEXT_LIGHT = "#FFFFFF"        # White/Very light grey for main text
    COLOR_TEXT_MUTED_DARK_BG = "#B0B0B0" # Muted light grey for secondary text on dark background
    COLOR_TEXT_DARK = "#E0E0E0"         # Fallback light color (Original DARK is now irrelevant on dark bg)
    COLOR_CHART_BG_MUTED = "#404040"     # Darker grey for donut background arc

    # Matplotlib Colors for Dark Theme
    MPL_FILL_COLOR_EXAMPLE = '#555555' # Darker grey fill
    MPL_MARKER_COLORS = [COLOR_PRIMARY, COLOR_SECONDARY, COLOR_TERTIARY_PURPLE, '#2ECC71', '#F1C40F'] # Orange, Blue, Purple, Green, Yellow
    MPL_MARKER_EDGE_COLOR = '#DDDDDD'   # Light grey edge for visibility
    MPL_GRID_COLOR = "#444444"          # Faint light grey grid lines
    MPL_SPINE_COLOR = '#666666'         # Faint light grey axis spines
    MPL_TICK_COLOR = '#B0B0B0'          # Light grey ticks (same as muted text)
    MPL_LABEL_COLOR = COLOR_TEXT_MUTED_DARK_BG # Light grey labels

    # Table Colors (Dark Theme Adaptation)
    COLOR_BORDER_LIGHT = '#444444'      # Dark theme borders
    COLOR_BORDER_MEDIUM = '#555555'     # Dark theme medium borders
    COLOR_HOVER_BG = "#3C3C3E"          # Slightly lighter dark grey for hover
    COLOR_HEADER_BG = '#353537'         # Slightly distinct dark header background
    COLOR_TEXT_HEADER = '#E5E7EB'       # Light header text
    COLOR_TEXT_SECONDARY_TABLE = '#D1D5DB' # Light secondary table text
    COLOR_TEXT_TERTIARY_TABLE = '#9CA3AF'  # Muted light tertiary table text

    # Status Colors (Dark Backgrounds, Light Text)
    COLOR_STATUS_CUSTOMER_BG = '#064E3B' # Dark Green BG
    COLOR_STATUS_CUSTOMER_FG = '#A7F3D0' # Light Green Text
    COLOR_STATUS_CHURNED_BG = '#374151'   # Dark Grey BG
    COLOR_STATUS_CHURNED_FG = '#D1D5DB'   # Light Grey Text
    COLOR_STATUS_INPROGRESS_BG = '#7C2D12' # Dark Orange BG
    COLOR_STATUS_INPROGRESS_FG = '#FCD9B6' # Light Orange Text
    COLOR_STATUS_COMPLETED_BG = COLOR_STATUS_CUSTOMER_BG # Dark Green BG
    COLOR_STATUS_COMPLETED_FG = COLOR_STATUS_CUSTOMER_FG # Light Green Text
    COLOR_STATUS_PENDING_BG = '#1E3A8A'    # Dark Blue BG
    COLOR_STATUS_PENDING_FG = '#BFDBFE'    # Light Blue Text
    COLOR_STATUS_BLOCKED_BG = '#7F1D1D'    # Dark Red BG
    COLOR_STATUS_BLOCKED_FG = '#FECACA'    # Light Red Text
    COLOR_STATUS_DEFAULT_BG = COLOR_STATUS_CHURNED_BG # Dark Grey BG
    COLOR_STATUS_DEFAULT_FG = COLOR_STATUS_CHURNED_FG # Light Grey Text

    # Progress Bar Colors (Dark Theme)
    COLOR_PROGRESS_BG = '#4B5563'       # Darker grey base
    COLOR_PROGRESS_FILL = '#3B82F6'      # Keep the bright blue fill

    # Kanban Colors (Dark Theme Adaptation)
    KANBAN_COLUMN_BG = "#333335"        # Base dark grey for column content area
    KANBAN_COLUMN_HOVER_BG = "#404040"   # Slightly lighter for hover
    KANBAN_TASK_BG = COLOR_PANEL_BG     # Use panel background for tasks
    KANBAN_TASK_BORDER = "#444444"      # Dark theme border
    KANBAN_TASK_HOVER_BG = "#38383A"      # Slightly lighter than task bg for hover
    KANBAN_TEXT_HEADER = COLOR_TEXT_LIGHT # White header text
    KANBAN_TEXT_TASK = "#E0E0E0"        # Light grey task text
    KANBAN_DRAG_BORDER = '#6EE7B7'      # Use a bright accent for drag border (like image 1 accent)

    # Kanban Header Backgrounds (Darker Shades)
    KANBAN_HEADER_TODO_BG = "#7F1D1D"       # Dark Red/Maroon
    KANBAN_HEADER_INPROGRESS_BG = "#1E40AF" # Dark Blue
    KANBAN_HEADER_COMPLETED_BG = "#065F46"  # Dark Green

    # --- Main Application Window ---
    root = tk.Tk()
    root.title("Dashboard")
    root.geometry("1000x600")  # Fallback size
    root.configure(bg=COLOR_CONTENT_BG) # Use dark content background
    
    # Make window fullscreen and remove gaps
    if platform.system() == "Windows":
        root.state('zoomed')
    elif platform.system() == "Linux":
        try:
            root.attributes('-zoomed', True)
        except Exception:
            root.attributes('-fullscreen', True)
    else:
        # fallback for other OS
        pass
    # --- END NEW THEME ---

    # Simple tuple fonts (safe to define early)
    FONT_BOLD = ("Arial", 15, "bold")
    FONT_NORMAL = ("Arial", 9)
    FONT_LARGE = ("Arial", 36, "bold")
    FONT_MEDIUM_BOLD = ("Arial", 12, "bold")
    FONT_SMALL = ("Arial", 8)
    FONT_ICON_PLACEHOLDER = ("Arial", 36, "bold")

    ANIMATION_DELAY = 25
    ANIMATION_STEPS = 40
    DEBOUNCE_DELAY = 150 # ms delay for resize redraw

    # --- Font Definitions (using tkinter.font) ---
    # NOW it's safe to use font.families() and font.Font()
    _FONT_FAMILY_PRIMARY_TEMP = "Nourd" # Start with Nourd font
    try:
        _preferred_font = "Nourd"
        if hasattr(font, 'families') and callable(font.families):
            available_families = font.families()
            if _preferred_font in available_families:
                _FONT_FAMILY_PRIMARY_TEMP = _preferred_font
            else:
                # Fallback to Arial if Nourd is not available
                _FONT_FAMILY_PRIMARY_TEMP = "Arial"
        FONT_FAMILY_PRIMARY = _FONT_FAMILY_PRIMARY_TEMP
    except tk.TclError as e:
        print(f"Warning: TclError checking font families ({e}), falling back to Arial.")
        FONT_FAMILY_PRIMARY = "Arial"
    except Exception as e:
        print(f"Warning: Unexpected error checking font families ({e}), falling back to Arial.")
        FONT_FAMILY_PRIMARY = "Arial"

    try:
        if 'FONT_FAMILY_PRIMARY' not in locals() or not FONT_FAMILY_PRIMARY:
            print("Critical Error: FONT_FAMILY_PRIMARY not set. Defaulting all fonts to Arial.")
            FONT_FAMILY_PRIMARY = "Arial"

        TABLE_FONT_HEADER = font.Font(family=FONT_FAMILY_PRIMARY, size=10, weight="bold")
        TABLE_FONT_PROJECT_NAME = font.Font(family=FONT_FAMILY_PRIMARY, size=11, weight="bold")
        TABLE_FONT_BODY_BOLD = font.Font(family=FONT_FAMILY_PRIMARY, size=10, weight="bold") # For Job Name
        TABLE_FONT_BODY_REGULAR = font.Font(family=FONT_FAMILY_PRIMARY, size=10)
        TABLE_FONT_BODY_SMALL = font.Font(family=FONT_FAMILY_PRIMARY, size=9)
        TABLE_FONT_STATUS = font.Font(family=FONT_FAMILY_PRIMARY, size=9, weight="bold")
        KANBAN_FONT_HEADER = font.Font(family=FONT_FAMILY_PRIMARY, size=11, weight="bold")
        KANBAN_FONT_TASK = font.Font(family=FONT_FAMILY_PRIMARY, size=10)

    except tk.TclError as e:
        print(f"Error creating font objects: {e}. Using default tuple fonts.")
        FONT_FAMILY_PRIMARY = "Arial"
        TABLE_FONT_HEADER = (FONT_FAMILY_PRIMARY, 10, "bold")
        TABLE_FONT_PROJECT_NAME = (FONT_FAMILY_PRIMARY, 11, "bold")
        TABLE_FONT_BODY_BOLD = (FONT_FAMILY_PRIMARY, 10, "bold")
        TABLE_FONT_BODY_REGULAR = (FONT_FAMILY_PRIMARY, 10)
        TABLE_FONT_BODY_SMALL = (FONT_FAMILY_PRIMARY, 9)
        TABLE_FONT_STATUS = (FONT_FAMILY_PRIMARY, 9, "bold")
        KANBAN_FONT_HEADER = (FONT_FAMILY_PRIMARY, 11, "bold")
        KANBAN_FONT_TASK = (FONT_FAMILY_PRIMARY, 10)
    # --- End Font Definitions ---

    # --- Animation State & Resize Variables ---
    donut_animation_id = None
    area_chart_resize_timer_id = None

    # --- Page Management ---
    pages = {}
    sidebar_buttons = {} # To store references for styling

    # --- Helper function to create styled panels ---
    def create_panel(parent, row, col, rowspan=1, colspan=1):
        # Use dark panel background
        panel = tk.Frame(parent, bg=COLOR_PANEL_BG, relief=tk.FLAT, borderwidth=0, padx=20, pady=15)
        panel.grid(row=row, column=col, rowspan=rowspan, columnspan=colspan, sticky="nsew", padx=8, pady=8)
        return panel

    # --- Helper function: Draw Rounded Rectangle (from new table code) ---
    def draw_rounded_rectangle(canvas, x1, y1, x2, y2, radius, **kwargs):
        """Draws a rounded rectangle on the canvas."""
        try:
            coords = [x1, y1, x2, y2, radius]
            if not all(isinstance(c, (int, float)) and math.isfinite(c) for c in coords):
                return canvas.create_rectangle(x1, y1, x2, y2, **{k: v for k, v in kwargs.items() if k != 'smooth'})
            radius = min(radius, abs(x2-x1)/2, abs(y2-y1)/2)
            if radius < 0: radius = 0
            points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, x2, y1,
                    x2, y1+radius, x2, y1+radius, x2, y2-radius, x2, y2-radius, x2, y2,
                    x2-radius, y2, x2-radius, y2, x1+radius, y2, x1+radius, y2, x1, y2,
                    x1, y2-radius, x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1]
            points = [p for p in points if isinstance(p, (int, float)) and math.isfinite(p)]
            if len(points) < 6:
                return canvas.create_rectangle(x1, y1, x2, y2, **{k: v for k, v in kwargs.items() if k != 'smooth'})
            smooth_val = True if radius > 0 else False
            return canvas.create_polygon(points, **kwargs, smooth=smooth_val)
        except tk.TclError as e:
            print(f"TclError drawing rounded rectangle: {e}. Falling back.")
            return canvas.create_rectangle(x1, y1, x2, y2, **{k: v for k, v in kwargs.items() if k != 'smooth'})
        except Exception as e:
            print(f"Error drawing rounded rectangle: {e}. Falling back.")
            return canvas.create_rectangle(x1, y1, x2, y2, **{k: v for k, v in kwargs.items() if k != 'smooth'})



    sidebar_buttons = {}  # <-- move this above
    pages = {}            # <-- move this above

    # --- Page Switching Function ---
    def switch_page(page_name, **kwargs):
        nonlocal pages, sidebar_buttons

        # Update sidebar button styling
        for name, button in sidebar_buttons.items():
            if button.winfo_exists():
                if name == page_name:
                    button.config(bg=COLOR_PRIMARY) # Active uses Primary Orange
                else:
                    button.config(bg=COLOR_SIDEBAR_BG) # Inactive uses Sidebar Dark

        # Special handling for Report and Project
        if page_name == "Report":
            report_page = pages.get("Report")
            if report_page:
                report_page._show_project_list()
        if page_name == "Project":
            project_page = pages.get("Project")
            if project_page and hasattr(project_page, 'trigger_redraw'):
                project_page.trigger_redraw()

        # Handle TestCases page specifics (loading data)
        if page_name == "TestCases":
            test_cases_page = pages.get("TestCases")
            if test_cases_page:
                if test_cases_page.winfo_exists():
                    # If no arguments provided, reload the last known project data
                    project_name = kwargs.get("project_name", getattr(test_cases_page, 'project_name', "Unknown Project"))
                    test_cases_data = kwargs.get("test_cases_data", getattr(test_cases_page, 'test_cases_data', {}))
                    project_id = kwargs.get("project_id", getattr(test_cases_page, 'project_id', None))
                    agent_id = kwargs.get("agent_id", getattr(test_cases_page, 'agent_id', None))
                    subtype_id_map = kwargs.get("subtype_id_map", getattr(test_cases_page, 'subtype_id_map', {}))

                    test_cases_page.load_project(
                        project_name,
                        test_cases_data,
                        project_id=project_id,
                        agent_id=agent_id,
                        subtype_id_map=subtype_id_map
                    )
                    test_cases_page.tkraise()
                else:
                    messagebox.showerror("Error", "TestCases page widget no longer exists.")
            else:
                messagebox.showerror("Error", "TestCases page not found in registry.")
            return

        # Raise the selected page
        page = pages.get(page_name)
        if page:
            if page.winfo_exists():
                if hasattr(page, 'trigger_redraw'):
                    page.trigger_redraw()
                page.tkraise()
            else:
                messagebox.showerror("Error", f"Page '{page_name}' widget no longer exists.")
        else:
            messagebox.showerror("Error", f"Page '{page_name}' not found in registry.")

    # --- Logout Function ---
    def logout():
        if messagebox.askokcancel("Logout", "Are you sure you want to sign out?"):
            try:
                global _draw_scheduled, donut_animation_id
                global area_chart_resize_timer_id

                if '_draw_scheduled' in globals() and _draw_scheduled:
                    root.after_cancel(_draw_scheduled)
                    _draw_scheduled = None

                for var_name in [
                    'donut_animation_id',
                    'area_chart_resize_timer_id'
                ]:
                    if var_name in globals():
                        root.after_cancel(globals()[var_name])

            except Exception as e:
                print(f"Error cancelling scheduled tasks: {e}")
            root.destroy()

    # --- Main Layout Frames ---
    sidebar_frame = tk.Frame(root, bg=COLOR_SIDEBAR_BG, width=250) # Dark Sidebar BG
    sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
    sidebar_frame.pack_propagate(False)

    content_frame = tk.Frame(root, bg=COLOR_CONTENT_BG) # Dark Content BG
    content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    # Configure root to expand content frame to fill all available space
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    # --- Sidebar Widgets ---
    profile_frame = tk.Frame(sidebar_frame, bg=COLOR_SIDEBAR_BG, pady=25)
    profile_frame.pack(fill=tk.X)

   
    def get_random_color():
        r = random.randint(60, 200)
        g = random.randint(60, 200)
        b = random.randint(60, 200)
        return (r, g, b)

    def rgb_to_hex(rgb_tuple):
        return '#%02x%02x%02x' % rgb_tuple

    initials = "".join([word[0] for word in agent_name.strip().split()[:2]]).upper() or "A"
    bg_color = '#888888'  # Fixed gray color for avatar background

    def render_avatar_square():
        try:
            avatar_frame = tk.Frame(profile_frame, width=60, height=60, bg=bg_color, bd=0)
            avatar_frame.pack_propagate(False)
            avatar_frame.pack(pady=(0, 15)) 


            label = tk.Label(avatar_frame, text=initials, bg=bg_color, fg=COLOR_TEXT_LIGHT,
                            font=("Arial", 18, "bold"))
            label.pack(expand=True, fill='both')
        except Exception as e:
            print(f"Error rendering square avatar: {e}")


    render_avatar_square()

    # --- Now add the agent labels below the avatar ---
    # name_label = tk.Label(profile_frame, text="Agent", bg=COLOR_SIDEBAR_BG, fg=COLOR_TEXT_LIGHT, font=FONT_MEDIUM_BOLD)
    # name_label.pack(pady=(0, 0))

    sub_name_label = tk.Label(profile_frame, text=agent_name.title(), bg=COLOR_SIDEBAR_BG, fg=COLOR_PRIMARY, font=FONT_MEDIUM_BOLD)
    sub_name_label.pack()

    # Separator and nav
    separator = tk.Frame(profile_frame, bg=COLOR_TEXT_MUTED_DARK_BG, height=1)
    separator.pack(pady=20, padx=20, fill=tk.X)

    nav_frame = tk.Frame(sidebar_frame, bg=COLOR_SIDEBAR_BG)
    nav_frame.pack(fill=tk.X, padx=20, pady=(10, 0))

    nav_items = [
        {"text": "Dashboard", "active": True},
        {"text": "Project", "active": False},
        {"text": "Job", "active": False},
        {"text": "Report", "active": False},
        {"text": "Suites", "active": False},
    ]

    for item in nav_items:
        btn = tk.Button(
            nav_frame,
            text=item["text"],
            bg=COLOR_PRIMARY if item["active"] else COLOR_SIDEBAR_BG,
            fg=COLOR_TEXT_LIGHT, # Light text always
            font=FONT_MEDIUM_BOLD,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            padx=20,
            pady=10,
            anchor='w',
            activebackground=COLOR_SECONDARY, # Use Secondary Blue for hover/active click
            activeforeground=COLOR_TEXT_LIGHT,
            command=lambda p=item["text"]: switch_page(p)
        )
        btn.pack(fill=tk.X, pady=(0, 5))
        sidebar_buttons[item["text"]] = btn

   # --- Content Area Widgets ---
    top_bar_frame = tk.Frame(content_frame, bg=COLOR_SIDEBAR_BG, height=60)
    top_bar_frame.pack(fill=tk.X)
    top_bar_frame.pack_propagate(False)

    signout_button = tk.Button(
        top_bar_frame,
        text="Log Out",
        bg=COLOR_PRIMARY,
        fg=COLOR_TEXT_LIGHT,
        font=FONT_MEDIUM_BOLD,
        relief=tk.FLAT,
        bd=0,
        highlightthickness=0,
        activebackground=COLOR_SECONDARY,
        activeforeground=COLOR_TEXT_LIGHT,
        padx=20,
        pady=8,
        command=logout
    )
    signout_button.pack(side=tk.RIGHT, padx=20, pady=10)


    def refresh_dashboard():
        try:
            with open('client.conf.json', 'r') as f:
                config = json.load(f)
            base_url = config.get('server_url')
            token = config.get('token')
            get_data_endpoint = "/api/connection/get_data"
            config_url = base_url + get_data_endpoint
            request_data = {}
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.post(config_url, json=request_data, headers=headers)
            
            if response.status_code == 200:
                new_agent_data = response.json()
                update_status_boxes(new_agent_data)
                update_project_page(new_agent_data)
                update_job_page(new_agent_data)
                update_charts(new_agent_data)
                update_tree_page(new_agent_data)

                # ✅ Save refreshed token if present
                new_token = new_agent_data.get("token")
                if new_token:
                    config = {
                        "server_url": base_url,
                        "token": new_token
                    }
                    with open('client.conf.json', 'w') as file:
                        json.dump(config, file)
                    # Update token in TestCasesPage to prevent stale token issues
                    update_test_cases_page_token(new_token)
            else:
                messagebox.showerror("Refresh Error", f"Server returned status code {response.status_code}: {response.text}")
        except Exception as e:
            messagebox.showerror("Refresh Error", str(e))

        # --- Helper: Update status boxes in place ---
    

        # --- Helper: Update status boxes in place ---
    def update_status_boxes(new_agent_data):
        total_todo = 0
        total_in_progress = 0
        total_done = 0
        print("[DEBUG] update_status_boxes: new_agent_data:", new_agent_data)
        for project in new_agent_data.get("data", []):
            for subtype in project.get("subtypes_status", []):
                status = subtype.get("status", "").strip().lower()
                print(f"[DEBUG] Subtype status: {status}")
                if status in ("to-do", "todo", "pending", "not yet started"):
                    total_todo += 1
                elif status in ("in progress", "progress"):
                    total_in_progress += 1
                elif status in ("done", "completed", "finished"):
                    total_done += 1
        print(f"[DEBUG] Status counts: Not Yet Started={total_todo}, In Progress={total_in_progress}, Completed={total_done}")
        new_counts = [total_todo, total_in_progress, total_done]
        for i, count in enumerate(new_counts):
            if i < len(status_count_labels):
                status_count_labels[i].config(text=str(count))

    # --- Helper: Update ProjectPage in place ---
    def update_project_page(new_agent_data):
        if "Project" in pages and hasattr(pages["Project"], "projects_data"):
            projects_data = []
            agent_id = new_agent_data.get("agentid")
            print("[DEBUG] update_project_page: new_agent_data:", new_agent_data)
            for item in new_agent_data.get("data", []):
                name = item.get("project_name", "Untitled Project")
                lead = item.get("authorizer", "Unknown")
                raw_status = item.get("progress", "Unknown").strip().lower()
                print(f"[DEBUG] Project: {name}, progress: {raw_status}")
                if raw_status in ("not yet started", "pending", "to-do", "todo"):
                    status = "Not Yet Started"
                elif raw_status in ("in progress", "progress"):
                    status = "In Progress"
                elif raw_status in ("done", "completed", "finished"):
                    status = "Completed"
                else:
                    status = "Not Yet Started"
                dut = item.get("dut_name", "Unknown")
                project_id = item.get("project_id")
                reporting_manager = item.get("reporting_manager", "Unknown")
                subtypes = item.get("subtypes_status", [])
                total = len(subtypes)
                done_count = sum(1 for s in subtypes if s.get("status", "").strip().lower() in ("done", "completed", "finished"))
                print(f"[DEBUG] Project: {name}, subtypes total: {total}, done_count: {done_count}")
                progress_val = int((done_count / total) * 100) if total > 0 else 0
                projects_data.append((name, lead, status, dut, reporting_manager, progress_val, subtypes, project_id, agent_id))
            pages["Project"].projects_data = projects_data
            if hasattr(pages["Project"], "_draw_table"):
                pages["Project"]._draw_table()

    def update_job_page(new_agent_data):
        if "Job" in pages and hasattr(pages["Job"], "load_jobs_from_agent_data"):
            pages["Job"].load_jobs_from_agent_data(new_agent_data)

    def update_charts(new_agent_data):
        # Redraw the main dashboard chart with new data
        # This assumes you have a reference to the chart widget/figure
        pass

    def update_tree_page(new_agent_data):
        """Update TreePage with new agent data"""
        if "Suites" in pages and hasattr(pages["Suites"], "update_agent_data"):
            pages["Suites"].update_agent_data(new_agent_data)

    def update_test_cases_page_token(new_token):
        """Update token in TestCasesPage to prevent stale token issues"""
        if "TestCases" in pages and hasattr(pages["TestCases"], "token"):
            pages["TestCases"].token = new_token
        # Also update token in other pages that use it
        if "Report" in pages and hasattr(pages["Report"], "token"):
            pages["Report"].token = new_token
        if "Download" in pages and hasattr(pages["Download"], "token"):
            pages["Download"].token = new_token
        if "Dashboard" in pages:
            dashboard_frame = pages["Dashboard"]
            # Find the chart panel and redraw it
            # (You may need to store a reference to the FigureCanvasTkAgg or chart widget for a more robust solution)
            # For now, simplest is to destroy and recreate the chart panel
            for widget in dashboard_frame.winfo_children():
                if isinstance(widget, tk.Frame) and any("chart" in str(child).lower() for child in widget.winfo_children()):
                    widget.destroy()
            # Recreate the chart panel with new data (reuse the code from initial dashboard setup)
            # You may want to refactor chart creation into a function for reuse
            # For now, you can call start_dashboard or a chart creation function if available
            # (No-op if not easily accessible)
            pass

    refresh_button = tk.Button(
        top_bar_frame,
        text="⟳ Refresh",
        bg=COLOR_PRIMARY,
        fg=COLOR_TEXT_LIGHT,
        font=FONT_MEDIUM_BOLD,
        relief=tk.FLAT,
        bd=0,
        highlightthickness=0,
        activebackground=COLOR_SECONDARY,
        activeforeground=COLOR_TEXT_LIGHT,
        padx=20,
        pady=8,
        command=refresh_dashboard
    )
    refresh_button.pack(side=tk.RIGHT, padx=(0, 0), pady=10)

    # --- Page Container ---
    page_container = tk.Frame(content_frame, bg=COLOR_CONTENT_BG)
    page_container.pack(fill=tk.BOTH, expand=True)
    page_container.grid_rowconfigure(0, weight=1)
    page_container.grid_columnconfigure(0, weight=1)

    # --- Dashboard Page Content ---
    dashboard_page_frame = tk.Frame(page_container, bg=COLOR_CONTENT_BG)
    dashboard_page_frame.grid(row=0, column=0, sticky="nsew")
    pages["Dashboard"] = dashboard_page_frame

    dashboard_page_frame.grid_rowconfigure(0, weight=1)  # Status boxes row
    dashboard_page_frame.grid_rowconfigure(1, weight=4)  # Chart + Progress row
    dashboard_page_frame.grid_columnconfigure(0, weight=2)
    dashboard_page_frame.grid_columnconfigure(1, weight=1)

    # --- Top Status Boxes ---
    status_frame = tk.Frame(dashboard_page_frame, bg=COLOR_CONTENT_BG)
    status_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(15, 15))
    status_frame.grid_columnconfigure(0, weight=1)
    status_frame.grid_columnconfigure(1, weight=1)
    status_frame.grid_columnconfigure(2, weight=1)

    status_data = [
        ("Not Yet Started", 0, "📝", "#3498db"),
        ("In Progress", 0, "⏳", "#f1c40f"),
        ("Completed", 0, "✅", "#2ecc71"),
    ]
    status_icons = {}
    status_icon_refs = []
    try:
        resample_method = Image.Resampling.LANCZOS
    except AttributeError:
        resample_method = getattr(Image, 'LANCZOS', getattr(Image, 'BICUBIC', getattr(Image, 'NEAREST', 0)))

    from PIL import ImageOps
    status_icon_files = {
        "✅": "icons/icons8-check-mark-32.png",
        "📝": "icons/icons8-to-do-list-32.png",
        "⏳": "icons/icons8-in-progress-32.png"
    }
    # Map each emoji to its color in the color scheme
    emoji_colors = {
        "📝": (52, 152, 219),   # #3498db
        "⏳": (241, 196, 15),   # #f1c40f
        "✅": (46, 204, 113),   # #2ecc71
    }
    base_dir = os.path.dirname(__file__)
    for emoji, rel_path in status_icon_files.items():
        img_path = os.path.join(base_dir, rel_path)
        img = Image.open(img_path).convert("RGBA").resize((32, 32), resample=resample_method)
        datas = img.getdata()
        color = emoji_colors.get(emoji, (255, 255, 255))
        newData = []
        for item in datas:
            if item[3] > 0:
                newData.append((*color, item[3]))
            else:
                newData.append(item)
        img.putdata(newData)
        icon = ImageTk.PhotoImage(img)
        status_icons[emoji] = icon
        status_icon_refs.append(icon)

    status_count_labels = []
    for i, (label, count, emoji, color) in enumerate(status_data):
        box = tk.Frame(status_frame, bg=COLOR_PANEL_BG, bd=1, relief=tk.FLAT, highlightthickness=0)
        box.grid(row=0, column=i, padx=10, pady=0, sticky="nsew")
        box.configure(height=80)
        box.grid_propagate(False)
        icon_label = tk.Label(box, image=status_icons[emoji], bg=COLOR_PANEL_BG)
        icon_label.pack(side=tk.LEFT, padx=(20, 15), pady=10)
        text_frame = tk.Frame(box, bg=COLOR_PANEL_BG)
        text_frame.pack(side=tk.LEFT, fill="both", expand=True)
        tk.Label(text_frame, text=label, font=("Arial", 12, "bold"), bg=COLOR_PANEL_BG, fg=color).pack(anchor="nw", padx=0, pady=(10, 2))
        count_label = tk.Label(text_frame, text=str(count), font=("Arial", 18, "bold"), bg=COLOR_PANEL_BG, fg=COLOR_TEXT_LIGHT)
        count_label.pack(anchor="sw", padx=0, pady=(0, 10))
        status_count_labels.append(count_label)

    # --- Clean update_status_counts_from_jobs ---
    def update_status_counts_from_jobs():
        jobs_data = []
        if "Job" in pages and hasattr(pages["Job"], "jobs_data"):
            jobs_data = pages["Job"].jobs_data
        total_todo = sum(1 for job in jobs_data if job[3] == "Not Yet Started")
        total_in_progress = sum(1 for job in jobs_data if job[3] == "In Progress")
        total_done = sum(1 for job in jobs_data if job[3] == "Completed")
        for i, (label, _, emoji, color) in enumerate(status_data):
            if label == "Not Yet Started":
                new_count = total_todo
            elif label == "In Progress":
                new_count = total_in_progress
            elif label == "Completed":
                new_count = total_done
            else:
                new_count = 0
            if i < len(status_count_labels):
                status_count_labels[i].config(text=str(new_count))

    # --- Main Content Area (Chart + Progress Bars) ---
    main_content_frame = tk.Frame(dashboard_page_frame, bg=COLOR_CONTENT_BG)
    main_content_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=(0, 20))
    main_content_frame.grid_rowconfigure(0, weight=1)
    main_content_frame.grid_columnconfigure(0, weight=1)
    main_content_frame.grid_columnconfigure(1, weight=1)

    # --- Left: Project Status by Status Line Chart ---
    chart_panel = tk.Frame(main_content_frame, bg=COLOR_PANEL_BG, bd=1, relief=tk.FLAT)
    chart_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=0)
    tk.Label(chart_panel, text="Project Status Overview", font=("Arial", 14, "bold"), bg=COLOR_PANEL_BG, fg=COLOR_TEXT_HEADER).pack(anchor="nw", padx=20, pady=(15, 5))

    # Use real data for the chart
    project_names = []
    todo_counts = []
    inprogress_counts = []
    completed_counts = []
    for item in agent_data.get("data", []):
        project_names.append(item.get("project_name", "Untitled"))
        subtypes = item.get("subtypes_status", [])
        # Use the same mapping as JobPage
        todo = sum(1 for s in subtypes if str(s.get("status", "")).strip().lower() in ("to-do", "todo", "pending", "not yet started"))
        inprogress = sum(1 for s in subtypes if str(s.get("status", "")).strip().lower() in ("in progress", "progress"))
        completed = sum(1 for s in subtypes if str(s.get("status", "")).strip().lower() in ("done", "completed"))
        todo_counts.append(todo)
        inprogress_counts.append(inprogress)
        completed_counts.append(completed)

    x = np.arange(len(project_names))
    fig = Figure(figsize=(5, 4), dpi=100, facecolor=COLOR_PANEL_BG)
    ax = fig.add_subplot(111)
    ax.set_facecolor(COLOR_PANEL_BG)

    # Plot each status as a line across all projects with specified colors
    todo_line, = ax.plot(x, todo_counts, color="#42A5F5", marker="o", label="To Do", linewidth=2)         # Blue
    completed_line, = ax.plot(x, completed_counts, color="#43A047", marker="o", label="Completed", linewidth=2) # Green
    inprogress_line, = ax.plot(x, inprogress_counts, color="#FBC02D", marker="o", label="In Progress", linewidth=2) # Yellow

    ax.set_xticks(x)
    ax.set_xticklabels(project_names, color=COLOR_TEXT_HEADER, fontsize=10)
    max_y = max(todo_counts + inprogress_counts + completed_counts) if (todo_counts + inprogress_counts + completed_counts) else 5
    ax.set_yticks(list(range(0, max_y+2)))
    ax.set_ylabel("Count", color=COLOR_TEXT_HEADER, fontsize=10)
    ax.tick_params(axis='x', colors=COLOR_TEXT_HEADER, labelsize=10)
    ax.tick_params(axis='y', colors=COLOR_TEXT_HEADER, labelsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(MPL_SPINE_COLOR)
    ax.spines['bottom'].set_color(MPL_SPINE_COLOR)
    ax.grid(True, axis='y', linestyle='--', alpha=0.3, color=MPL_GRID_COLOR)
    # Set legend text color to white
    legend = ax.legend(facecolor=COLOR_PANEL_BG, edgecolor=COLOR_PANEL_BG, fontsize=9, loc='upper left')
    for text in legend.get_texts():
        text.set_color(COLOR_TEXT_LIGHT)

    legend = ax.legend(facecolor=COLOR_PANEL_BG, edgecolor=COLOR_PANEL_BG, fontsize=9, loc='upper left')
    for text in legend.get_texts():
        text.set_color(COLOR_TEXT_LIGHT)

    fig.tight_layout(pad=1.5)

    # Add interactive tooltips using mplcursors if available
    try:
        import mplcursors
        # Create scatter plots for each status to use with mplcursors
        todo_scatter = ax.scatter(x, todo_counts, color="#42A5F5", s=60, zorder=4)
        inprogress_scatter = ax.scatter(x, inprogress_counts, color="#FBC02D", s=60, zorder=4)
        completed_scatter = ax.scatter(x, completed_counts, color="#43A047", s=60, zorder=4)
        # Only attach tooltips to the scatter points, not the lines
        cursor = mplcursors.cursor([todo_scatter, inprogress_scatter, completed_scatter], hover=True)
        def show_tooltip(sel):
            idx = sel.index
            if sel.artist == todo_scatter:
                label = "To Do"
                value = todo_counts[idx]
                color = "#42A5F5"
            elif sel.artist == inprogress_scatter:
                label = "In Progress"
                value = inprogress_counts[idx]
                color = "#FBC02D"
            else:
                label = "Completed"
                value = completed_counts[idx]
                color = "#43A047"
            project = project_names[idx] if idx < len(project_names) else "Unknown"
            sel.annotation.set_text(f"{label} {value}\nProject: {project}")
            sel.annotation.get_bbox_patch().set(fc=color, ec=color)
            sel.annotation.get_bbox_patch().set_alpha(0.95)
        cursor.connect("add", show_tooltip)
    except ImportError:
        pass  # If mplcursors is not installed, skip tooltips

    chart_canvas = FigureCanvasTkAgg(fig, master=chart_panel)
    chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

    # --- Right: Project Status Percentages Bar Panel ---
    right_panel = tk.Frame(main_content_frame, bg=COLOR_PANEL_BG, bd=1, relief=tk.FLAT)
    right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
    tk.Label(right_panel, text="Project Status (%)", font=("Arial", 14, "bold"), bg=COLOR_PANEL_BG, fg=COLOR_TEXT_HEADER).pack(anchor="nw", padx=20, pady=(15, 5))
    bar_labels = {}
    bar_frames = {}
    bar_colors = {"Not Yet Started": "#3498db", "In Progress": "#f1c40f", "Completed": "#2ecc71"}
    max_bar_width = 220
    bar_bg_refs = {}  # Store references to each bar_bg for dynamic width
    for status in ["Not Yet Started", "In Progress", "Completed"]:
        frame = tk.Frame(right_panel, bg=COLOR_PANEL_BG)
        frame.pack(fill="x", padx=20, pady=(10, 0))
        tk.Label(frame, text=status, font=("Arial", 11, "bold"), bg=COLOR_PANEL_BG, fg=bar_colors[status]).pack(anchor="w")
        bar_bg = tk.Frame(frame, bg="#333", height=18)
        bar_bg.pack(fill="x", pady=(4, 0))
        bar_bg.pack_propagate(False)
        bar_fg = tk.Frame(bar_bg, bg=bar_colors[status], width=0, height=18)
        bar_fg.pack(side="left", fill="y", anchor="w")
        percent_label = tk.Label(frame, text="0.0%", font=("Arial", 10), bg=COLOR_PANEL_BG, fg=COLOR_TEXT_HEADER)
        percent_label.pack(anchor="e", pady=(2, 0))
        bar_labels[status] = percent_label
        bar_frames[status] = bar_fg
        bar_bg_refs[status] = bar_bg
        # Bind resize event to update bars dynamically
        bar_bg.bind("<Configure>", lambda event: update_project_status_percentages())

    def update_project_status_percentages():
        status_counts = {"Not Yet Started": 0, "In Progress": 0, "Completed": 0}
        total_projects = len(projects_data)
        for project in projects_data:
            status = project[2]  # status field index
            if status in status_counts:
                status_counts[status] += 1
        for status in status_counts:
            percent = (status_counts[status] / total_projects * 100) if total_projects else 0
            bar_labels[status].config(text=f"{percent:.1f}%")
            bar_bg = bar_bg_refs[status]
            bar_bg.update_idletasks()
            actual_width = bar_bg.winfo_width()
            bar_width = int(actual_width * percent / 100)
            bar_fg = bar_frames[status]
            bar_fg.config(width=bar_width)
            bar_fg.pack_forget()
            bar_fg.pack(side="left", fill="y", anchor="w")

    # --- Donut Animation Function (unchanged) ---
    def animate_donut(canvas, current_step):
        global donut_animation_id
        if not isinstance(canvas, tk.Canvas) or not canvas.winfo_exists():
            donut_animation_id = None
            return

        try:
            canvas.update_idletasks()
            w, h = canvas.winfo_width(), canvas.winfo_height()
            if w <= 1 or h <=1:
                if current_step < ANIMATION_STEPS:
                    if canvas.winfo_exists():
                        donut_animation_id = root.after(ANIMATION_DELAY, animate_donut, canvas, current_step + 1)
                    else:
                        donut_animation_id = None
                else:
                    donut_animation_id = None
                return

            progress = current_step / ANIMATION_STEPS
            current_extent = - (done_percentage / 100) * 359.9 * progress
            canvas.delete("anim_donut")

            cx, cy = w / 2, h / 2
            radius = min(cx, cy) * 0.8
            bbox_half_width = radius
            bbox = (cx - bbox_half_width, cy - bbox_half_width, cx + bbox_half_width, cy + bbox_half_width)
            line_width = max(6, radius * 0.15)

            canvas.create_arc(bbox, start=90, extent=359.9, style=tk.ARC, outline=COLOR_CHART_BG_MUTED, width=line_width, tags=("anim_donut", "background"))
            canvas.create_arc(bbox, start=90, extent=current_extent, style=tk.ARC, outline=COLOR_PRIMARY, width=line_width, tags=("anim_donut", "progress"))

            current_percentage_text = int(done_percentage * progress)
            canvas.create_text(cx, cy, text=f"{current_percentage_text}%", fill=COLOR_TEXT_LIGHT, font=FONT_MEDIUM_BOLD, tags=("anim_donut", "text"))

            if current_step < ANIMATION_STEPS:
                if canvas.winfo_exists():
                    donut_animation_id = root.after(ANIMATION_DELAY, animate_donut, canvas, current_step + 1)
                else:
                    donut_animation_id = None
            else:
                donut_animation_id = None

        except tk.TclError as e:
            print(f"TclError during donut animation: {e}. Stopping.")
            donut_animation_id = None
        except Exception as e:
            print(f"Unexpected error during donut animation: {e}. Stopping.")
            donut_animation_id = None

    # --- Matplotlib Area Chart Function ---
    # def create_matplotlib_area_chart(parent_widget):
    #     years = [2013, 2014, 2015, 2016, 2017]
    #     votes = [12, 19, 3, 6, 2]
    #     fig = Figure(figsize=(6, 3.5), dpi=100, facecolor=COLOR_PANEL_BG) # Dark Panel BG
    #     fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.15)
    #     try:
    #         ax = fig.add_subplot(111)
    #         ax.set_facecolor(COLOR_PANEL_BG) # Dark Panel BG
    #         # Use a fill derived from Primary Orange, but lighter/desaturated for dark theme
    #         fill_color_primary_light = '#A85C34' # Adjust alpha or color manually if needed
    #         ax.fill_between(years, votes, color=fill_color_primary_light, alpha=0.6) # Adjusted fill
    #         ax.scatter(years, votes, color=COLOR_PRIMARY, edgecolors=MPL_MARKER_EDGE_COLOR, zorder=3, s=60) # Primary Orange markers, light edge
    #         ax.set_ylabel("Jobs", fontsize=10, fontweight='bold', color=COLOR_PRIMARY) # Primary Orange label
    #         ax.set_xticks(years)
    #         ax.set_yticks(np.arange(0, max(votes) + 2, 2))
    #         ax.spines['top'].set_visible(False)
    #         ax.spines['right'].set_visible(False)
    #         ax.spines['left'].set_color(MPL_SPINE_COLOR) # Light grey spines
    #         ax.spines['bottom'].set_color(MPL_SPINE_COLOR)
    #         ax.tick_params(axis='x', colors=MPL_TICK_COLOR, labelsize=8) # Light grey ticks
    #         ax.tick_params(axis='y', colors=MPL_TICK_COLOR, labelsize=8)
    #         ax.grid(True, axis='y', linestyle='--', alpha=0.6, color=MPL_GRID_COLOR) # Light grey grid
    #         canvas = FigureCanvasTkAgg(fig, master=parent_widget)
    #         canvas_widget = canvas.get_tk_widget()
    #         canvas_widget.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)
    #         return fig, canvas
    #     except Exception as e:
    #         print(f"Error creating Matplotlib chart: {e}")
    #         return None, None


    # Extract and count projects by year
    year_counts = Counter()
    for project in agent_data.get("data", []):
        created = project.get("created_date")
        if created:
            try:
                dt = datetime.fromisoformat(created.rstrip("Z"))
                year_counts[dt.year] += 1
            except Exception as e:
                print(f"Invalid date: {created} -> {e}")

    # Sort by year
    years = sorted(year_counts)
    votes = [year_counts[y] for y in years]

    def create_matplotlib_area_chart(parent_widget):
        fig = Figure(figsize=(6, 3.5), dpi=100, facecolor=COLOR_PANEL_BG)
        fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.15)
        try:
            ax = fig.add_subplot(111)
            ax.set_facecolor(COLOR_PANEL_BG)
            fill_color_primary_light = '#A85C34'
            ax.fill_between(years, votes, color=fill_color_primary_light, alpha=0.6)
            ax.scatter(years, votes, color=COLOR_PRIMARY, edgecolors=MPL_MARKER_EDGE_COLOR, zorder=3, s=60)
            ax.set_ylabel("Projects", fontsize=10, fontweight='bold', color=COLOR_PRIMARY)
            ax.set_xticks(years)
            ax.set_yticks(np.arange(0, max(votes)+1))
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color(MPL_SPINE_COLOR)
            ax.spines['bottom'].set_color(MPL_SPINE_COLOR)
            ax.tick_params(axis='x', colors=MPL_TICK_COLOR, labelsize=8)
            ax.tick_params(axis='y', colors=MPL_TICK_COLOR, labelsize=8)
            ax.grid(True, axis='y', linestyle='--', alpha=0.6, color=MPL_GRID_COLOR)
            canvas = FigureCanvasTkAgg(fig, master=parent_widget)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)
            return fig, canvas
        except Exception as e:
            print(f"Error creating dynamic chart: {e}")
            return None, None

    total_todo = 0
    # for project in agent_data.get("data", []):
    #     for subtype in project.get("subtypes_status", []):
    #         status = subtype.get("status", "").strip().lower()
    #         if status == "to-do":
    #             total_todo += 1

    # # Remove undefined total_assigned and use total = total_todo + total_in_progress + total_done
    # total = total_todo + total_in_progress + total_done or 1  # avoid divide-by-zero
    # percent_done = round((total_done / total) * 100)
    # percent_in_progress = round((total_in_progress / total) * 100)
    # percent_todo = round((total_todo / total) * 100)


    # --- Row 1 & 2: Area Chart & Triangle Chart (Inside Dashboard Page) ---
    # panel7 = create_panel(dashboard_page_frame, 1, 0, rowspan=2, colspan=1) # Dark Panel BG
    # area_title_frame = tk.Frame(panel7, bg=COLOR_PANEL_BG)
    # area_title_frame.pack(fill=tk.X, pady=(0, 5))
    # tk.Label(area_title_frame, text="Project Timeline (Created Dates)", bg=COLOR_PANEL_BG, fg=COLOR_TEXT_LIGHT, font=("Arial", 14, "bold")).pack(side=tk.LEFT)

    # --- Area Chart: X=Days, Y=Project Names, horizontal lines showing project age ---
    def create_project_timeline_chart(parent_widget):
        # Gather project names and their created dates
        projects = [(p.get("project_name", "Untitled"), p.get("created_date")) for p in agent_data.get("data", [])]
        from datetime import datetime
        valid_projects = [(name, cd) for name, cd in projects if cd]
        if not valid_projects:
            return None, None
        dates = [datetime.fromisoformat(cd.rstrip("Z")) for _, cd in valid_projects]
        min_date = min(dates)
        days = [(d - min_date).days + 1 for d in dates]
        names = [name for name, _ in valid_projects]
        y_pos = np.arange(len(names))
        fig = Figure(figsize=(6, 2.5), dpi=100, facecolor=COLOR_PANEL_BG)
        fig.subplots_adjust(left=0.18, right=0.98, top=0.92, bottom=0.15)
        ax = fig.add_subplot(111)
        ax.set_facecolor(COLOR_PANEL_BG)

        # # Draw horizontal lines for each project starting from x=0 (the Y-axis)
        # for i, (day, name) in enumerate(zip(days, names)):
        #     ax.hlines(i, 0, day, color=COLOR_PRIMARY, linewidth=2)
        #     # Start circle at the Y-axis (optional, for clarity)
        #     ax.plot(0, i, 'o', color=COLOR_PANEL_BG, markeredgecolor=COLOR_PRIMARY, markersize=7, zorder=3)
        #     # End circle (big dot)
        #     ax.plot(day, i, 'o', color=COLOR_PRIMARY, markersize=10, zorder=4)

        # ax.set_yticks(y_pos)
        # ax.set_yticklabels(names, fontsize=11, color=COLOR_TEXT_LIGHT)
        # max_days = max(days) if days else 1
        # ax.set_xticks(np.arange(0, max_days + 1))
        # ax.set_xlabel("Days", color=COLOR_TEXT_LIGHT, fontsize=12)
        # # ax.set_ylabel("Project", color=COLOR_TEXT_LIGHT, fontsize=12)
        # ax.tick_params(axis='x', colors=COLOR_TEXT_LIGHT, labelsize=10)
        # ax.tick_params(axis='y', colors=COLOR_TEXT_LIGHT, labelsize=10)
        # ax.spines['top'].set_visible(False)
        # ax.spines['right'].set_visible(False)
        # ax.spines['left'].set_color(MPL_SPINE_COLOR)
        # ax.spines['bottom'].set_color(MPL_SPINE_COLOR)
        # ax.grid(True, axis='x', linestyle='--', alpha=0.5, color=MPL_GRID_COLOR)

        # canvas = FigureCanvasTkAgg(fig, master=parent_widget)
        # canvas_widget = canvas.get_tk_widget()
        # canvas_widget.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)
        # return fig, canvas

    # # Remove old chart if present
    # for child in panel7.pack_slaves():
    #     if isinstance(child, FigureCanvasTkAgg):
    #         child.get_tk_widget().destroy()
    # mpl_fig, mpl_canvas_agg = create_project_timeline_chart(panel7)

    # # --- Resizing Handlers for Area Chart ---
    # def _redraw_area_chart_debounced(canvas_agg, fig):
    #     nonlocal area_chart_resize_timer_id
    #     if canvas_agg and fig and canvas_agg.get_tk_widget().winfo_exists():
    #         try:
    #             canvas_agg.draw_idle()
    #         except Exception as e:
    #             print(f"Error redrawing area chart: {e}")
        # area_chart_resize_timer_id = None

    # def on_area_chart_resize(event):
    #     nonlocal area_chart_resize_timer_id
    #     if mpl_canvas_agg:
    #         if area_chart_resize_timer_id:
    #             root.after_cancel(area_chart_resize_timer_id)
    #         area_chart_resize_timer_id = root.after(DEBOUNCE_DELAY, _redraw_area_chart_debounced, mpl_canvas_agg, mpl_fig)

    # if mpl_canvas_agg:
    #     panel7.configure(bg=COLOR_PANEL_BG)
    #     mpl_canvas_agg.get_tk_widget().configure(bg=COLOR_PANEL_BG)
    #     panel7.bind("<Configure>", on_area_chart_resize)

    # --- Triangle Chart Panel replaced with Radar Chart ---
    # All radar chart and dropdown code removed as per new dashboard layout
    # (No more references to project_names, selected_project, radar_dropdown, or draw_radar_chart)


    # --- PAGE CLASSES ---
    class ReportDetailPage(tk.Frame):
        def __init__(self, parent, switch_page_callback, project_data):
            super().__init__(parent, bg=COLOR_CONTENT_BG)
            self.switch_page_callback = switch_page_callback
            self.project_data = project_data
            # Title
            title_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
            title_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
            title = tk.Label(title_frame, text=f"{project_data[0]} - Details", font=("Arial", 18, "bold"), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
            title.pack(side=tk.LEFT)
            back_btn = tk.Button(title_frame, text="← Back", command=lambda: switch_page_callback("Report"), bg=COLOR_PANEL_BG, fg=COLOR_TEXT_LIGHT, font=("Segoe UI", 10, "bold"), relief=tk.FLAT, bd=0, padx=10, pady=5, activebackground=COLOR_PRIMARY, activeforeground=COLOR_TEXT_LIGHT)
            back_btn.pack(side=tk.RIGHT)
            # Show all subtypes (test cases) for this project
            subtypes = project_data[6]
            grid_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
            grid_frame.pack(fill=tk.BOTH, expand=True)
            folder_size = 80
            max_cols = 4
            for idx, subtype in enumerate(subtypes):
                row = idx // max_cols
                col = idx % max_cols
                cell = tk.Frame(grid_frame, bg=COLOR_CONTENT_BG)
                cell.grid(row=row, column=col, padx=60, pady=40)
                canvas = tk.Canvas(cell, width=folder_size, height=folder_size, bg=COLOR_CONTENT_BG, highlightthickness=0)
                canvas.create_rectangle(10, 30, 70, 70, fill="#FFD966", outline="#FFD966")
                canvas.create_rectangle(20, 15, 50, 40, fill="#FFE599", outline="#FFE599")
                canvas.pack()
                name_label = tk.Label(cell, text=subtype.get("type", "Unnamed"), font=("Arial", 13), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
                name_label.pack(pady=(8, 0))
        # ============================================
    # MODIFIED ProjectPage Class for Responsiveness & Dark Theme
    # ============================================
    class ProjectPage(tk.Frame):
        def __init__(self, parent, switch_page_callback, fonts, projects_data=None, token=None, base_url=None):
            super().__init__(parent, bg=COLOR_CONTENT_BG)
            self.switch_page_callback = switch_page_callback
            self.TABLE_FONT_HEADER = fonts["TABLE_FONT_HEADER"]
            self.TABLE_FONT_PROJECT_NAME = fonts["TABLE_FONT_PROJECT_NAME"]
            self.TABLE_FONT_BODY_SMALL = fonts["TABLE_FONT_BODY_SMALL"]
            self.TABLE_FONT_STATUS = fonts["TABLE_FONT_STATUS"]
            self.TABLE_FONT_BODY_REGULAR = fonts["TABLE_FONT_BODY_REGULAR"]
            self.token = token
            self.base_url = base_url
            self.projects_data = projects_data or []

            # All other existing attributes stay the same
            self.headers = ["Projects", "Status", "DUT", "Reporting Manager", "Progress"]
            self.horizontal_padding = 15
            self.row_start_x = 10
            self.scrollbar_width_approx = 20

            self.col_proportions = [1, 1, 1, 1, 1]
            self.min_col_widths = [120, 120, 120, 120, 120]
            self.min_total_content_width = self.row_start_x + sum(self.min_col_widths) + self.horizontal_padding

            self.current_col_widths = list(self.min_col_widths)
            self.current_content_width = self.min_total_content_width
            self.header_height = 45
            self.row_height = 75
            self.row_y_coords = {}
            self.hover_rect_id = None
            self.current_hover_row = -1
            self._draw_scheduled = None

            # Title uses Dark BG, Light FG
            title_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
            title_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
            title = tk.Label(title_frame, text="Projects", font=("Arial", 18, "bold"), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
            title.pack(side=tk.LEFT)

            # Table area uses Dark BG
            table_area_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
            table_area_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
            table_area_frame.grid_rowconfigure(0, weight=1)
            table_area_frame.grid_columnconfigure(0, weight=1)

            # Canvas uses Dark Panel BG, Dark Border
            self.canvas = tk.Canvas(table_area_frame, bg=COLOR_PANEL_BG, bd=0,
                                    highlightthickness=1, highlightbackground=COLOR_BORDER_MEDIUM, takefocus=1 )
            self.canvas.grid(row=0, column=0, sticky="nsew")

            # Style scrollbars if possible (ttk might allow some styling)
            style = ttk.Style()
            try: # Add basic scrollbar styling for dark theme if possible
                style.theme_use('clam') # Or 'alt', 'default' - experiment
                style.configure("Vertical.TScrollbar", gripcount=0, background=COLOR_PANEL_BG, darkcolor=COLOR_BORDER_MEDIUM, lightcolor=COLOR_BORDER_LIGHT, troughcolor=COLOR_CONTENT_BG, bordercolor=COLOR_SIDEBAR_BG, arrowcolor=COLOR_TEXT_MUTED_DARK_BG)
                style.configure("Horizontal.TScrollbar", gripcount=0, background=COLOR_PANEL_BG, darkcolor=COLOR_BORDER_MEDIUM, lightcolor=COLOR_BORDER_LIGHT, troughcolor=COLOR_CONTENT_BG, bordercolor=COLOR_SIDEBAR_BG, arrowcolor=COLOR_TEXT_MUTED_DARK_BG)
            except tk.TclError:
                print("Warning: Failed to apply ttk scrollbar style (theme issue?). Using default.")

            v_scrollbar = ttk.Scrollbar(table_area_frame, orient="vertical", command=self.canvas.yview, style="Vertical.TScrollbar")
            v_scrollbar.grid(row=0, column=1, sticky="ns")
            self.canvas.configure(yscrollcommand=v_scrollbar.set)

            h_scrollbar = ttk.Scrollbar(table_area_frame, orient="horizontal", command=self.canvas.xview, style="Horizontal.TScrollbar")
            h_scrollbar.grid(row=1, column=0, sticky="ew")
            self.canvas.configure(xscrollcommand=h_scrollbar.set)

            self.canvas.bind("<Motion>", self._on_motion)
            self.canvas.bind("<Leave>", self._on_leave)
            self.canvas.bind("<Button-1>", self._on_click)

            # self.canvas.bind("<Double-1>", lambda e: print("Canvas double-click triggered"))


            self.canvas.bind("<Configure>", self._on_canvas_configure_debounced)
            self.canvas.bind("<Enter>", lambda _: self.canvas.focus_set())
            self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
            self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))
            self.canvas.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        def _update_layout(self, available_width):
            """Calculates column widths and total content width based on available space."""
            usable_width = available_width - self.row_start_x - self.horizontal_padding
            if usable_width < (sum(self.min_col_widths)):
                self.current_col_widths = list(self.min_col_widths)
                self.current_content_width = self.min_total_content_width
            else:
                total_proportion = sum(self.col_proportions)
                calculated_widths = []
                extra_space_per_proportion = usable_width / total_proportion
                for i, prop in enumerate(self.col_proportions):
                    calc_w = int(prop * extra_space_per_proportion)
                    actual_w = max(self.min_col_widths[i], calc_w)
                    calculated_widths.append(actual_w)
                current_sum = sum(calculated_widths)
                remainder = usable_width - current_sum
                if remainder > 0:
                    eligible_indices = [i for i, w in enumerate(calculated_widths) if w > self.min_col_widths[i]]
                    if eligible_indices:
                        prop_sum_eligible = sum(self.col_proportions[i] for i in eligible_indices)
                        if prop_sum_eligible > 0:
                            added_so_far = 0
                            for i in eligible_indices[:-1]:
                                add_amount = int(remainder * (self.col_proportions[i] / prop_sum_eligible))
                                calculated_widths[i] += add_amount
                                added_so_far += add_amount
                            calculated_widths[eligible_indices[-1]] += (remainder - added_so_far)
                self.current_col_widths = calculated_widths
                self.current_content_width = self.row_start_x + sum(self.current_col_widths) + self.horizontal_padding

        def _draw_table(self):
            """Draws the entire table content onto the canvas, recalculating layout."""
            if not self.winfo_exists() or not self.canvas.winfo_exists():
                return
            try:
                current_canvas_width = self.canvas.winfo_width()
                if current_canvas_width <= 1:
                    self._schedule_redraw()
                    return
                self._update_layout(current_canvas_width)
                self.canvas.delete("all")
                self.row_y_coords.clear()
                self.hover_rect_id = None
                draw_width = max(current_canvas_width, self.current_content_width)

                # Draw Header Background (Dark Header BG)
                self.canvas.create_rectangle(0, 0, draw_width, self.header_height, fill=COLOR_HEADER_BG, outline="", tags=("header_bg", "header"))

                # Draw Header Text (Light Header Text)
                x_header = self.row_start_x
                y_header_text = self.header_height / 2
                for i, header in enumerate(self.headers):
                    if i < len(self.current_col_widths):
                        col_w = self.current_col_widths[i]
                        self.canvas.create_text(x_header + self.horizontal_padding, y_header_text, text=header, anchor='w',
                                                font=TABLE_FONT_HEADER, fill=COLOR_TEXT_HEADER, tags=("header_text", "header"))
                        x_header += col_w
                    else:
                        print(f"Warning: Header index {i} out of bounds for current_col_widths (len={len(self.current_col_widths)})")
                        break

                # Header line uses dark theme border color
                header_line_end_x = self.row_start_x + sum(self.current_col_widths)
                self.canvas.create_line(self.row_start_x, self.header_height, header_line_end_x, self.header_height,
                                        fill=COLOR_BORDER_LIGHT, tags=("header_line", "header"))

                y_current = self.header_height
                for i, project_data in enumerate(self.projects_data):
                    if not self.canvas.winfo_exists(): break
                    self._draw_row(y_current, project_data, i, self.current_col_widths)
                    self.row_y_coords[i] = (y_current, y_current + self.row_height)
                    y_current += self.row_height

                total_content_height = y_current
                self.canvas.config(scrollregion=(0, 0, self.current_content_width, total_content_height))
                self._redraw_hover()

            except tk.TclError as e:
                print(f"TclError during table draw: {e}")
            except Exception as e:
                print(f"Unexpected error during table draw: {e}")
            finally:
                self._draw_scheduled = None

        def _draw_row(self, y_pos, data, index, current_widths):
            """Draws a single project row onto the canvas using provided widths."""
            if not self.canvas.winfo_exists() or len(current_widths) != len(self.headers):
                print(f"Warning: Skipping row draw for index {index} due to invalid state.")
                return
            try:
                name, site, status, dut, manager, progress, subtypes, project_id, agent_id = data

                x = self.row_start_x
                row_center_y = y_pos + self.row_height / 2
                top_padding = 15
                row_tags = (f"row_{index}", "project_row")
                row_end_x = self.row_start_x + sum(current_widths)

                # Col 1: Project Name & Site (Light Text)
                col_w = current_widths[0]
                name_wrap_width = max(20, col_w - (self.horizontal_padding * 1.5))
                self.canvas.create_text(x + self.horizontal_padding, y_pos + top_padding, text=name, anchor='nw',
                                        font=TABLE_FONT_PROJECT_NAME if str(type(TABLE_FONT_PROJECT_NAME)) == "<class 'tkinter.font.Font'>" else ("Arial", 11, "bold"), fill=COLOR_TEXT_LIGHT, # Main Light Text
                                        width=name_wrap_width, tags=row_tags)
                site_y_offset = y_pos + top_padding + TABLE_FONT_PROJECT_NAME.metrics('linespace') + 4
                self.canvas.create_text(x + self.horizontal_padding, site_y_offset, text=site, anchor='nw',
                                        font=TABLE_FONT_BODY_SMALL, fill=COLOR_TEXT_TERTIARY_TABLE, tags=row_tags) # Muted Light Text
                x += col_w

                # Col 2: Status Badge (Use Dark Theme Status Colors)
                col_w = current_widths[1]
                status_box_width, status_box_height = 130, 22  
                status_box_x = x + self.horizontal_padding  # Aligned to left
                status_box_y = y_pos + 15  # Adjust vertical position as needed

                # Use dark theme status colors (same as JobPage)
                status_map = {
                    "Not Yet Started": (COLOR_STATUS_PENDING_BG, COLOR_STATUS_PENDING_FG),
                    "In Progress": (COLOR_STATUS_INPROGRESS_BG, COLOR_STATUS_INPROGRESS_FG),
                    "Completed": (COLOR_STATUS_COMPLETED_BG, COLOR_STATUS_COMPLETED_FG),
                    "Blocked": (COLOR_STATUS_BLOCKED_BG, COLOR_STATUS_BLOCKED_FG),
                    "Customer": (COLOR_STATUS_CUSTOMER_BG, COLOR_STATUS_CUSTOMER_FG),
                }
                status_bg, status_fg = status_map.get(status, (COLOR_STATUS_CHURNED_BG, COLOR_STATUS_CHURNED_FG))

                if all(math.isfinite(c) for c in [status_box_x, status_box_y]):
                    draw_rounded_rectangle(self.canvas, status_box_x, status_box_y, status_box_x + status_box_width, status_box_y + status_box_height,
                                    radius=8, fill=status_bg, outline="", tags=row_tags + ("status_badge",))
                    self.canvas.create_text(status_box_x + status_box_width / 2, status_box_y + status_box_height / 2,
                                        text=status, font=TABLE_FONT_STATUS, fill=status_fg, tags=row_tags + ("status_text",))
                x += col_w

                # --- Col 3: DUT ---
                col_w = current_widths[2]
                self.canvas.create_text(x + self.horizontal_padding, y_pos + top_padding, text=dut, anchor='nw',
                                        font=self.TABLE_FONT_BODY_REGULAR, fill=COLOR_TEXT_SECONDARY_TABLE,
                                        width=col_w - self.horizontal_padding * 1.5, tags=row_tags)
                x += col_w

                # --- Col 4: Reporting Manager ---
                col_w = current_widths[3]
                self.canvas.create_text(x + self.horizontal_padding, y_pos + top_padding, text=manager, anchor='nw',
                                        font=self.TABLE_FONT_BODY_REGULAR, fill=COLOR_TEXT_SECONDARY_TABLE,
                                        width=col_w - self.horizontal_padding * 1.5, tags=row_tags)
                x += col_w

                # --- Col 5: Progress Bar ---
                col_w = current_widths[4]
                progress_bar_x = x + self.horizontal_padding
                progress_bar_y = row_center_y
                progress_bar_width = max(10, col_w - self.horizontal_padding * 2 - 40)
                progress_bar_height = 8
                progress_radius = 4
                p_y1 = progress_bar_y - (progress_bar_height / 2)
                p_y2 = progress_bar_y + (progress_bar_height / 2)
                draw_rounded_rectangle(self.canvas, progress_bar_x, p_y1, progress_bar_x + progress_bar_width, p_y2,
                                    radius=progress_radius, fill=COLOR_PROGRESS_BG, outline="", tags=row_tags)
                progress_clamped = max(0, min(100, int(progress)))
                fill_width = progress_clamped * (progress_bar_width / 100.0)
                if fill_width > 0:
                    fill_x2 = min(progress_bar_x + fill_width, progress_bar_x + progress_bar_width)
                    if fill_width >= 2 * progress_radius:
                        draw_rounded_rectangle(self.canvas, progress_bar_x, p_y1, fill_x2, p_y2,
                                            radius=progress_radius, fill=COLOR_PROGRESS_FILL, outline="", tags=row_tags)
                    else:
                        self.canvas.create_rectangle(progress_bar_x, p_y1, fill_x2, p_y2,
                                                    fill=COLOR_PROGRESS_FILL, outline="", tags=row_tags)
                text_x = progress_bar_x + progress_bar_width + 10
                self.canvas.create_text(text_x, progress_bar_y,
                                        text=f"{progress_clamped}%", anchor='w', font=self.TABLE_FONT_BODY_SMALL,
                                        fill=COLOR_TEXT_TERTIARY_TABLE, tags=row_tags)

                # --- Row Separator ---
                self.canvas.create_line(self.row_start_x, y_pos + self.row_height, row_end_x, y_pos + self.row_height,
                                        fill=COLOR_BORDER_LIGHT, tags=row_tags)
            except tk.TclError as e: print(f"TclError drawing row {index}: {e}")
            except Exception as e: print(f"Unexpected error drawing row {index}: {e}")

        def _find_row_at_y(self, canvas_y):
            if not math.isfinite(canvas_y): return -1
            for i, (y1, y2) in self.row_y_coords.items():
                if math.isfinite(y1) and math.isfinite(y2):
                    if y1 <= canvas_y < y2: return i
            return -1

        def _redraw_hover(self):
            """Redraws hover effect using current row end coordinate and dark theme hover color."""
            if not self.canvas.winfo_exists(): return
            try:
                hover_end_x = self.row_start_x + sum(self.current_col_widths)
                if self.hover_rect_id and self.hover_rect_id in self.canvas.find_all():
                    self.canvas.delete(self.hover_rect_id)
                self.hover_rect_id = None

                if self.current_hover_row != -1:
                    if self.current_hover_row in self.row_y_coords:
                        y1, y2 = self.row_y_coords[self.current_hover_row]
                        if math.isfinite(y1) and math.isfinite(y2):
                            self.hover_rect_id = self.canvas.create_rectangle(
                                self.row_start_x, y1, hover_end_x, y2,
                                fill=COLOR_HOVER_BG, outline="", tags="hover_effect") # Dark theme hover
                            self.canvas.tag_lower(self.hover_rect_id, "project_row")
                    else:
                        self.current_hover_row = -1
            except tk.TclError as e:
                print(f"TclError during hover redraw: {e}")
                self.hover_rect_id = None
            except Exception as e:
                print(f"Unexpected error during hover redraw: {e}")
                self.hover_rect_id = None

        def _on_motion(self, event):
            """Handles mouse motion for hover effects."""
            if not self.canvas.winfo_exists(): return
            try:
                canvas_y = self.canvas.canvasy(event.y)
                if not math.isfinite(canvas_y): return
                hovering_over_row = self._find_row_at_y(canvas_y)
                canvas_x = self.canvas.canvasx(event.x)
                row_end_x = self.row_start_x + sum(self.current_col_widths)
                if not (self.row_start_x <= canvas_x < row_end_x):
                    hovering_over_row = -1
                if hovering_over_row != self.current_hover_row:
                    self.current_hover_row = hovering_over_row
                    self._redraw_hover()
            except tk.TclError: pass
            except Exception as e: print(f"Unexpected error in _on_motion: {e}")

        def _on_leave(self, event):
            """Clears hover effect when mouse leaves the canvas."""
            if not self.canvas.winfo_exists(): return
            if self.current_hover_row != -1:
                self.current_hover_row = -1
                self._redraw_hover()

        def _on_click(self, event):
            if not self.canvas.winfo_exists():
                return
            try:
                canvas_y = self.canvas.canvasy(event.y)
                canvas_x = self.canvas.canvasx(event.x)
                clicked_row_index = self._find_row_at_y(canvas_y)
                row_end_x = self.row_start_x + sum(self.current_col_widths)

                if clicked_row_index != -1 and (self.row_start_x <= canvas_x < row_end_x):
                    if 0 <= clicked_row_index < len(self.projects_data):
                        project_data = self.projects_data[clicked_row_index]
                        project_name = project_data[0]
                        subtypes = project_data[6]
                        test_cases_data = {"todo": [], "inprogress": [], "completed": []}
                        project_id = project_data[7]
                        agent_id = project_data[8]

                        subtype_id_map = {}
                        for sub in subtypes:
                            status = sub.get("status", "").strip().lower()
                            tc_title = sub.get("type", "Unnamed")
                            subtype_id = sub.get("id")
                            subtype_id_map[tc_title] = subtype_id
                            if status in ("to-do", "todo"):
                                test_cases_data["todo"].append(tc_title)
                            elif status in ("in progress", "progress"):
                                test_cases_data["inprogress"].append(tc_title)
                            elif status in ("done", "completed"):
                                test_cases_data["completed"].append(tc_title)
                            else:
                                test_cases_data["todo"].append(tc_title)

                        # Open TestCases page and load local data, no server call
                        testcases_page = pages.get("TestCases")
                        if testcases_page:
                            testcases_page.load_project(project_name, test_cases_data, project_id, subtype_id_map, agent_id)
                            testcases_page.tkraise()
                        else:
                            messagebox.showerror("Error", "TestCases page not found.")
            except Exception as e:
                print(f"Error in click handler: {e}")

        def _schedule_redraw(self):
            """Schedules a redraw using after, cancelling any pending redraw."""
            if not self.winfo_exists():
                if self._draw_scheduled:
                    self.after_cancel(self._draw_scheduled)
                    self._draw_scheduled = None
                return
            if self._draw_scheduled:
                self.after_cancel(self._draw_scheduled)
            self._draw_scheduled = self.after(DEBOUNCE_DELAY, self._draw_table)

        def _on_canvas_configure_debounced(self, event):
            """Handles canvas resize event with debouncing."""
            self._schedule_redraw()

        def trigger_redraw(self):
            if self.winfo_exists():
                self._schedule_redraw()

        def fetch_dashboard_data(self):
            pass

        def tkraise(self, aboveThis=None):
            super().tkraise(aboveThis)
            self.fetch_dashboard_data()

    # ============================================
    # End of MODIFIED ProjectPage Class
    # ============================================

    class ReportPage(tk.Frame):
        def __init__(self, parent, switch_page_callback, fonts, projects_data=None, base_url=None, agent_id=None, token=None):
            super().__init__(parent, bg=COLOR_CONTENT_BG)
            self.switch_page_callback = switch_page_callback
            self.fonts = fonts
            self.parent = parent
            self.base_url = base_url
            self.token = token 
            self.clipboard_item = None  # (full_path, type, display_name)
            self.copied_highlight_cell = None  # Track the currently highlighted cell
            self.agent_id = agent_id 
            self._show_project_list()

        def highlight_enter(self, event, fr):
            try:
                fr.config(bg="#232323")
            except Exception:
                pass
            for w in fr.winfo_children():
                try:
                    w.config(bg="#232323")
                except Exception:
                    pass

        def highlight_leave(self, event, fr):
            try:
                fr.config(bg=COLOR_CONTENT_BG)
            except Exception:
                pass
            for w in fr.winfo_children():
                try:
                    w.config(bg=COLOR_CONTENT_BG)
                except Exception:
                    pass

        def highlight_copied_cell(self, cell):
            # Remove highlight from previous
            if self.copied_highlight_cell and self.copied_highlight_cell.winfo_exists():
                try:
                    self.copied_highlight_cell.config(highlightbackground=COLOR_CONTENT_BG, highlightthickness=0)
                except Exception:
                    pass
            # Highlight new cell
            if cell and cell.winfo_exists():
                try:
                    cell.config(highlightbackground="#ff9900", highlightthickness=3)
                except Exception:
                    pass
            self.copied_highlight_cell = cell

        def clear_copied_highlight(self):
            if self.copied_highlight_cell and self.copied_highlight_cell.winfo_exists():
                try:
                    self.copied_highlight_cell.config(highlightbackground=COLOR_CONTENT_BG, highlightthickness=0)
                except Exception:
                    pass
            self.copied_highlight_cell = None

        def show_context_menu(self, event, path, item_type, display_name, refresh_callback, parent_path=None, cell_widget=None):
            import shutil, os, time, tkinter.simpledialog
            menu = tk.Menu(event.widget, tearoff=0, fg=COLOR_TEXT_LIGHT, bg=COLOR_PANEL_BG, activeforeground=COLOR_TEXT_LIGHT, activebackground=COLOR_PRIMARY)

            def copy_cmd():
                self.clipboard_item = (path, item_type, display_name)
                self.highlight_copied_cell(cell_widget)
            def paste_cmd():
                if self.clipboard_item:
                    src, src_type, src_name = self.clipboard_item
                    try:
                        import os, shutil
                        if item_type == 'project' and src_type == 'project':
                            dest_dir = os.path.dirname(os.path.join('tmp', os.path.basename(path)))
                            unique_name = get_unique_name(dest_dir, os.path.basename(src))
                            dest = os.path.join(dest_dir, unique_name)
                            if os.path.isdir(src) and is_subpath(dest, src):
                                messagebox.showerror("Paste Error", "Cannot paste a folder into itself or its subfolder.")
                                return
                            shutil.copytree(src, dest)
                        elif item_type == 'testcase' and src_type == 'testcase':
                            dest_dir = path
                            unique_name = get_unique_name(dest_dir, os.path.basename(src))
                            dest = os.path.join(dest_dir, unique_name)
                            if os.path.isdir(src) and is_subpath(dest, src):
                                messagebox.showerror("Paste Error", "Cannot paste a folder into itself or its subfolder.")
                                return
                            shutil.copytree(src, dest)
                        elif item_type == 'testcase' and src_type == 'file':
                            dest_dir = path
                            unique_name = get_unique_name(dest_dir, os.path.basename(src))
                            dest = os.path.join(dest_dir, unique_name)
                            shutil.copy2(src, dest)
                        elif item_type == 'file' and src_type == 'file' and parent_path:
                            dest_dir = parent_path
                            unique_name = get_unique_name(dest_dir, os.path.basename(src))
                            dest = os.path.join(dest_dir, unique_name)
                            shutil.copy2(src, dest)
                        self.clipboard_item = None
                        self.clear_copied_highlight()
                        refresh_callback()
                        self.update_idletasks()
                        # Only show error if destination does not exist
                        if not os.path.exists(dest):
                            messagebox.showerror("Paste Error", f"Failed to paste: Destination was not created.")
                    except Exception as e:
                        # Only show error if destination does not exist
                        if 'dest' in locals() and os.path.exists(dest):
                            # Paste actually succeeded, suppress error
                            pass
                        else:
                            messagebox.showerror("Paste Error", f"Failed to paste: {e}")
            def rename_cmd():
                new_name = tkinter.simpledialog.askstring("Rename", f"Enter new name for {item_type} '{display_name}':", initialvalue=display_name)
                if new_name and new_name != display_name:
                    dst = os.path.join(os.path.dirname(path), new_name)
                    if not os.path.exists(dst):
                        os.rename(path, dst)
                        refresh_callback()
                    else:
                        messagebox.showerror("Rename Error", f"'{new_name}' already exists.")
            def delete_cmd():
                if messagebox.askyesno("Delete", f"Delete {item_type} '{display_name}'?"):
                    try:
                        if os.path.isdir(path):
                            shutil.rmtree(path)
                        else:
                            os.remove(path)
                        refresh_callback()
                    except Exception as e:
                        messagebox.showerror("Delete Error", f"Failed to delete: {e}")

            menu.add_command(label="Copy", command=copy_cmd)
            menu.add_command(label="Paste", command=paste_cmd, state="normal" if self.clipboard_item else "disabled")
            menu.add_command(label="Rename", command=rename_cmd)
            menu.add_command(label="Delete", command=delete_cmd)
            menu.tk_popup(event.x_root, event.y_root)

        def create_scrollable_frame(self, parent, bg_color):
            canvas = tk.Canvas(parent, bg=bg_color, highlightthickness=0)
            scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=bg_color)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(
                    scrollregion=canvas.bbox("all")
                )
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # --- Mouse wheel binding for scrolling ---
            def _on_mousewheel(event):
                # For Windows and MacOS
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                return "break"

            def _on_mousewheel_linux(event):
                # For Linux (event.num 4=up, 5=down)
                if event.num == 4:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")
                return "break"

            # Bind mousewheel to both canvas and frame
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel_linux)
            canvas.bind_all("<Button-5>", _on_mousewheel_linux)

            return scrollable_frame

        def _show_project_list(self):
            self.tmp_structure = get_tmp_file_structure()
            for widget in self.winfo_children():
                widget.destroy()
            title = tk.Label(self, text="Reports", font=("Arial", 18, "bold"), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
            title.pack(anchor="w", padx=0, pady=(10, 0))
            outer_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
            outer_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
            grid_frame = self.create_scrollable_frame(outer_frame, COLOR_CONTENT_BG)
            folder_size = 80
            max_cols = 4
            projects = list(self.tmp_structure.keys())
            if not projects:
                grid_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
                grid_frame.pack(fill=tk.BOTH, expand=True)
                no_reports_label = tk.Label(
                    grid_frame,
                    text="No reports found.",
                    font=("Arial", 14),
                    fg=COLOR_TEXT_LIGHT,
                    bg=COLOR_CONTENT_BG,
                    anchor="center",
                    justify="center"
                )
                no_reports_label.pack(side="top", fill="x", pady=(10, 0))
                return
            for idx, project_name in enumerate(projects):
                row = idx // max_cols
                col = idx % max_cols
                cell = tk.Frame(grid_frame, bg=COLOR_CONTENT_BG, highlightthickness=0)
                cell.grid(row=row, column=col, padx=60, pady=40)
                canvas = tk.Canvas(cell, width=folder_size, height=folder_size, bg=COLOR_CONTENT_BG, highlightthickness=0)
                canvas.create_rectangle(10, 30, 70, 70, fill="#FFD966", outline="#FFD966")
                canvas.create_rectangle(20, 15, 50, 40, fill="#FFE599", outline="#FFE599")
                canvas.pack()
                name_label = tk.Label(cell, text=project_name, font=("Arial", 13), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
                name_label.pack(pady=(8, 0))
                # --- Highlight on single click ---
                def on_single_click(event, idx=idx):
                    for i, widget in enumerate(grid_frame.winfo_children()):
                        if i == idx:
                            if isinstance(widget, (tk.Frame, tk.Label, tk.Canvas)):
                                widget.config(bg="#232323")
                            for w in widget.winfo_children():
                                if isinstance(w, (tk.Frame, tk.Label, tk.Canvas)):
                                    w.config(bg="#232323")
                        else:
                            if isinstance(widget, (tk.Frame, tk.Label, tk.Canvas)):
                                widget.config(bg=COLOR_CONTENT_BG)
                            for w in widget.winfo_children():
                                if isinstance(w, (tk.Frame, tk.Label, tk.Canvas)):
                                    w.config(bg=COLOR_CONTENT_BG)
                cell.bind("<Button-1>", on_single_click)
                canvas.bind("<Button-1>", on_single_click)
                name_label.bind("<Button-1>", on_single_click)
                # --- Double click to open ---
                cell.bind("<Double-Button-1>", lambda e, p=project_name: self._show_testcases(p))
                canvas.bind("<Double-Button-1>", lambda e, p=project_name: self._show_testcases(p))
                name_label.bind("<Double-Button-1>", lambda e, p=project_name: self._show_testcases(p))
                # --- Right click context menu ---
                def show_menu_cell(event, pn=project_name, cell_widget=cell):
                    self.show_context_menu(event, os.path.join(os.getcwd(), 'tmp', pn), 'project', pn, lambda: [setattr(self, 'tmp_structure', get_tmp_file_structure()), self._show_project_list()][-1], cell_widget=cell_widget)
                    return "break"
                cell.bind("<Button-3>", show_menu_cell)
                canvas.bind("<Button-3>", show_menu_cell)
                name_label.bind("<Button-3>", show_menu_cell)
            # --- Right click on empty space shows paste menu ---
            def show_bg_menu(event):
                # Only show if not on a cell
                widget = event.widget.winfo_containing(event.x_root, event.y_root)
                if widget not in [c for c in grid_frame.winfo_children()]:
                    self.show_bg_context_menu(event, os.path.join(os.getcwd(), 'tmp'), lambda: [setattr(self, 'tmp_structure', get_tmp_file_structure()), self._show_project_list()][-1])
            grid_frame.bind("<Button-3>", show_bg_menu)
            outer_frame.bind("<Button-3>", show_bg_menu)
            self.bind("<Button-3>", show_bg_menu)

        def _show_testcases(self, project_name):
            self._show_scanids_current_testcase = None
            self.tmp_structure = get_tmp_file_structure()
            for widget in self.winfo_children():
                widget.destroy()
            title = tk.Label(self, text="Test Cases", font=("Arial", 18, "bold"), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
            title.pack(anchor="w", padx=0, pady=(10, 0))
            breadcrumb = tk.Frame(self, bg=COLOR_CONTENT_BG)
            breadcrumb.pack(anchor="w", padx=0, pady=(0, 10))
            link_color = '#2986cc'
            hover_color = '#174a7c'
            def go_report(event=None):
                self._show_project_list()
            report_label = tk.Label(breadcrumb, text="Report", font=("Arial", 12), fg=link_color, bg=COLOR_CONTENT_BG, cursor="hand2")
            report_label.pack(side=tk.LEFT)
            def on_enter_testcases_report(e): report_label.config(fg=hover_color)
            def on_leave_testcases_report(e): report_label.config(fg=link_color)
            report_label.bind("<Enter>", on_enter_testcases_report)
            report_label.bind("<Leave>", on_leave_testcases_report)
            report_label.bind("<Button-1>", go_report)
            sep1 = tk.Label(breadcrumb, text=" > ", font=("Arial", 12), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
            sep1.pack(side=tk.LEFT)
            project_label = tk.Label(breadcrumb, text=project_name, font=("Arial", 12), fg=link_color, bg=COLOR_CONTENT_BG)
            project_label.pack(side=tk.LEFT)
            title_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
            title_frame.pack(fill=tk.X, padx=0, pady=(0, 0))
            back_btn = tk.Button(title_frame, text="\u2190 Back", command=self._show_project_list, bg=COLOR_PANEL_BG, fg=COLOR_TEXT_LIGHT, font=("Segoe UI", 10, "bold"), relief=tk.FLAT, bd=0, padx=10, pady=5, activebackground=COLOR_PRIMARY, activeforeground=COLOR_TEXT_LIGHT)
            back_btn.pack(side=tk.RIGHT)
            testcases = list(self.tmp_structure[project_name].keys())
            outer_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
            outer_frame.pack(fill=tk.BOTH, expand=True)
            grid_frame = self.create_scrollable_frame(outer_frame, COLOR_CONTENT_BG)
            folder_size = 80
            max_cols = 4
            for idx, testcase_name in enumerate(testcases):
                row = idx // max_cols
                col = idx % max_cols
                cell = tk.Frame(grid_frame, bg=COLOR_CONTENT_BG, highlightthickness=0)
                cell.grid(row=row, column=col, padx=60, pady=40)
                canvas = tk.Canvas(cell, width=folder_size, height=folder_size, bg=COLOR_CONTENT_BG, highlightthickness=0)
                canvas.create_rectangle(10, 30, 70, 70, fill="#FFD966", outline="#FFD966")
                canvas.create_rectangle(20, 15, 50, 40, fill="#FFE599", outline="#FFE599")
                canvas.pack()
                name_label = tk.Label(cell, text=testcase_name, font=("Arial", 13), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
                name_label.pack(pady=(8, 0))
                # --- Highlight on single click ---
                def on_single_click(event, idx=idx):
                    for i, widget in enumerate(grid_frame.winfo_children()):
                        if i == idx:
                            if isinstance(widget, (tk.Frame, tk.Label, tk.Canvas)):
                                widget.config(bg="#232323")
                            for w in widget.winfo_children():
                                if isinstance(w, (tk.Frame, tk.Label, tk.Canvas)):
                                    w.config(bg="#232323")
                        else:
                            if isinstance(widget, (tk.Frame, tk.Label, tk.Canvas)):
                                widget.config(bg=COLOR_CONTENT_BG)
                            for w in widget.winfo_children():
                                if isinstance(w, (tk.Frame, tk.Label, tk.Canvas)):
                                    w.config(bg=COLOR_CONTENT_BG)
                cell.bind("<Button-1>", on_single_click)
                canvas.bind("<Button-1>", on_single_click)
                name_label.bind("<Button-1>", on_single_click)
                # --- Double click to open ---
                cell.bind("<Double-Button-1>", lambda e, t=testcase_name, p=project_name: self._show_scanids(p, t, skip_download=True))
                canvas.bind("<Double-Button-1>", lambda e, t=testcase_name, p=project_name: self._show_scanids(p, t, skip_download=True))
                name_label.bind("<Double-Button-1>", lambda e, t=testcase_name, p=project_name: self._show_scanids(p, t, skip_download=True))
                # --- Right click context menu ---
                def show_menu_cell(event, tn=testcase_name, pn=project_name, cell_widget=cell):
                    self.show_context_menu(event, os.path.join(os.getcwd(), 'tmp', pn, tn), 'testcase', tn, lambda: [setattr(self, 'tmp_structure', get_tmp_file_structure()), self._show_testcases(pn)][-1], cell_widget=cell_widget)
                    return "break"
                cell.bind("<Button-3>", show_menu_cell)
                canvas.bind("<Button-3>", show_menu_cell)
                name_label.bind("<Button-3>", show_menu_cell)
            # --- Right click on empty space shows paste menu ---
            def show_bg_menu(event):
                widget = event.widget.winfo_containing(event.x_root, event.y_root)
                if widget not in [c for c in grid_frame.winfo_children()]:
                    self.show_bg_context_menu(event, os.path.join(os.getcwd(), 'tmp', project_name), lambda: [setattr(self, 'tmp_structure', get_tmp_file_structure()), self._show_testcases(project_name)][-1])
            grid_frame.bind("<Button-3>", show_bg_menu)
            outer_frame.bind("<Button-3>", show_bg_menu)
            self.bind("<Button-3>", show_bg_menu)

        def _download_and_extract_testcase(self, project_name, testcase_name, force_download=False):
            """Download and extract test case files if they don't exist or if force_download is True"""
            print(f"[DEBUG] Starting download for test case: {testcase_name} in project: {project_name}")
            release_dir = os.path.join('release', testcase_name)
            extracted_dir = os.path.join(release_dir, 'extracted')
            
            print(f"[DEBUG] Release dir: {release_dir}")
            print(f"[DEBUG] Extracted dir: {extracted_dir}")
            
            # Check if files already exist
            if os.path.exists(extracted_dir):
                print(f"[DEBUG] Extracted directory exists: {extracted_dir}")
                if not force_download:
                    print("[DEBUG] Prompting user for re-download confirmation")
                    if not messagebox.askyesno("Files Exist", 
                                             f"Test case files already exist for {testcase_name}.\n"
                                             "Do you want to download them again?"):
                        print("[DEBUG] User chose not to re-download, using existing files")
                        return extracted_dir  # Return the path without downloading again
                else:
                    print("[DEBUG] Force download is True, proceeding with download")
            else:
                print("[DEBUG] Extracted directory does not exist, will create")
            
            # Create directories if they don't exist
            try:
                print(f"[DEBUG] Creating directories: {extracted_dir}")
                os.makedirs(extracted_dir, exist_ok=True)
                
                # TODO: Implement actual download logic here
                print("[DEBUG] Starting download process...")
                # Example: 
                # download_url = f"{self.base_url}/download/{project_name}/{testcase_name}"
                # print(f"[DEBUG] Downloading from: {download_url}")
                # response = requests.get(download_url, headers={"Authorization": f"Bearer {self.token}"})
                # response.raise_for_status()
                # 
                # print("[DEBUG] Download completed, extracting files...")
                # with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                #     zip_ref.extractall(extracted_dir)
                
                # For now, just create a dummy file to test the flow
                test_file = os.path.join(extracted_dir, "testfile.txt")
                with open(test_file, 'w') as f:
                    f.write(f"Test file for {testcase_name}\n")
                
                print(f"[DEBUG] Successfully created test file: {test_file}")
                messagebox.showinfo("Success", f"Successfully downloaded and extracted test case: {testcase_name}")
                return extracted_dir
                
            except Exception as e:
                error_msg = f"Failed to download test case: {str(e)}"
                print(f"[ERROR] {error_msg}")
                print(f"[ERROR] Exception type: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", error_msg)
                return None

        def _run_automation(self, project_name, testcase_name, extracted_dir):
            """Run the automation for the test case"""
            print(f"[DEBUG] Starting automation for test case: {testcase_name}")
            print(f"[DEBUG] Project: {project_name}")
            print(f"[DEBUG] Extracted dir: {extracted_dir}")
            
            try:
                # Create result directory
                result_dir = os.path.join(os.getcwd(), 'tmp', safe_name(project_name), safe_name(testcase_name), 'results')
                print(f"[DEBUG] Creating result directory: {result_dir}")
                os.makedirs(result_dir, exist_ok=True)
                
                # Verify extracted directory exists and has content
                if not os.path.exists(extracted_dir):
                    error_msg = f"Extracted directory not found: {extracted_dir}"
                    print(f"[ERROR] {error_msg}")
                    messagebox.showerror("Error", error_msg)
                    return
                    
                print("[DEBUG] Starting terminal app with automation...")
                try:
                    # Start the terminal app with the automation
                    run_terminal_app(
                        scan_id=testcase_name,
                        repo_dir=extracted_dir,
                        base_url=self.base_url,
                        folder_path=extracted_dir,
                        result_path=result_dir,
                        agent_name=f"{project_name}_{testcase_name}",
                        on_terminal_close=lambda: print("[DEBUG] Terminal closed"),
                        token=getattr(self, 'token', None),
                        upload_files_endpoint=getattr(self, 'upload_files_endpoint', None),
                        upload_results_endpoint=getattr(self, 'upload_results_endpoint', None)
                    )
                    save_scan_repo_mapping(testcase_name, extracted_dir)
                    print("[DEBUG] Terminal app started successfully")
                except ImportError as ie:
                    error_msg = f"Failed to import required module: {str(ie)}"
                    print(f"[ERROR] {error_msg}")
                    messagebox.showerror("Missing Dependency", error_msg)
                except Exception as e:
                    error_msg = f"Failed to start terminal app: {str(e)}"
                    print(f"[ERROR] {error_msg}")
                    print(f"[ERROR] Exception type: {type(e).__name__}")
                    import traceback
                    traceback.print_exc()
                    messagebox.showerror("Error", error_msg)
                    
            except Exception as e:
                error_msg = f"Failed to run automation: {str(e)}"
                print(f"[ERROR] {error_msg}")
                print(f"[ERROR] Exception type: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", error_msg)

        def _show_scanids(self, project_name, testcase_name, skip_download=False):
            """Show scan IDs for a test case, with optional download and automation"""
            print(f"[DEBUG] _show_scanids called - Project: {project_name}, Test Case: {testcase_name}, Skip Download: {skip_download}")
            
            try:
                if not skip_download:
                    print("[DEBUG] Starting download and extraction process...")
                    # First download and extract the test case
                    extracted_dir = self._download_and_extract_testcase(project_name, testcase_name)
                    
                    if not extracted_dir or not os.path.exists(extracted_dir):
                        error_msg = f"Failed to prepare test case: {testcase_name}"
                        print(f"[ERROR] {error_msg}")
                        messagebox.showerror("Error", error_msg)
                        return
                        
                    print("[DEBUG] Starting automation process...")
                    # Run the automation
                    self._run_automation(project_name, testcase_name, extracted_dir)
                else:
                    print("[DEBUG] Skipping download as requested")
                
                print("[DEBUG] Showing scan IDs view...")
                # Now show the scan IDs
                self._show_scanids_view(project_name, testcase_name)
                
            except Exception as e:
                error_msg = f"Error in _show_scanids: {str(e)}"
                print(f"[ERROR] {error_msg}")
                print(f"[ERROR] Exception type: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", error_msg)
        
        def _show_scanids_view(self, project_name, testcase_name):
            """Show the scan IDs view without triggering download/automation"""
            self._show_scanids_current_testcase = testcase_name
            self.tmp_structure = get_tmp_file_structure()
            for widget in self.winfo_children():
                widget.destroy()
                
            # Ensure the result directory exists
            result_dir = os.path.join(os.getcwd(), 'tmp', safe_name(project_name), safe_name(testcase_name), 'results')
            os.makedirs(result_dir, exist_ok=True)
            title = tk.Label(self, text="Scan IDs", font=("Arial", 18, "bold"), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
            title.pack(anchor="w", padx=0, pady=(10, 0))
            breadcrumb = tk.Frame(self, bg=COLOR_CONTENT_BG)
            breadcrumb.pack(anchor="w", padx=0, pady=(0, 10))
            link_color = '#2986cc'
            hover_color = '#174a7c'
            def go_report(event=None):
                self._show_project_list()
            def go_project(event=None):
                self._show_testcases(project_name)
            report_label = tk.Label(breadcrumb, text="Report", font=("Arial", 12), fg=link_color, bg=COLOR_CONTENT_BG, cursor="hand2")
            report_label.pack(side=tk.LEFT)
            def on_enter_scanids_report(e): report_label.config(fg=hover_color)
            def on_leave_scanids_report(e): report_label.config(fg=link_color)
            report_label.bind("<Enter>", on_enter_scanids_report)
            report_label.bind("<Leave>", on_leave_scanids_report)
            report_label.bind("<Button-1>", go_report)
            sep1 = tk.Label(breadcrumb, text=" > ", font=("Arial", 12), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
            sep1.pack(side=tk.LEFT)
            project_label = tk.Label(breadcrumb, text=project_name, font=("Arial", 12), fg=link_color, bg=COLOR_CONTENT_BG, cursor="hand2")
            project_label.pack(side=tk.LEFT)
            def on_enter_scanids_proj(e): project_label.config(fg=hover_color)
            def on_leave_scanids_proj(e): project_label.config(fg=link_color)
            project_label.bind("<Enter>", on_enter_scanids_proj)
            project_label.bind("<Leave>", on_leave_scanids_proj)
            project_label.bind("<Button-1>", go_project)
            sep2 = tk.Label(breadcrumb, text=" > ", font=("Arial", 12), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
            sep2.pack(side=tk.LEFT)
            testcase_label = tk.Label(breadcrumb, text=testcase_name, font=("Arial", 12), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
            testcase_label.pack(side=tk.LEFT)
            title_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
            title_frame.pack(fill=tk.X, padx=0, pady=(0, 0))
            back_btn = tk.Button(title_frame, text="\u2190 Back", command=lambda: self._show_testcases(project_name), bg=COLOR_PANEL_BG, fg=COLOR_TEXT_LIGHT, font=("Segoe UI", 10, "bold"), relief=tk.FLAT, bd=0, padx=10, pady=5, activebackground=COLOR_PRIMARY, activeforeground=COLOR_TEXT_LIGHT)
            back_btn.pack(side=tk.RIGHT)
            refresh_btn = tk.Button(
                title_frame,
                text="⟳ Refresh",
                command=lambda: self._show_scanids(project_name, testcase_name),
                bg=COLOR_PANEL_BG, fg=COLOR_TEXT_LIGHT,
                font=("Segoe UI", 10, "bold"),
                relief=tk.FLAT, bd=0, padx=10, pady=5,
                activebackground=COLOR_PRIMARY,
                activeforeground=COLOR_TEXT_LIGHT
            )
            refresh_btn.pack(side=tk.RIGHT)
            outer_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
            outer_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
            files_frame = self.create_scrollable_frame(outer_frame, COLOR_CONTENT_BG)
            scanids = list(self.tmp_structure[project_name][testcase_name].keys())
            if not scanids:
                placeholder = tk.Label(files_frame, text=f"No scan id folders found for this testcase.", font=("Arial", 14), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
                placeholder.pack(pady=20)
                return
            # Show scan id folders as a grid
            grid_frame = tk.Frame(files_frame, bg=COLOR_CONTENT_BG)
            grid_frame.pack(fill=tk.BOTH, expand=True)
            folder_size = 80
            max_cols = 6
            for idx, scan_id in enumerate(scanids):
                row = idx // max_cols
                col = idx % max_cols
                cell = tk.Frame(grid_frame, bg=COLOR_CONTENT_BG, highlightthickness=0)
                cell.grid(row=row, column=col, padx=40, pady=30)
                icon_frame = tk.Frame(cell, width=folder_size, height=folder_size, bg=COLOR_CONTENT_BG)
                icon_frame.pack()
                canvas = tk.Canvas(icon_frame, width=folder_size, height=folder_size, bg=COLOR_CONTENT_BG, highlightthickness=0, cursor="hand2")
                # Draw folder icon (like project folder)
                canvas.create_rectangle(10, 30, 70, 70, fill="#FFD966", outline="#FFD966")
                canvas.create_rectangle(20, 15, 50, 40, fill="#FFE599", outline="#FFE599")
                canvas.pack()
                name_label = tk.Label(cell, text=scan_id, font=("Arial", 12), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG, wraplength=110, justify="center")
                name_label.pack(pady=(8, 0))
                def on_double_click(event, sid=scan_id):
                    self._show_scanid_files(project_name, testcase_name, sid)
                for widget in (cell, canvas, name_label):
                    widget.bind("<Double-Button-1>", on_double_click)
                # Do not bind single click to enter

        def _show_scanid_files(self, project_name, testcase_name, scan_id):
            self._show_scanids_current_testcase = testcase_name
            self.tmp_structure = get_tmp_file_structure()
            for widget in self.winfo_children():
                widget.destroy()
            title = tk.Label(self, text=f"Files in {scan_id}", font=("Arial", 18, "bold"), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
            title.pack(anchor="w", padx=0, pady=(10, 0))
            breadcrumb = tk.Frame(self, bg=COLOR_CONTENT_BG)
            breadcrumb.pack(anchor="w", padx=0, pady=(0, 10))
            link_color = '#2986cc'
            hover_color = '#174a7c'
            def go_report(event=None):
                self._show_project_list()
            def go_project(event=None):
                self._show_testcases(project_name)
            def go_scanids(event=None):
                self._show_scanids(project_name, testcase_name)
            report_label = tk.Label(breadcrumb, text="Report", font=("Arial", 12), fg=link_color, bg=COLOR_CONTENT_BG, cursor="hand2")
            report_label.pack(side=tk.LEFT)
            def on_enter_scanids_report(e): report_label.config(fg=hover_color)
            def on_leave_scanids_report(e): report_label.config(fg=link_color)
            report_label.bind("<Enter>", on_enter_scanids_report)
            report_label.bind("<Leave>", on_leave_scanids_report)
            report_label.bind("<Button-1>", go_report)
            sep1 = tk.Label(breadcrumb, text=" > ", font=("Arial", 12), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
            sep1.pack(side=tk.LEFT)
            project_label = tk.Label(breadcrumb, text=project_name, font=("Arial", 12), fg=link_color, bg=COLOR_CONTENT_BG, cursor="hand2")
            project_label.pack(side=tk.LEFT)
            def on_enter_scanids_proj(e): project_label.config(fg=hover_color)
            def on_leave_scanids_proj(e): project_label.config(fg=link_color)
            project_label.bind("<Enter>", on_enter_scanids_proj)
            project_label.bind("<Leave>", on_leave_scanids_proj)
            project_label.bind("<Button-1>", go_project)
            sep2 = tk.Label(breadcrumb, text=" > ", font=("Arial", 12), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
            sep2.pack(side=tk.LEFT)
            testcase_label = tk.Label(breadcrumb, text=testcase_name, font=("Arial", 12), fg=link_color, bg=COLOR_CONTENT_BG, cursor="hand2")
            testcase_label.pack(side=tk.LEFT)
            def on_enter_testcase(e): testcase_label.config(fg=hover_color)
            def on_leave_testcase(e): testcase_label.config(fg=link_color)
            testcase_label.bind("<Enter>", on_enter_testcase)
            testcase_label.bind("<Leave>", on_leave_testcase)
            testcase_label.bind("<Button-1>", go_scanids)
            sep3 = tk.Label(breadcrumb, text=" > ", font=("Arial", 12), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
            sep3.pack(side=tk.LEFT)
            scanid_label = tk.Label(breadcrumb, text=scan_id, font=("Arial", 12), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
            scanid_label.pack(side=tk.LEFT)
            title_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
            title_frame.pack(fill=tk.X, padx=0, pady=(0, 0))
            back_btn = tk.Button(title_frame, text="\u2190 Back", command=lambda: self._show_scanids(project_name, testcase_name), bg=COLOR_PANEL_BG, fg=COLOR_TEXT_LIGHT, font=("Segoe UI", 10, "bold"), relief=tk.FLAT, bd=0, padx=10, pady=5, activebackground=COLOR_PRIMARY, activeforeground=COLOR_TEXT_LIGHT)
            back_btn.pack(side=tk.RIGHT)
            refresh_btn = tk.Button(
                title_frame,
                text="⟳ Refresh",
                command=lambda: self._show_scanid_files(project_name, testcase_name, scan_id),
                bg=COLOR_PANEL_BG, fg=COLOR_TEXT_LIGHT,
                font=("Segoe UI", 10, "bold"),
                relief=tk.FLAT, bd=0, padx=10, pady=5,
                activebackground=COLOR_PRIMARY,
                activeforeground=COLOR_TEXT_LIGHT
            )
            refresh_btn.pack(side=tk.RIGHT)
            outer_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
            outer_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
            files_frame = self.create_scrollable_frame(outer_frame, COLOR_CONTENT_BG)
            files = self.tmp_structure[project_name][testcase_name][scan_id]
            if not files:
                placeholder = tk.Label(files_frame, text=f"No files found in scan id {scan_id}.", font=("Arial", 14), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
                placeholder.pack(pady=20)
                return
            selection_frame = tk.Frame(files_frame, bg=COLOR_CONTENT_BG)
            selection_frame.pack(anchor="nw", padx=10, pady=(0, 10))
            select_all_var = tk.BooleanVar(value=False)
            selected_files = set()
            self.selected_files = selected_files  # <-- Make selected_files accessible to context menu
            file_cells = []
            tick_canvases = []
            def update_file_ticks():
                for idx, cell in enumerate(file_cells):
                    tick_canvas = tick_canvases[idx]
                    fname = files[idx]
                    tick_canvas.place_forget()
                    if fname in selected_files:
                        tick_canvas.config(width=22, height=22, bg=COLOR_CONTENT_BG, highlightthickness=0, bd=0)
                        tick_canvas.place(relx=1.0, rely=0.0, anchor="ne", x=-6, y=6)
                        tick_canvas.delete("all")
                        tick_canvas.create_rectangle(2,2,20,20, fill="white", outline="#555", width=2)
                        tick_canvas.create_line(6,12,10,16,16,6, fill="black", width=3, capstyle="round", joinstyle="round")
                    else:
                        tick_canvas.place_forget()
            def on_select_all():
                if select_all_var.get():
                    selected_files.clear()
                    selected_files.update(files)
                else:
                    selected_files.clear()
                update_file_ticks()
            select_all_cb = tk.Checkbutton(selection_frame, text="Select All", variable=select_all_var, command=on_select_all, bg=COLOR_PANEL_BG, fg=COLOR_TEXT_LIGHT, selectcolor="#232323", activebackground=COLOR_PANEL_BG, activeforeground=COLOR_TEXT_LIGHT, font=("Arial", 11, "bold"), bd=0, highlightthickness=0, padx=16, pady=8)
            select_all_cb.configure(indicatoron=True, borderwidth=0, relief=tk.FLAT)
            select_all_cb.pack(side=tk.LEFT, padx=(0, 20), ipadx=8, ipady=2)
            grid_frame = tk.Frame(files_frame, bg=COLOR_CONTENT_BG)
            grid_frame.pack(fill=tk.BOTH, expand=True)
            folder_size = 80
            max_cols = 8
            highlighted_idx = [None]
            def highlight_cell(idx):
                for i, cell in enumerate(file_cells):
                    if i == idx:
                        if isinstance(cell, (tk.Frame, tk.Label)):
                            cell.config(bg="#232323")
                        for w in cell.winfo_children():
                            if isinstance(w, (tk.Frame, tk.Label)):
                                w.config(bg="#232323")
                    else:
                        if isinstance(cell, (tk.Frame, tk.Label)):
                            cell.config(bg=COLOR_CONTENT_BG)
                        for w in cell.winfo_children():
                            if isinstance(w, (tk.Frame, tk.Label)):
                                w.config(bg=COLOR_CONTENT_BG)
                highlighted_idx[0] = idx
            def unselect_file(idx):
                fname = files[idx]
                if fname in selected_files:
                    selected_files.remove(fname)
                    update_file_ticks()
            def update_select_all_checkbox():
                if len(selected_files) == len(files):
                    select_all_var.set(True)
                else:
                    select_all_var.set(False)
            for idx, rel_path in enumerate(files):
                row = idx // max_cols
                col = idx % max_cols
                cell = tk.Frame(grid_frame, bg=COLOR_CONTENT_BG, highlightthickness=0)
                cell.grid(row=row, column=col, padx=40, pady=30)
                file_cells.append(cell)
                icon_frame = tk.Frame(cell, width=folder_size, height=folder_size, bg=COLOR_CONTENT_BG)
                icon_frame.pack()
                ext = rel_path.lower().split('.')[-1]
                canvas = tk.Canvas(icon_frame, width=folder_size, height=folder_size, bg=COLOR_CONTENT_BG, highlightthickness=0, cursor="hand2")
                icon_drawn = False
                src_path = os.path.join(os.getcwd(), 'tmp', project_name, testcase_name, rel_path)
                if ext in ["png", "jpg", "jpeg"]:
                    try:
                        from PIL import Image, ImageTk
                        img = Image.open(src_path)
                        img.thumbnail((folder_size-10, folder_size-10))
                        photo = ImageTk.PhotoImage(img)
                        canvas.create_rectangle(5, 5, folder_size-5, folder_size-5, fill="#222", outline="#555")
                        canvas.create_image(folder_size//2, folder_size//2, image=photo)
                        canvas.image = photo
                        icon_drawn = True
                    except Exception:
                        pass
                if not icon_drawn and ext == "docx":
                    canvas.create_rectangle(15, 15, 65, 65, fill="#3A70C7", outline="#3A70C7")
                    canvas.create_rectangle(15, 15, 65, 35, fill="#5A9BEF", outline="#5A9BEF")
                    canvas.create_text(folder_size//2, folder_size//2+10, text="DOCX", fill="white", font=("Arial", 12, "bold"))
                    icon_drawn = True
                if not icon_drawn and ext == "json":
                    canvas.create_rectangle(15, 15, 65, 65, fill="#F7DF1E", outline="#F7DF1E")
                    canvas.create_text(folder_size//2, folder_size//2, text="JSON", fill="#222", font=("Arial", 12, "bold"))
                    icon_drawn = True
                if not icon_drawn and ext == "pcap":
                    canvas.create_rectangle(15, 15, 65, 65, fill="#FF9800", outline="#FF9800")
                    canvas.create_text(folder_size//2, folder_size//2, text="PCAP", fill="white", font=("Arial", 12, "bold"))
                    icon_drawn = True
                if not icon_drawn and ext == "mp4":
                    canvas.create_rectangle(15, 15, 65, 65, fill="#222", outline="#222")
                    canvas.create_polygon(35, 30, 55, 40, 35, 50, fill="#E74C3C", outline="#E74C3C")
                    canvas.create_text(folder_size//2, 60, text="MP4", fill="white", font=("Arial", 10, "bold"))
                    icon_drawn = True
                if not icon_drawn:
                    canvas.create_rectangle(18, 18, 62, 62, fill="#bbb", outline="#bbb")
                    canvas.create_rectangle(18, 18, 62, 35, fill="#eee", outline="#eee")
                    canvas.create_text(folder_size//2, folder_size//2+10, text="FILE", fill="#444", font=("Arial", 12, "bold"))
                canvas.pack()
                tick_canvas = tk.Canvas(icon_frame, width=22, height=22, bg=COLOR_CONTENT_BG, highlightthickness=0, bd=0)
                tick_canvas.pack(anchor="ne", padx=2, pady=2)
                tick_canvases.append(tick_canvas)
                name_label = tk.Label(cell, text=os.path.basename(rel_path), font=("Arial", 12), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG, wraplength=110, justify="center")
                name_label.pack(pady=(8, 0))
                def on_double_click(event, f=rel_path):
                    self.preview_file(f, os.path.join(os.getcwd(), 'tmp', project_name, testcase_name, scan_id))
                def on_enter(event, fr=cell):
                    fr.config(bg="#232323")
                    for w in fr.winfo_children():
                        w.config(bg="#232323")
                def on_leave(event, fr=cell):
                    if highlighted_idx[0] == idx:
                        fr.config(bg="#232323")
                        for w in fr.winfo_children():
                            w.config(bg="#232323")
                    else:
                        fr.config(bg=COLOR_CONTENT_BG)
                        for w in fr.winfo_children():
                            w.config(bg=COLOR_CONTENT_BG)
                def on_single_click(event, idx=idx):
                    highlight_cell(idx)
                    fname = files[idx]
                    if fname in selected_files:
                        selected_files.remove(fname)
                    else:
                        selected_files.add(fname)
                    update_file_ticks()
                    update_select_all_checkbox()
                single_click_handler = functools.partial(on_single_click, idx=idx)
                cell.bind("<Double-Button-1>", on_double_click)
                canvas.bind("<Double-Button-1>", on_double_click)
                name_label.bind("<Double-Button-1>", on_double_click)
                cell.bind("<Button-1>", single_click_handler)
                canvas.bind("<Button-1>", single_click_handler)
                name_label.bind("<Button-1>", single_click_handler)
                cell.bind("<Enter>", on_enter)
                cell.bind("<Leave>", on_leave)
                canvas.bind("<Enter>", on_enter)
                canvas.bind("<Leave>", on_leave)
                name_label.bind("<Enter>", on_enter)
                name_label.bind("<Leave>", on_leave)
                # Attach right-click context menu for files
                for widget in (cell, canvas, name_label):
                    src_path = os.path.join(os.getcwd(), 'tmp', project_name, testcase_name, scan_id, rel_path)
                    widget.bind("<Button-3>", lambda e, p=src_path, f=rel_path: self.show_context_menu(
                        e, p, 'file', f, lambda: [setattr(self, 'tmp_structure', get_tmp_file_structure()), self._show_scanid_files(project_name, testcase_name, scan_id)][-1], parent_path=os.path.join(os.getcwd(), 'tmp', project_name, testcase_name, scan_id), cell_widget=cell))
            update_file_ticks()

            # --- Send To Server Button (bottom right, small) ---
            def show_uploading_popup():
                self.uploading_popup = tk.Toplevel(self)
                self.uploading_popup.title("Uploading...")
                self.uploading_popup.geometry("300x100")
                self.uploading_popup.configure(bg=COLOR_CONTENT_BG)
                self.uploading_popup.transient(self.winfo_toplevel())
                self.uploading_popup.grab_set()
                label = tk.Label(self.uploading_popup, text="Uploading files...", font=("Arial", 14, "bold"), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
                label.pack(expand=True, fill="both", pady=20)
                self._upload_anim_running = True
                def animate():
                    if not getattr(self, '_upload_anim_running', False):
                        return
                    dots = animate.counter % 4
                    label.config(text="Uploading files" + "." * dots)
                    animate.counter += 1
                    self.uploading_popup.after(400, animate)
                animate.counter = 0
                animate()
            def hide_uploading_popup():
                self._upload_anim_running = False
                if hasattr(self, 'uploading_popup') and self.uploading_popup:
                    self.uploading_popup.grab_release()
                    self.uploading_popup.destroy()
                    self.uploading_popup = None
            def send_to_server():
                from tkinter import messagebox
                import os
                print(f"[DEBUG] Starting upload process...")
                print(f"[DEBUG] Selected files: {selected_files}")
                print(f"[DEBUG] Scan ID: {scan_id}")
                print(f"[DEBUG] Project name: {project_name}")
                print(f"[DEBUG] Test case name: {testcase_name}")
                
                send_btn.config(state='disabled')
                show_uploading_popup()
                file_paths = [os.path.join(os.getcwd(), 'tmp', project_name, testcase_name, scan_id, fname) for fname in selected_files]
                repo_dir = get_repo_dir_for_scan(scan_id)
                print(f"[DEBUG] File paths: {file_paths}")
                print(f"[DEBUG] Repo dir: {repo_dir}")
                def do_upload():
                    try:
                        if not repo_dir:
                            self.after(0, hide_uploading_popup)
                            self.after(0, lambda: messagebox.showerror("Error", f"No repo_dir found for scan_id {scan_id}"))
                            self.after(0, lambda: send_btn.config(state='normal'))
                            return
                        if not file_paths:
                            self.after(0, hide_uploading_popup)
                            self.after(0, lambda: messagebox.showwarning("No Files", "No files selected to upload."))
                            self.after(0, lambda: send_btn.config(state='normal'))
                            return
                        
                        # Upload files first
                        files_upload_success = self.upload_files_via_http(file_paths, repo_dir=repo_dir)
                        
                        # Upload metadata
                        metadata = {
                            'agent_name': getattr(self, 'agent_id', 'unknown'),
                            'scan_id': scan_id,
                            'repo_dir': testcase_name,
                            'files': list(selected_files)
                        }
                        results_upload_success = self.upload_results(metadata)
                        
                        # Show appropriate message based on upload results
                        self.after(0, lambda: send_btn.config(state='normal'))
                        self.after(0, hide_uploading_popup)
                        
                        if files_upload_success and results_upload_success:
                            self.after(0, lambda: messagebox.showinfo("Upload Success", "Documentation uploaded successfully!"))
                        elif files_upload_success:
                            self.after(0, lambda: messagebox.showwarning("Partial Upload", "Files uploaded but metadata upload failed."))
                        elif results_upload_success:
                            self.after(0, lambda: messagebox.showwarning("Partial Upload", "Metadata uploaded but files upload failed."))
                        else:
                            self.after(0, lambda: messagebox.showerror("Upload Failed", "Both files and metadata upload failed."))
                            
                    except Exception as e:
                        print(f"Exception during upload: {e}")
                        self.after(0, hide_uploading_popup)
                        self.after(0, lambda: messagebox.showerror("Upload Error", f"Unexpected error: {e}"))
                        self.after(0, lambda: send_btn.config(state='normal'))
                import threading
                threading.Thread(target=do_upload, daemon=True).start()

            send_btn = tk.Button(
                outer_frame,
                text="Send To Server",
                bg=COLOR_PRIMARY,
                fg=COLOR_TEXT_LIGHT,
                font=("Arial", 12, "bold"),
                relief=tk.FLAT,
                bd=0,
                padx=18,
                pady=8,
                activebackground=COLOR_PRIMARY,
                activeforeground=COLOR_TEXT_LIGHT,
                command=send_to_server,
                state='normal',
                cursor='hand2',
                highlightthickness=0
            )
            send_btn.place(relx=1.0, rely=1.0, anchor="se", x=-32, y=-32)

        def preview_file(self, fname, files_path):
            import os
            import subprocess
            from tkinter import messagebox, Toplevel, scrolledtext
            from PIL import Image, ImageTk
            import json
            ext = fname.lower().split('.')[-1]
            
            # Use /home/$user/tmp path for deb package
            home_dir = os.path.expanduser('~')
            abs_files_path = os.path.join(home_dir, 'tmp', os.path.relpath(files_path, 'tmp'))
            src_path = os.path.join(abs_files_path, fname)
            cwd = os.getcwd()
            exists = os.path.exists(src_path)
            print(f"[DEBUG] preview_file: src_path={src_path}, exists={exists}, cwd={cwd}, abs_files_path={abs_files_path}")
            if not exists:
                messagebox.showerror("File Not Found", f"The file does not exist:\n{src_path}\nCurrent working directory: {cwd}\nExists: {exists}")
                return
            # 16:9 centered, not fullscreen, with window decorations
            screen_width = self.winfo_toplevel().winfo_screenwidth()
            screen_height = self.winfo_toplevel().winfo_screenheight()
            max_width = int(screen_width * 0.8)
            max_height = int(screen_height * 0.8)
            ratio_width = max_width
            ratio_height = int(ratio_width * 9 / 16)
            if ratio_height > max_height:
                ratio_height = max_height
                ratio_width = int(ratio_height * 16 / 9)
            width, height = ratio_width, ratio_height
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
            if ext in ["png", "jpg", "jpeg"]:
                img = Image.open(src_path)
                img = img.copy()
                img.thumbnail((width, height), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                win = Toplevel(self)
                win.title(fname)
                win.configure(bg=COLOR_CONTENT_BG)
                win.geometry(f"{width}x{height}+{x}+{y}")
                win.resizable(True, True)
                lbl = tk.Label(win, image=photo, bg=COLOR_CONTENT_BG)
                lbl.image = photo
                lbl.pack(expand=True, fill="both")
            elif ext == "docx":
                try:
                    subprocess.Popen(["libreoffice", src_path])
                except Exception as e:
                    messagebox.showerror("Preview Error", f"Could not open DOCX: {e}")
            elif ext == "pcap":
                try:
                    subprocess.Popen(["wireshark", src_path])
                except Exception as e:
                    messagebox.showinfo("Preview", f"Could not open pcap in Wireshark: {e}")
            elif ext in ["txt", "log", "json"]:
                win = Toplevel(self)
                win.title(fname)
                win.configure(bg=COLOR_CONTENT_BG)
                win.geometry(f"{width}x{height}+{x}+{y}")
                win.resizable(True, True)
                if ext == "json":
                    try:
                        with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
                            data = json.load(f)
                        content = json.dumps(data, indent=4)
                    except Exception:
                        with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                else:
                    with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                txt = scrolledtext.ScrolledText(win, width=80, height=30, bg=COLOR_PANEL_BG, fg=COLOR_TEXT_LIGHT, insertbackground=COLOR_TEXT_LIGHT)
                txt.insert(tk.END, content)
                txt.pack(expand=True, fill="both")
                bind_text_mousewheel(txt)
                def block_edit(event):
                    return "break"
                txt.bind("<Key>", block_edit)
            else:
                try:
                    subprocess.Popen(["xdg-open", src_path])
                except Exception as e:
                    messagebox.showinfo("Preview", f"No preview available for this file type: {ext}\nSystem could not open the file.\nError: {e}")

        def upload_files_via_http(self, file_paths, repo_dir):
            import requests
            from tkinter import messagebox

            print(f"[DEBUG] upload_files_via_http called with {len(file_paths)} files")
            print(f"[DEBUG] File paths: {file_paths}")
            print(f"[DEBUG] Repo dir: {repo_dir}")

            try:
                # Get fresh token from configuration file to avoid stale token issues
                current_token = None
                try:
                    with open('client.conf.json', 'r') as f:
                        config = json.load(f)
                        current_token = config.get('token')
                        print(f"[DEBUG] Token loaded from config: {current_token[:20] if current_token else 'None'}...")
                except Exception as e:
                    print(f"Error reading token from config: {e}")
                    # Fallback to stored token if config read fails
                    current_token = self.token
                    print(f"[DEBUG] Using fallback token: {current_token[:20] if current_token else 'None'}...")

                files_to_upload = []
                for file_path in file_paths:
                    filename = os.path.basename(file_path)
                    files_to_upload.append(('files', (filename, open(file_path, 'rb'))))

                if files_to_upload:
                    data = {'repo_dir': repo_dir}
                    headers = {"Authorization": f"Bearer {current_token}"}
                    upload_url = self.base_url + 'api/scan/upload_files'
                    print(f"[DEBUG] Uploading files to: {upload_url}")
                    print(f"[DEBUG] Headers: {headers}")
                    print(f"[DEBUG] Data: {data}")
                    print(f"[DEBUG] Files to upload: {[f[1][0] for f in files_to_upload]}")
                    
                    response = requests.post(
                        upload_url,
                        files=files_to_upload,
                        data=data,
                        headers=headers
                    )
                    print(f"[DEBUG] Response status: {response.status_code}")
                    # print(f"[DEBUG] Response text: {response.text}")
                    response.raise_for_status()
                    print("Files uploaded successfully to server")
                    return True  # Return success status
                else:
                    print("No files selected to upload")
                    return False
            except requests.RequestException as e:
                print(f"Error uploading files to server: {e}")
                return False
            except Exception as e:
                print(f"Unexpected error during file upload: {e}")
                return False

        def upload_results(self, data):
            import requests
            from tkinter import messagebox

            print(f"[DEBUG] upload_results called with data: {data}")

            try:
                # Get fresh token from configuration file to avoid stale token issues
                current_token = None
                try:
                    with open('client.conf.json', 'r') as f:
                        config = json.load(f)
                        current_token = config.get('token')
                        print(f"[DEBUG] Token loaded from config: {current_token[:20] if current_token else 'None'}...")
                except Exception as e:
                    print(f"Error reading token from config: {e}")
                    # Fallback to stored token if config read fails
                    current_token = self.token
                    print(f"[DEBUG] Using fallback token: {current_token[:20] if current_token else 'None'}...")

                headers = {"Authorization": f"Bearer {current_token}"}
                upload_url = self.base_url + 'api/scan/upload'
                print(f"[DEBUG] Uploading results to: {upload_url}")
                print(f"[DEBUG] Headers: {headers}")
                print(f"[DEBUG] Data: {data}")
                
                response = requests.post(
                    upload_url,
                    json=data,
                    headers=headers
                )
                print(f"[DEBUG] Response status: {response.status_code}")
                # print(f"[DEBUG] Response text: {response.text}")
                response.raise_for_status()
                print("Scan results uploaded successfully to server")
                return True  # Return success status
            except requests.RequestException as e:
                print(f"Error sending data to server: {e}")
                return False
            except Exception as e:
                print(f"Unexpected error during results upload: {e}")
                return False


        def show_bg_context_menu(self, event, parent_path, refresh_callback):
            import shutil, os
            menu = tk.Menu(event.widget, tearoff=0, fg=COLOR_TEXT_LIGHT, bg=COLOR_PANEL_BG,
                           activeforeground=COLOR_TEXT_LIGHT, activebackground=COLOR_PRIMARY)
            def paste_bg_cmd():
                if not self.clipboard_item:
                    return
                src, src_type, src_name = self.clipboard_item
                try:
                    import os, shutil
                    if os.path.isdir(src):
                        dest_dir = parent_path
                        unique_name = get_unique_name(dest_dir, os.path.basename(src))
                        dest = os.path.join(dest_dir, unique_name)
                        if is_subpath(dest, src):
                            messagebox.showerror("Paste Error", "Cannot paste a folder into itself or its subfolder.")
                            return
                        shutil.copytree(src, dest)
                    else:
                        dest_dir = parent_path
                        unique_name = get_unique_name(dest_dir, os.path.basename(src))
                        dest = os.path.join(dest_dir, unique_name)
                        shutil.copy2(src, dest)
                    self.clipboard_item = None
                    self.clear_copied_highlight()
                    refresh_callback()
                    self.update_idletasks()
                    # Only show error if destination does not exist
                    if not os.path.exists(dest):
                        messagebox.showerror("Paste Error", f"Failed to paste: Destination was not created.")
                except Exception as e:
                    if 'dest' in locals() and os.path.exists(dest):
                        # Paste actually succeeded, suppress error
                        pass
                    else:
                        try:
                            root = self.winfo_toplevel()
                            if root and root.winfo_exists():
                                messagebox.showerror("Paste Error", f"Failed to paste: {e}", parent=root)
                        except Exception:
                            pass
            menu.add_command(label="Copy", state="disabled")
            menu.add_command(label="Paste", command=paste_bg_cmd, state="normal" if self.clipboard_item else "disabled")
            menu.add_command(label="Rename", state="disabled")
            menu.add_command(label="Delete", state="disabled")
            menu.tk_popup(event.x_root, event.y_root)

            # Remove any previous send_btn if it exists (avoid duplicates)
            for widget in files_frame.winfo_children():
                if isinstance(widget, tk.Button) and widget.cget('text') == 'Send to server':
                    widget.destroy()

      

    # ============================================
    # End of MODIFIED ProjectPage Class
    # ============================================


    # ============================================
    # NEW JobPage Class (based on ProjectPage) - Dark Theme
    # ============================================
    class JobPage(tk.Frame):
        def __init__(self, parent, switch_page_callback=None):
            super().__init__(parent, bg=COLOR_CONTENT_BG) # Dark Content BG
            self.switch_page_callback = switch_page_callback

            self.horizontal_padding = 15
            self.row_start_x = 10
            self.scrollbar_width_approx = 20
            self.col_proportions = [0.35, 0.30, 0.20, 0.15]
            self.min_col_widths = [180, 150, 100, 90]
            self.min_total_content_width = self.row_start_x + sum(self.min_col_widths) + self.horizontal_padding
            self.headers = ["Jobs", "Project", "Reporter", "Status"]
            self.current_col_widths = list(self.min_col_widths)
            self.current_content_width = self.min_total_content_width
            self.header_height = 45
            self.row_height = 75
          
            self.row_y_coords = {}
            self.hover_rect_id = None
            self.current_hover_row = -1
            self._draw_scheduled = None

            # Title uses Dark BG, Light FG
            title_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
            title_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
            title = tk.Label(title_frame, text="Jobs", font=("Arial", 18, "bold"), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
            title.pack(side=tk.LEFT)

            # Table area uses Dark BG
            table_area_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
            table_area_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
            table_area_frame.grid_rowconfigure(0, weight=1)
            table_area_frame.grid_columnconfigure(0, weight=1)

            # Canvas uses Dark Panel BG, Dark Border
            self.canvas = tk.Canvas(table_area_frame, bg=COLOR_PANEL_BG, bd=0,
                                    highlightthickness=1, highlightbackground=COLOR_BORDER_MEDIUM)
            self.canvas.grid(row=0, column=0, sticky="nsew")

            # Use styled scrollbars
            v_scrollbar = ttk.Scrollbar(table_area_frame, orient="vertical", command=self.canvas.yview, style="Vertical.TScrollbar")
            v_scrollbar.grid(row=0, column=1, sticky="ns")
            self.canvas.configure(yscrollcommand=v_scrollbar.set)

            h_scrollbar = ttk.Scrollbar(table_area_frame, orient="horizontal", command=self.canvas.xview, style="Horizontal.TScrollbar")
            h_scrollbar.grid(row=1, column=0, sticky="ew")
            self.canvas.configure(xscrollcommand=h_scrollbar.set)

            self.canvas.bind("<Motion>", self._on_motion)
            self.canvas.bind("<Leave>", self._on_leave)
            self.canvas.bind("<Double-1>", self._on_double_click)
            self.canvas.bind("<Configure>", self._on_canvas_configure_debounced)
            self.canvas.bind("<Enter>", lambda _: self.canvas.focus_set())
            self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
            self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))
            self.canvas.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        
        def load_jobs_from_agent_data(self, agent_data):
            self.jobs_data = []  # Clear existing jobs

            try:
                for project in agent_data.get("data", []):
                    project_name = project.get("project_name", "Unknown Project")
                    reporter = project.get("reporting_manager", "Unknown")
                    subtypes = project.get("subtypes_status", [])

                    if not subtypes:  # Still add the project with empty subtype
                        continue;
                    else:
                        for subtype in subtypes:
                            job_name = subtype.get("type", "Unnamed Task")
                            status = subtype.get("status", "Pending")
                            # Map status to dashboard categories
                            status_lower = status.strip().lower()
                            if status_lower in ("to-do", "todo", "pending", "not yet started"):
                                mapped_status = "Not Yet Started"
                            elif status_lower in ("in progress", "progress"):
                                mapped_status = "In Progress"
                            elif status_lower in ("done", "completed"):
                                mapped_status = "Completed"
                            else:
                                mapped_status = status

                            self.jobs_data.append((
                                job_name,
                                project_name,
                                reporter,
                                mapped_status
                            ))

                self.trigger_redraw()
                if 'update_status_counts_from_jobs' in locals():
                    update_status_counts_from_jobs()
                # After jobs data is updated, update dashboard status counts
                if 'update_status_counts_from_jobs' in locals():
                    update_status_counts_from_jobs()
               

            except Exception as e:
                print(f"Error loading jobs from agent data: {e}")

        # --- Layout calculation method (copied) ---
        def _update_layout(self, available_width):
            usable_width = available_width - self.row_start_x - self.horizontal_padding
            if usable_width < (sum(self.min_col_widths)):
                self.current_col_widths = list(self.min_col_widths)
                self.current_content_width = self.min_total_content_width
            else:
                total_proportion = sum(self.col_proportions)
                calculated_widths = []
                extra_space_per_proportion = usable_width / total_proportion
                for i, prop in enumerate(self.col_proportions):
                    calc_w = int(prop * extra_space_per_proportion)
                    actual_w = max(self.min_col_widths[i], calc_w)
                    calculated_widths.append(actual_w)
                current_sum = sum(calculated_widths)
                remainder = usable_width - current_sum
                if remainder > 0:
                    eligible_indices = [i for i, w in enumerate(calculated_widths) if w > self.min_col_widths[i]]
                    if eligible_indices:
                        prop_sum_eligible = sum(self.col_proportions[i] for i in eligible_indices)
                        if prop_sum_eligible > 0:
                            added_so_far = 0
                            for i in eligible_indices[:-1]:
                                add_amount = int(remainder * (self.col_proportions[i] / prop_sum_eligible))
                                calculated_widths[i] += add_amount
                                added_so_far += add_amount
                            calculated_widths[eligible_indices[-1]] += (remainder - added_so_far)
                self.current_col_widths = calculated_widths
                self.current_content_width = self.row_start_x + sum(self.current_col_widths) + self.horizontal_padding

        # --- Table Drawing Logic (adapted for JobPage & Dark Theme) ---
        def _draw_table(self):
            """Draws the entire jobs table content onto the canvas."""
            if not self.winfo_exists() or not self.canvas.winfo_exists(): return
            try:
                current_canvas_width = self.canvas.winfo_width()
                if current_canvas_width <= 1:
                    self._schedule_redraw()
                    return
                self._update_layout(current_canvas_width)
                self.canvas.delete("all")
                self.row_y_coords.clear()
                self.hover_rect_id = None
                draw_width = max(current_canvas_width, self.current_content_width)
                if not self.canvas.winfo_exists():
                    return

                # Draw Header Background & Text (Dark Theme)
                self.canvas.create_rectangle(0, 0, draw_width, self.header_height, fill=COLOR_HEADER_BG, outline="", tags=("header_bg", "header"))
                x_header = self.row_start_x
                y_header_text = self.header_height / 2
                for i, header in enumerate(self.headers):
                    if i < len(self.current_col_widths):
                        col_w = self.current_col_widths[i]
                        self.canvas.create_text(x_header + self.horizontal_padding, y_header_text, text=header, anchor='w',
                                                font=TABLE_FONT_HEADER, fill=COLOR_TEXT_HEADER, tags=("header_text", "header"))
                        x_header += col_w
                    else: break
                header_line_end_x = self.row_start_x + sum(self.current_col_widths)
                self.canvas.create_line(self.row_start_x, self.header_height, header_line_end_x, self.header_height,
                                        fill=COLOR_BORDER_LIGHT, tags=("header_line", "header"))

                y_current = self.header_height
                for i, job_data in enumerate(self.jobs_data):
                    if not self.canvas.winfo_exists(): break
                    self._draw_row(y_current, job_data, i, self.current_col_widths)
                    self.row_y_coords[i] = (y_current, y_current + self.row_height)
                    y_current += self.row_height

                total_content_height = y_current
                self.canvas.config(scrollregion=(0, 0, self.current_content_width, total_content_height))
                self._redraw_hover()

            except tk.TclError as e: print(f"TclError during job table draw: {e}")
            except Exception as e: print(f"Unexpected error during job table draw: {e}")
            finally: self._draw_scheduled = None

        # --- Row Drawing Logic (adapted for JobPage data & Dark Theme) ---
        def _draw_row(self, y_pos, data, index, current_widths):
            """Draws a single job row onto the canvas."""
            if not self.canvas.winfo_exists() or len(current_widths) != len(self.headers): return
            try:
                job_name, project_name, reporter_name, status = data
                x = self.row_start_x
                row_center_y = y_pos + self.row_height / 2
                top_padding = 6
                row_tags = (f"row_{index}", "job_row")
                row_end_x = self.row_start_x + sum(current_widths)

                # Col 1: Job Name (Bold, Light Text)
                col_w = current_widths[0]
                job_wrap_width = max(20, col_w - (self.horizontal_padding * 1.5))
                self.canvas.create_text(x + self.horizontal_padding, y_pos + top_padding, text=job_name, anchor='nw',
                                        font=TABLE_FONT_BODY_BOLD, fill=COLOR_TEXT_LIGHT, # Bold, Light Text
                                        width=job_wrap_width, tags=row_tags)
                x += col_w

                # Col 2: Project Name (Secondary Light Text)
                col_w = current_widths[1]
                project_wrap_width = max(20, col_w - (self.horizontal_padding * 1.5))
                self.canvas.create_text(x + self.horizontal_padding, y_pos + top_padding, text=project_name, anchor='nw',
                                        font=TABLE_FONT_BODY_REGULAR, fill=COLOR_TEXT_SECONDARY_TABLE,
                                        width=project_wrap_width, tags=row_tags)
                x += col_w

                # Col 3: Reporter Name (Secondary Light Text)
                col_w = current_widths[2]
                reporter_wrap_width = max(20, col_w - (self.horizontal_padding * 1.5))
                self.canvas.create_text(x + self.horizontal_padding, y_pos + top_padding, text=reporter_name, anchor='nw',
                                        font=TABLE_FONT_BODY_REGULAR, fill=COLOR_TEXT_SECONDARY_TABLE,
                                        width=reporter_wrap_width, tags=row_tags)
                x += col_w

                # Col 4: Status Badge (Use Dark Theme Status Colors)
                col_w = current_widths[3]
                status_box_width, status_box_height = 130, 22
                badge_x_offset = max(self.horizontal_padding/2, (col_w - status_box_width) / 12)
                status_box_x = x + badge_x_offset
                status_box_y = y_pos + 10 

                status_map = { # Dark Theme Map
                    "In Progress": (COLOR_STATUS_INPROGRESS_BG, COLOR_STATUS_INPROGRESS_FG),
                    "Completed": (COLOR_STATUS_COMPLETED_BG, COLOR_STATUS_COMPLETED_FG),
                    "No Task": (COLOR_STATUS_PENDING_BG, COLOR_STATUS_PENDING_FG),
                    "Blocked": (COLOR_STATUS_BLOCKED_BG, COLOR_STATUS_BLOCKED_FG),
                }
                status_bg, status_fg = status_map.get(status, (COLOR_STATUS_DEFAULT_BG, COLOR_STATUS_DEFAULT_FG))

                if all(math.isfinite(c) for c in [status_box_x, status_box_y]):
                    draw_rounded_rectangle(self.canvas, status_box_x, status_box_y, status_box_x + status_box_width, status_box_y + status_box_height,
                                    radius=8, fill=status_bg, outline="", tags=row_tags + ("status_badge",))
                    self.canvas.create_text(status_box_x + status_box_width / 2, status_box_y + status_box_height / 2,
                                        text=status, font=TABLE_FONT_STATUS, fill=status_fg, tags=row_tags + ("status_text",))
                x += col_w

                # Row Separator Line (Dark theme border)
                self.canvas.create_line(self.row_start_x, y_pos + self.row_height, row_end_x, y_pos + self.row_height,
                                        fill=COLOR_BORDER_LIGHT, tags=row_tags + ("separator",))
            except tk.TclError as e: print(f"TclError drawing job row {index}: {e}")
            except Exception as e: print(f"Unexpected error drawing job row {index}: {e}")

        # --- Event Handlers (copied, hover uses dark theme color) ---
        def _find_row_at_y(self, canvas_y):
            if not math.isfinite(canvas_y): return -1
            for i, (y1, y2) in self.row_y_coords.items():
                if math.isfinite(y1) and math.isfinite(y2):
                    if y1 <= canvas_y < y2: return i
            return -1

        def _redraw_hover(self):
            if not self.canvas.winfo_exists(): return
            try:
                hover_end_x = self.row_start_x + sum(self.current_col_widths)
                if self.hover_rect_id and self.hover_rect_id in self.canvas.find_all():
                    self.canvas.delete(self.hover_rect_id)
                self.hover_rect_id = None

                if self.current_hover_row != -1:
                    if self.current_hover_row in self.row_y_coords:
                        y1, y2 = self.row_y_coords[self.current_hover_row]
                        if math.isfinite(y1) and math.isfinite(y2):
                            self.hover_rect_id = self.canvas.create_rectangle(
                                self.row_start_x, y1, hover_end_x, y2,
                                fill=COLOR_HOVER_BG, outline="", tags="hover_effect") # Dark hover
                            self.canvas.tag_lower(self.hover_rect_id, "job_row")
                else: self.current_hover_row = -1
            except tk.TclError as e:
                print(f"TclError during job hover redraw: {e}")
                self.hover_rect_id = None
            except Exception as e:
                print(f"Unexpected error during job hover redraw: {e}")
                self.hover_rect_id = None

        def _on_motion(self, event):
            if not self.canvas.winfo_exists(): return
            try:
                canvas_y = self.canvas.canvasy(event.y)
                if not math.isfinite(canvas_y): return
                hovering_over_row = self._find_row_at_y(canvas_y)
                canvas_x = self.canvas.canvasx(event.x)
                row_end_x = self.row_start_x + sum(self.current_col_widths)
                if not (self.row_start_x <= canvas_x < row_end_x): hovering_over_row = -1
                if hovering_over_row != self.current_hover_row:
                    self.current_hover_row = hovering_over_row
                    self._redraw_hover()
            except tk.TclError: pass
            except Exception as e: print(f"Unexpected error in JobPage _on_motion: {e}")

        def _on_leave(self, event):
            if not self.canvas.winfo_exists(): return
            if self.current_hover_row != -1:
                self.current_hover_row = -1
                self._redraw_hover()

        def _on_double_click(self, event):
            if not self.canvas.winfo_exists(): return
            try:
                canvas_y = self.canvas.canvasy(event.y)
                canvas_x = self.canvas.canvasx(event.x)
                if not math.isfinite(canvas_y): return
                clicked_row_index = self._find_row_at_y(canvas_y)
                row_end_x = self.row_start_x + sum(self.current_col_widths)
                if clicked_row_index != -1 and (self.row_start_x <= canvas_x < row_end_x):
                    if 0 <= clicked_row_index < len(self.jobs_data):
                        job_data = self.jobs_data[clicked_row_index]
                        print(f"Double-clicked Job: {job_data[0]} (Project: {job_data[1]})")
                    else: print("Warning: Clicked row index out of bounds for job data.")
            except tk.TclError as e: print(f"TclError on job double click: {e}")
            except Exception as e: print(f"An error occurred on job double click: {e}")

        # --- Redraw scheduling methods (copied) ---
        def _schedule_redraw(self):
            if not self.winfo_exists():
                if self._draw_scheduled: self.after_cancel(self._draw_scheduled); self._draw_scheduled = None
                return
            if self._draw_scheduled: self.after_cancel(self._draw_scheduled)
            self._draw_scheduled = self.after(DEBOUNCE_DELAY, self._draw_table)

        def _on_canvas_configure_debounced(self, event):
            self._schedule_redraw()

        def trigger_redraw(self):
            if self.winfo_exists():
                self._schedule_redraw()


        def tkraise(self, aboveThis=None):
            super().tkraise(aboveThis)
            self.trigger_redraw()

    # ============================================
    # End of NEW JobPage Class
    # ============================================

    # ============================================
    # NEW TreePage Class - Hierarchical Tree View
    # ============================================
    class TreePage(tk.Frame):
        def __init__(self, parent, switch_page_callback, agent_data=None, base_url=None, token=None):
            super().__init__(parent, bg=COLOR_CONTENT_BG)
            self.switch_page_callback = switch_page_callback
            self.agent_data = agent_data or {}
            self.base_url = base_url
            self.token = token
            self.expanded_nodes = set()
            self.child_types_data = {}  # Store fetched child types data
            self.selected_node = None
            self.current_items = []
            
            # Main container with sidebar and content
            main_container = tk.Frame(self, bg=COLOR_CONTENT_BG)
            main_container.pack(fill=tk.BOTH, expand=True)
            
            # Left Sidebar (Tree Navigation)
            self.sidebar_frame = tk.Frame(main_container, bg=COLOR_SIDEBAR_BG, width=500)
            self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
            self.sidebar_frame.pack_propagate(False)
        
            # Sidebar Header
            sidebar_header = tk.Frame(self.sidebar_frame, bg=COLOR_SIDEBAR_BG)
            sidebar_header.pack(fill=tk.X, padx=15, pady=15)
            
            # Suites Logo/Title
            logo_label = tk.Label(sidebar_header, text="Suites", font=(FONT_FAMILY_PRIMARY, 16, "bold"), 
                                fg=COLOR_PRIMARY, bg=COLOR_SIDEBAR_BG)
            logo_label.pack(anchor="w")
            
            # Breadcrumb
            self.breadcrumb_label = tk.Label(sidebar_header, text="Configuration", 
                                           font=(FONT_FAMILY_PRIMARY, 10), fg=COLOR_TEXT_MUTED_DARK_BG, 
                                           bg=COLOR_SIDEBAR_BG, anchor="w")
            self.breadcrumb_label.pack(anchor="w", pady=(5, 0))
            
            # Tree Navigation Container
            tree_nav_container = tk.Frame(self.sidebar_frame, bg=COLOR_SIDEBAR_BG)
            tree_nav_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
            
            # Create scrollable tree navigation
            self.tree_canvas = tk.Canvas(tree_nav_container, bg=COLOR_SIDEBAR_BG, 
                                       highlightthickness=0, bd=0)
            tree_scrollbar = ttk.Scrollbar(tree_nav_container, orient="vertical", 
                                         command=self.tree_canvas.yview)
            self.tree_frame = tk.Frame(self.tree_canvas, bg=COLOR_SIDEBAR_BG)
            
            self.tree_canvas.configure(yscrollcommand=tree_scrollbar.set)
            self.tree_canvas.create_window((0, 0), window=self.tree_frame, anchor="nw")
            
            print(f"[DEBUG] Tree canvas and frame created")
            print(f"[DEBUG] tree_canvas: {self.tree_canvas}")
            print(f"[DEBUG] tree_frame: {self.tree_frame}")
            print(f"[DEBUG] tree_frame background: {self.tree_frame.cget('bg')}")
            
            # Configure canvas scrolling
            def configure_canvas(event):
                print(f"[DEBUG] Canvas configure event: {event}")
                print(f"[DEBUG] tree_frame children in configure: {len(self.tree_frame.winfo_children())}")
                self.tree_canvas.configure(scrollregion=self.tree_canvas.bbox("all"))
            
            self.tree_frame.bind("<Configure>", configure_canvas)
            
            # Pack tree navigation
            tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.tree_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Bind mousewheel to tree canvas
            def on_mousewheel(event):
                self.tree_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
            def on_mousewheel_linux(event):
                if event.num == 4:
                    self.tree_canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.tree_canvas.yview_scroll(1, "units")
            
            # Touchpad scrolling support
            def on_touchpad_scroll(event):
                # Handle touchpad scrolling (common on modern laptops)
                if hasattr(event, 'delta'):
                    # Windows/MacOS touchpad
                    self.tree_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                elif hasattr(event, 'num'):
                    # Linux touchpad
                    if event.num == 4:
                        self.tree_canvas.yview_scroll(-1, "units")
                    elif event.num == 5:
                        self.tree_canvas.yview_scroll(1, "units")
            
            # Bind all possible scroll events
            self.tree_canvas.bind("<MouseWheel>", on_mousewheel)
            self.tree_canvas.bind("<Button-4>", on_mousewheel_linux)
            self.tree_canvas.bind("<Button-5>", on_mousewheel_linux)
            
            # Additional touchpad bindings
            self.tree_canvas.bind("<B1-Motion>", on_touchpad_scroll)
            self.tree_canvas.bind("<Motion>", on_touchpad_scroll)
            
            # Enable touchpad scrolling on the tree frame itself
            self.tree_frame.bind("<MouseWheel>", on_mousewheel)
            self.tree_frame.bind("<Button-4>", on_mousewheel_linux)
            self.tree_frame.bind("<Button-5>", on_mousewheel_linux)
            
            # Enable touchpad scrolling on all tree elements
            def enable_tree_scrolling(widget):
                """Recursively enable scrolling on all tree widgets"""
                widget.bind("<MouseWheel>", on_mousewheel)
                widget.bind("<Button-4>", on_mousewheel_linux)
                widget.bind("<Button-5>", on_mousewheel_linux)
                # Also bind to touchpad motion events
                widget.bind("<B1-Motion>", on_touchpad_scroll)
                widget.bind("<Motion>", on_touchpad_scroll)
                
                # Recursively bind to all child widgets
                for child in widget.winfo_children():
                    enable_tree_scrolling(child)
            
            # Apply scrolling to tree frame and all its children
            enable_tree_scrolling(self.tree_frame)
            
            # Configure tree frame width to be wider than canvas for more space
            def configure_tree_frame(event):
                # Set tree frame width to be wider than canvas for more internal space
                print(f"[DEBUG] Tree frame configure event: {event}")
                print(f"[DEBUG] Canvas width: {event.width}")
                try:
                    self.tree_canvas.itemconfig(self.tree_canvas.find_withtag("all")[0], width=event.width + 150)
                    print(f"[DEBUG] Tree frame width configured to: {event.width + 150}")
                except Exception as e:
                    print(f"[DEBUG] Error configuring tree frame width: {e}")
            
            self.tree_canvas.bind("<Configure>", configure_tree_frame)
            
            # Right Content Area
            self.content_frame = tk.Frame(main_container, bg=COLOR_CONTENT_BG)
            self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            
            # Content Header
            content_header = tk.Frame(self.content_frame, bg=COLOR_CONTENT_BG)
            content_header.pack(fill=tk.X, padx=20, pady=15)
            
            # Search Frame
            search_frame = tk.Frame(content_header, bg=COLOR_CONTENT_BG, relief=tk.FLAT, bd=0)
            search_frame.pack(side=tk.LEFT, padx=(0, 10))
            
            # Search icon and input
            search_icon = tk.Label(search_frame, text="", font=(FONT_FAMILY_PRIMARY, 14), 
                                 bg=COLOR_CONTENT_BG, fg=COLOR_TEXT_MUTED_DARK_BG)
            search_icon.pack(side=tk.LEFT, padx=(0, 8), pady=8)
            
            self.search_var = tk.StringVar()
            self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                                       font=(FONT_FAMILY_PRIMARY, 11), bg=COLOR_CONTENT_BG, fg=COLOR_TEXT_LIGHT,
                                       relief=tk.FLAT, bd=0, insertbackground=COLOR_TEXT_LIGHT, width=30,
                                       highlightthickness=1, highlightbackground="white",
                                       highlightcolor="white", selectbackground=COLOR_PRIMARY)
            self.search_entry.pack(side=tk.LEFT, pady=8, padx=5)
            
            # Bind focus events to maintain white border
            self.search_entry.bind("<FocusIn>", lambda e: self.search_entry.config(highlightbackground="white"))
            self.search_entry.bind("<FocusOut>", lambda e: self.search_entry.config(highlightbackground="white"))
            
            # Set initial placeholder text
            self.search_entry.insert(0, "Search...")
            self.search_entry.config(fg=COLOR_TEXT_MUTED_DARK_BG)
            
            # Update search placeholder based on selected node
            def update_search_placeholder():
                if hasattr(self, 'selected_node') and self.selected_node:
                    self.search_entry.delete(0, tk.END)
                    self.search_entry.insert(0, f"Search {self.selected_node}...")
                    self.search_entry.config(fg=COLOR_TEXT_MUTED_DARK_BG)
            
            # Handle focus events for Windows-style behavior
            def on_focus_in(event):
                if self.search_entry.get() in ["Search...", f"Search {getattr(self, 'selected_node', '')}..."]:
                    self.search_entry.delete(0, tk.END)
                    self.search_entry.config(fg=COLOR_TEXT_LIGHT)
            
            def on_focus_out(event):
                if not self.search_entry.get().strip():
                    update_search_placeholder()
            
            # Handle Enter key press - search and lose focus
            def on_enter_press(event):
                self._on_search_submit(event)
                self.search_entry.master.focus()  # Move focus to parent frame to hide cursor
            
            # Handle search input - refresh view when cleared
            def on_search_input(event):
                current_text = self.search_entry.get()
                if not current_text.strip():
                    # If search is cleared, refresh to show current folder contents
                    if hasattr(self, 'selected_node'):
                        self._display_grid_items(self.selected_node)
                    self.search_entry.master.focus()
                else:
                    # Otherwise, perform normal search
                    self._on_search_input(event)
            
            # Bind to search entry focus
            self.search_entry.bind("<FocusIn>", on_focus_in)
            self.search_entry.bind("<FocusOut>", on_focus_out)
            
            # Bind search functionality
            self.search_entry.bind("<KeyRelease>", on_search_input)
            self.search_entry.bind("<Return>", on_enter_press)
            
            # Back button for folder navigation
            self.back_btn = tk.Button(content_header, text="← Back", 
                                    bg=COLOR_SECONDARY, fg=COLOR_TEXT_LIGHT,
                                    font=(FONT_FAMILY_PRIMARY, 11, "bold"), relief=tk.FLAT, bd=0,
                                    activebackground=COLOR_PRIMARY, activeforeground=COLOR_TEXT_LIGHT,
                                    padx=15, pady=8, command=self._navigate_back)
            self.back_btn.pack(side=tk.RIGHT, padx=(0, 10))
            self.back_btn.pack_forget()  # Initially hidden
            
            # Refresh button (icon only)
            refresh_btn = tk.Button(content_header, text="⟳", 
                                  bg=COLOR_SECONDARY, fg=COLOR_TEXT_LIGHT,
                                  font=(FONT_FAMILY_PRIMARY, 14, "bold"), relief=tk.FLAT, bd=0,
                                  activebackground=COLOR_PRIMARY, activeforeground=COLOR_TEXT_LIGHT,
                                  padx=8, pady=8, command=self.refresh_tree)
            refresh_btn.pack(side=tk.RIGHT, padx=(0, 10))
            
            # Content Grid Container
            self.grid_container = tk.Frame(self.content_frame, bg=COLOR_CONTENT_BG)
            self.grid_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
            
            # Create scrollable grid
            self.grid_canvas = tk.Canvas(self.grid_container, bg=COLOR_CONTENT_BG, 
                                       highlightthickness=0, bd=0)
            grid_scrollbar = ttk.Scrollbar(self.grid_container, orient="vertical", 
                                         command=self.grid_canvas.yview)
            self.grid_frame = tk.Frame(self.grid_canvas, bg=COLOR_CONTENT_BG)
            
            self.grid_canvas.configure(yscrollcommand=grid_scrollbar.set)
            self.grid_canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
            
            # Pack grid
            grid_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.grid_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Bind events
            self.tree_frame.bind("<Configure>", self._on_tree_frame_configure)
            self.grid_frame.bind("<Configure>", self._on_grid_frame_configure)
            self.tree_canvas.bind("<MouseWheel>", self._on_tree_mousewheel)
            self.grid_canvas.bind("<MouseWheel>", self._on_grid_mousewheel)
            
            # Additional touchpad support for grid canvas
            self.grid_canvas.bind("<Button-4>", self._on_grid_mousewheel)
            self.grid_canvas.bind("<Button-5>", self._on_grid_mousewheel)
            self.grid_container.bind("<MouseWheel>", self._on_grid_mousewheel)
            self.grid_container.bind("<Button-4>", self._on_grid_mousewheel)
            self.grid_container.bind("<Button-5>", self._on_grid_mousewheel)
            
            # Initial population
            self.fetch_child_types()
            self.populate_tree()
            
            # Set up initial content display
            self._setup_initial_content()
            
            # Force tree visibility and update
            self._force_tree_visibility()
            
            # Add a test label to verify tree frame is working
            test_label = tk.Label(self.tree_frame, text="TEST TREE FRAME", 
                                bg="red", fg="white", font=("Arial", 16, "bold"))
            test_label.pack(pady=20)
            
            # Initialize navigation history
            self.navigation_history = []
        
        def _force_tree_visibility(self):
            """Force the tree to be visible and properly configured"""
            print(f"[DEBUG] _force_tree_visibility called")
            print(f"[DEBUG] tree_frame exists: {hasattr(self, 'tree_frame')}")
            print(f"[DEBUG] tree_canvas exists: {hasattr(self, 'tree_canvas')}")
            
            if hasattr(self, 'tree_frame') and hasattr(self, 'tree_canvas'):
                print(f"[DEBUG] tree_frame children: {len(self.tree_frame.winfo_children())}")
                print(f"[DEBUG] tree_frame background: {self.tree_frame.cget('bg')}")
                
                # Force update of the tree frame
                self.tree_frame.update_idletasks()
                
                # Update canvas scroll region
                self.tree_canvas.update_idletasks()
                self.tree_canvas.configure(scrollregion=self.tree_canvas.bbox("all"))
                
                print(f"[DEBUG] Tree visibility forced, scroll region: {self.tree_canvas.bbox('all')}")
            else:
                print(f"[DEBUG] Tree components not ready")
        
        def _on_tree_frame_configure(self, event):
            self.tree_canvas.configure(scrollregion=self.tree_canvas.bbox("all"))
        
        def _on_grid_frame_configure(self, event):
            self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all"))
        
        def _on_tree_mousewheel(self, event):
            # Handle both mouse wheel and touchpad scrolling
            if hasattr(event, 'delta'):
                # Windows/MacOS
                self.tree_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            elif hasattr(event, 'num'):
                # Linux
                if event.num == 4:
                    self.tree_canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.tree_canvas.yview_scroll(1, "units")
        
        def _on_grid_mousewheel(self, event):
            # Handle both mouse wheel and touchpad scrolling
            if hasattr(event, 'delta'):
                # Windows/MacOS
                self.grid_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            elif hasattr(event, 'num'):
                # Linux
                if event.num == 4:
                    self.grid_canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.grid_canvas.yview_scroll(1, "units")
        
        def _enable_tree_scrolling(self):
            """Enable touchpad scrolling on all tree elements"""
            def enable_scrolling_on_widget(widget):
                """Recursively enable scrolling on a widget and all its children"""
                try:
                    # Bind mouse wheel events
                    widget.bind("<MouseWheel>", self._on_tree_mousewheel)
                    widget.bind("<Button-4>", self._on_tree_mousewheel)
                    widget.bind("<Button-5>", self._on_tree_mousewheel)
                    
                    # Bind touchpad motion events
                    widget.bind("<B1-Motion>", self._on_tree_mousewheel)
                    widget.bind("<Motion>", self._on_tree_mousewheel)
                    
                    # Recursively bind to all child widgets
                    for child in widget.winfo_children():
                        enable_scrolling_on_widget(child)
                except Exception as e:
                    # Skip widgets that can't be bound
                    pass
            
            # Apply to tree frame and all its children
            enable_scrolling_on_widget(self.tree_frame)
        
        def fetch_child_types(self):
            """Fetch child types from the API"""
            if not self.base_url or not self.token:
                print("Warning: Missing base_url or token for child types API call")
                return
            
            try:
                # Get fresh token from configuration file to avoid stale token issues
                current_token = None
                try:
                    with open('client.conf.json', 'r') as f:
                        config = json.load(f)
                        current_token = config.get('token')
                except Exception as e:
                    print(f"Error reading token from config: {e}")
                    # Fallback to stored token if config read fails
                    current_token = self.token
                # current_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NfdG9rZW4iOiI4MzlhMDY2ZTNlZmZkYzczYjI2MDE0MDhlNWViMmQxN2UzNTRjNzE1MTNhYmNhOWQ5ZTFhMzgyODhmMjFkMWRmNTZhNDA4MjBkMjgwZDczMWM0YTViNmM3OTcwMjY5ZmRiMDU2YjUxMjk2YTBkZTVlNGY3OTU1M2QzYjhhMTNmNWZhYTA4NmQ2YTExMDE1ZjQzODlhZDViNTlkZGZlYTM3OGU0NjlkMDhmNjgwYTc3N2Y1MTFhY2E5MTEyNDg0MzdiZWY0OWNiZWU3ODRkMmY2NzM0Njg1ZjYwYjNiNWJiZTM0MzAxZjA4ZjYxNzQ3YTZiMzI0MDUzODQ2MzYzMTgyZTJiNDc2YjQzMGM4YTY0NDYzNTM1OGRmYjJhMWJkYjVhZDE5OWNjYzRhYjA2ZWVlYjg2ODVhYmQ4ZGUyZjAxM2QwMGFmZTBlYmRmYmVmOGE4NjI3NjkzMjE2MjY1MTBjZWJmNTQ0MTA0YWJkMTVhNzYwNzA0NTBlOGVjMWIxYjU0YmY4NTc5ODM3MjMzNzI0Y2U4MjZiNDExNTZhNWVjMzVhNmQzZTM5MjJhYWQ3Yjk2MjI4NzVjZTEyZjNlZWI0N2EwOWM4YTAzMTVkMDk3ODczNWE3ZGEwYTdjZjVkOWJiMzQzZTcwNWM3MjM2ZTE4ZTY1Y2Q1NDM5NzY5M2UwOTM3MGY3OWJlOTlkOGQ3ZTBlN2VkNzk0NGQ4ODA4NTE5NzMxZWRlOGE2OWI1MDI3NTEwNzk4MzE4MWEyZmRiZWU4ODMwNDZkOGI3NmNlZjEyNjkyNjdiNTJmNTg0MzJkOWFjOGRiYWMyZjc0NTlmNzI0ZDU5MmZkMDYyZmY4YWQyZDgwYTIyN2Q0N2Y2NjMyZDIzMjg4N2MxNWFmMjVjM2EiLCJ1c2VyX3R5cGUiOiJhZG1pbiIsImlhdCI6MTc1Njc0OTA4MCwiZXhwIjoxNzU2ODM1NDgwfQ.dD-6ntj1ba8yFXbxJp9eNJmtOrWzTUWgilltQZJaD9M"
                headers = {"Authorization": f"Bearer {current_token}"}
                api_url = f"{self.base_url.rstrip('/')}/api/type/child/list/all"
                
                print(f"[DEBUG] Fetching child types from: {api_url}")
                print(f"[DEBUG] Headers: {headers}")
                
                response = requests.get(api_url, headers=headers)
                
                print(f"[DEBUG] Response status: {response.status_code}")
                # print(f"[DEBUG] Response text: {response.text}")
                
                if response.status_code == 200:
                    self.child_types_data = response.json()
                    # print(f"[DEBUG] Child types data: {self.child_types_data}")
                else:
                    print(f"Error fetching child types: {response.status_code} - {response.text}")
                    self.child_types_data = {}
                    
            except Exception as e:
                print(f"Exception during child types fetch: {e}")
                self.child_types_data = {}

        def refresh_tree(self):
            # Store current selection for restoration
            current_selection = getattr(self, 'selected_node', None)
            
            # Fetch latest child types data
            self.fetch_child_types()
            # Clear existing tree and grid
            for widget in self.tree_frame.winfo_children():
                widget.destroy()
            for widget in self.grid_frame.winfo_children():
                widget.destroy()
            self.expanded_nodes.clear()
            self.populate_tree()
            # Re-enable scrolling after refresh
            self._enable_tree_scrolling()
            
            # Ensure ITSAR visibility is maintained after refresh
            self._ensure_itsar_visibility()
            
            # Restore previous selection if possible
            if current_selection:
                self._restore_selection(current_selection)
        
        def populate_tree(self):
            print(f"DEBUG: populate_tree called")
            print(f"DEBUG: tree_frame exists: {hasattr(self, 'tree_frame')}")
            print(f"DEBUG: tree_frame children before clear: {len(self.tree_frame.winfo_children()) if hasattr(self, 'tree_frame') else 'N/A'}")
            
            # Clear existing tree
            for widget in self.tree_frame.winfo_children():
                widget.destroy()
            
            print(f"DEBUG: tree_frame children after clear: {len(self.tree_frame.winfo_children())}")
            print(f"DEBUG: child_types_data: {self.child_types_data}")
            
            # Add child types data if available (this creates the Suites section)
            if self.child_types_data:
                print(f"DEBUG: Creating child types tree")
                self._create_child_types_tree()
            else:
                print(f"DEBUG: Creating project tree (fallback)")
                self._create_project_tree()
            
            print(f"DEBUG: tree_frame children after population: {len(self.tree_frame.winfo_children())}")
            
            # Update canvas scroll region after populating
            self.tree_canvas.update_idletasks()
            self.tree_canvas.configure(scrollregion=self.tree_canvas.bbox("all"))
            
            # Enable touchpad scrolling on all newly created tree elements
            self._enable_tree_scrolling()
            
            # Display top-level folders in the grid by default
            if self.child_types_data and isinstance(self.child_types_data, dict) and 'data' in self.child_types_data:
                # Get all top-level folders (type1_names) to display in the grid
                top_level_folders = []
                for type1_item in self.child_types_data['data']:
                    type1_name = type1_item.get('type1_name', 'Unknown')
                    if type1_name:
                        top_level_folders.append(type1_name)
                
                if top_level_folders:
                    print(f"DEBUG: Displaying top-level folders in grid: {top_level_folders}")
                    # Display the top-level folders as cards
                    self._display_grid_items_from_list(top_level_folders, "Suites")
                else:
                    # Fallback to single item display
                    self._display_grid_items("Suites")
            else:
                # Fallback: Create default folders if no data available
                print(f"DEBUG: No child_types_data available, creating default folders")
                default_folders = ["ITSAR", "Test2", "Test3", "Test4", "Test5", "Test6", "Test7", "Test8"]
                self._display_grid_items_from_list(default_folders, "Suites")
        
        def _create_nav_section(self, title, is_expanded=False):
            """Create a navigation section with expand/collapse functionality"""
            print(f"[DEBUG] _create_nav_section called with title: {title}, is_expanded: {is_expanded}")
            print(f"[DEBUG] tree_frame children before section creation: {len(self.tree_frame.winfo_children())}")
            
            section_frame = tk.Frame(self.tree_frame, bg=COLOR_SIDEBAR_BG)
            section_frame.pack(fill=tk.X, pady=2)
            
            print(f"[DEBUG] section_frame created and packed")
            print(f"[DEBUG] tree_frame children after section_frame.pack: {len(self.tree_frame.winfo_children())}")
            
            # Section header
            header_frame = tk.Frame(section_frame, bg=COLOR_SIDEBAR_BG)
            header_frame.pack(fill=tk.X, padx=5, pady=3)
            
            # Expand/collapse icon
            icon_text = "▼" if is_expanded else "▶"
            icon_label = tk.Label(header_frame, text=icon_text, font=(FONT_FAMILY_PRIMARY, 10), 
                                fg=COLOR_TEXT_LIGHT, bg=COLOR_SIDEBAR_BG, cursor="hand2")
            icon_label.pack(side=tk.LEFT, padx=(0, 8))
            
            # Custom pixelated folder icon canvas for section
            section_icon_canvas = tk.Canvas(header_frame, width=16, height=16, 
                                          bg=COLOR_SIDEBAR_BG, highlightthickness=0)
            section_icon_canvas.pack(side=tk.LEFT, padx=(0, 5))
            
            # Draw pixelated folder icon (darker golden yellow main body, lighter yellow tab)
            # Main folder body (darker golden yellow)
            section_icon_canvas.create_rectangle(2, 4, 14, 14, fill="#D4A017", outline="#D4A017")
            # Folder tab (lighter yellow) - positioned on top left
            section_icon_canvas.create_rectangle(3, 2, 11, 6, fill="#FFD966", outline="#FFD966")
            
            # Section title
            title_label = tk.Label(header_frame, text=title, font=(FONT_FAMILY_PRIMARY, 11, "bold"), 
                                 fg=COLOR_TEXT_LIGHT, bg=COLOR_SIDEBAR_BG, anchor="w")
            title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Content frame (initially shown/hidden based on is_expanded)
            content_frame = tk.Frame(section_frame, bg=COLOR_SIDEBAR_BG)
            if is_expanded:
                content_frame.pack(fill=tk.X, padx=15)
            
            # Store expansion state
            expanded_state = is_expanded
            
            # Toggle function
            def toggle_section():
                nonlocal expanded_state
                if expanded_state:
                    # Collapse
                    content_frame.pack_forget()
                    icon_label.config(text="▶")
                    expanded_state = False
                else:
                    # Expand
                    content_frame.pack(fill=tk.X, padx=15)
                    icon_label.config(text="▼")
                    expanded_state = True
                
                # Update canvas scroll region
                self.tree_canvas.update_idletasks()
                self.tree_canvas.configure(scrollregion=self.tree_canvas.bbox("all"))
            
            # Both single and double click for toggle
            icon_label.bind("<Button-1>", lambda e: toggle_section())
            title_label.bind("<Button-1>", lambda e: toggle_section())
            
            # Double click also works for toggle
            icon_label.bind("<Double-Button-1>", lambda e: toggle_section())
            title_label.bind("<Double-Button-1>", lambda e: toggle_section())
            
            print(f"[DEBUG] _create_nav_section returning content_frame: {content_frame}")
            return content_frame
        
        def _create_child_types_tree(self):
            """Create hierarchical tree from child types data"""
            # print(f"[DEBUG] Creating child types tree with data: {self.child_types_data}")
            # print(f"[DEBUG] tree_frame children before creation: {len(self.tree_frame.winfo_children())}")
            
            # Create main section
            main_section = self._create_nav_section("Suites", is_expanded=True)
            print(f"[DEBUG] main_section created: {main_section}")
            print(f"[DEBUG] tree_frame children after main_section: {len(self.tree_frame.winfo_children())}")
            
            # Directly create folders for each type1_name
            if self.child_types_data and isinstance(self.child_types_data, dict) and 'data' in self.child_types_data:
                print(f"[DEBUG] Found {len(self.child_types_data['data'])} type1 items")
                for type1_item in self.child_types_data['data']:
                    type1_name = type1_item.get('type1_name', 'Unknown')
                    levels = type1_item.get('levels', [])
                    print(f"[DEBUG] Creating folder for {type1_name} with {len(levels)} levels")
                    
                    # Create expandable folder for this type1_name
                    self._create_expandable_node(main_section, type1_name, levels, level=0)
            else:
                print(f"[DEBUG] No child_types_data or invalid format: {self.child_types_data}")
                # Create default folders to ensure ITSAR exists
                print(f"[DEBUG] Creating default folders including ITSAR")
                default_folders = ["ITSAR", "Test2", "Test3", "Test4", "Test5", "Test6", "Test7", "Test8"]
                for folder_name in default_folders:
                    # Create empty expandable node for each default folder
                    self._create_expandable_node(main_section, folder_name, [], level=0)
            
            print(f"[DEBUG] tree_frame children after all creation: {len(self.tree_frame.winfo_children())}")
            
            # Enable scrolling on the new tree elements
            self._enable_tree_scrolling()
        
        def _build_tree_structure(self, data):
            """Build hierarchical structure from API response"""
            tree_structure = {}
            
            # Parse the API response structure
            if isinstance(data, dict) and 'data' in data:
                for type1_item in data['data']:
                    type1_name = type1_item.get('type1_name', 'Unknown')
                    levels = type1_item.get('levels', [])
                    
                    # Build the tree for this type1
                    tree_structure[type1_name] = self._build_level_tree(levels)
            
            return tree_structure
        
        def _build_level_tree(self, levels):
            """Recursively build tree structure from levels"""
            tree = {}
            
            for level in levels:
                level_name = level.get('name', 'Unknown')
                children = level.get('children', [])
                
                if children:
                    # This level has children, so it's a folder
                    # Recursively build the tree for children
                    child_tree = self._build_level_tree(children)
                    tree[level_name] = child_tree
                else:
                    # This level has no children, so it's a leaf node
                    # Store as a list to group leaf nodes together
                    if level_name not in tree:
                        tree[level_name] = []
                    tree[level_name].append(level)
            
            return tree
        
        def _render_levels_structure(self, levels, parent_frame, level=0):
            """Render the levels structure from API data"""
            print(f"[DEBUG] Rendering levels structure: {len(levels)} items at level {level}")
            for level_item in levels:
                level_name = level_item.get('name', 'Unknown')
                children = level_item.get('children', [])
                print(f"[DEBUG] Level item: {level_name}, has {len(children)} children")
                
                if children:
                    # This level has children, so it's a folder
                    self._create_expandable_node(parent_frame, level_name, children, level)
                else:
                    # This level has no children, so it's a leaf node
                    self._create_leaf_node(parent_frame, level_item, level)
            
            # Enable scrolling on the new elements
            self._enable_tree_scrolling()
        
        def _render_tree_structure(self, structure, parent_frame, level=0):
            """Recursively render tree structure with expandable nodes"""
            for key, value in structure.items():
                if isinstance(value, dict):
                    # Check if this is a leaf node (has 'id' and 'name' keys)
                    if 'id' in value and 'name' in value:
                        # This is a leaf node (individual item) - always show
                        self._create_leaf_node(parent_frame, value, level)
                    else:
                        # This is a folder node (has children) - always show
                        self._create_expandable_node(parent_frame, key, value, level)
                    
                elif isinstance(value, list):
                    # Handle list of items (leaf nodes) - always show
                        # Limit to first 20 items to prevent overflow
                        max_items = 20
                        items_to_show = value[:max_items]
                        
                        for item in items_to_show:
                            if isinstance(item, dict):
                                self._create_leaf_node(parent_frame, item, level)
                            else:
                                self._create_leaf_node(parent_frame, {'name': str(item), 'id': ''}, level)
                        
                        # If there are more items, show a "Show more" indicator
                        if len(value) > max_items:
                            remaining_count = len(value) - max_items
                            show_more_frame = tk.Frame(parent_frame, bg=COLOR_SIDEBAR_BG)
                            show_more_frame.pack(fill=tk.X, padx=level * 8, pady=1)
                            
                            # Show more icon
                            show_more_icon = tk.Label(show_more_frame, text="⋯", font=(FONT_FAMILY_PRIMARY, 8), 
                                                    fg=COLOR_TEXT_MUTED_DARK_BG, bg=COLOR_SIDEBAR_BG)
                            show_more_icon.pack(side=tk.LEFT, padx=(0, 3))
                            
                            show_more_label = tk.Label(show_more_frame, text=f"and {remaining_count} more items", 
                                                     font=(FONT_FAMILY_PRIMARY, 8), fg=COLOR_TEXT_LIGHT, bg=COLOR_SIDEBAR_BG, anchor="w")
                            show_more_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def _create_leaf_node(self, parent_frame, item_data, level):
            """Create a leaf node (individual item)"""
            item_name = item_data.get('name', 'Unknown')
            item_id = item_data.get('id', '')
            
            item_frame = tk.Frame(parent_frame, bg=COLOR_SIDEBAR_BG)
            item_frame.pack(fill=tk.X, padx=level * 8, pady=1)
            
            # Item file icon
            item_icon = tk.Label(item_frame, text="📄", font=(FONT_FAMILY_PRIMARY, 8), 
                               fg="#F0F0F0", bg=COLOR_SIDEBAR_BG)
            item_icon.pack(side=tk.LEFT, padx=(0, 5))
            
            # Item name - allow text to expand and fill available space
            item_name_label = tk.Label(item_frame, text=item_name, font=(FONT_FAMILY_PRIMARY, 9), 
                                     fg=COLOR_TEXT_LIGHT, bg=COLOR_SIDEBAR_BG, anchor="w")
            item_name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Add click handler
            item_frame.bind("<Button-1>", lambda e, n=item_name, i=item_id: self._on_item_click(n, i))
            item_icon.bind("<Button-1>", lambda e, n=item_name, i=item_id: self._on_item_click(n, i))
            item_name_label.bind("<Button-1>", lambda e, n=item_name, i=item_id: self._on_item_click(n, i))
        
        def _create_expandable_node(self, parent_frame, key, value, level):
            """Create an expandable tree node with toggle functionality"""
            print(f"[DEBUG] _create_expandable_node called with key: {key}, level: {level}")
            print(f"[DEBUG] parent_frame: {parent_frame}")
            print(f"[DEBUG] parent_frame children before: {len(parent_frame.winfo_children())}")
            
            # Main container for the expandable node
            node_container = tk.Frame(parent_frame, bg=COLOR_SIDEBAR_BG)
            node_container.pack(fill=tk.X, padx=level * 8, pady=1)
            
            print(f"[DEBUG] node_container created and packed")
            print(f"[DEBUG] parent_frame children after: {len(parent_frame.winfo_children())}")
            
            # Header frame (always visible)
            header_frame = tk.Frame(node_container, bg=COLOR_SIDEBAR_BG)
            header_frame.pack(fill=tk.X)
            
            # Expand/collapse icon (starts as collapsed)
            expand_icon = tk.Label(header_frame, text="▶", font=(FONT_FAMILY_PRIMARY, 8), 
                                 fg=COLOR_TEXT_LIGHT, bg=COLOR_SIDEBAR_BG)
            expand_icon.pack(side=tk.LEFT, padx=(0, 3))
            
            # Custom pixelated folder icon canvas
            folder_icon_canvas = tk.Canvas(header_frame, width=16, height=16, 
                                         bg=COLOR_SIDEBAR_BG, highlightthickness=0)
            folder_icon_canvas.pack(side=tk.LEFT, padx=(0, 5))
            
            # Draw pixelated folder icon (darker golden yellow main body, lighter yellow tab)
            # Main folder body (darker golden yellow)
            folder_icon_canvas.create_rectangle(2, 4, 14, 14, fill="#D4A017", outline="#D4A017")
            # Folder tab (lighter yellow) - positioned on top left
            folder_icon_canvas.create_rectangle(3, 2, 11, 6, fill="#FFD966", outline="#FFD966")
            
            # Folder name
            folder_name = tk.Label(header_frame, text=key, font=(FONT_FAMILY_PRIMARY, 10), 
                                 fg=COLOR_TEXT_LIGHT, bg=COLOR_SIDEBAR_BG, anchor="w")
            folder_name.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Content frame (initially hidden) - contained within node_container
            content_frame = tk.Frame(node_container, bg=COLOR_SIDEBAR_BG)
            
            # Store references for toggle functionality
            node_data = {
                'key': key,
                'value': value,
                'level': level + 1,
                'expanded': False,
                'expand_icon': expand_icon,
                'content_frame': content_frame,
                'parent_container': node_container
            }
            
            # Add click handler for expand/collapse
            def toggle_node(event, data=node_data):
                self._toggle_node(data)
            
            # Bind events - both single and double click for expand/collapse
            header_frame.bind("<Button-1>", toggle_node)
            expand_icon.bind("<Button-1>", toggle_node)
            folder_icon_canvas.bind("<Button-1>", toggle_node)
            folder_name.bind("<Button-1>", toggle_node)
            
            # Double click also works for expand/collapse
            header_frame.bind("<Double-Button-1>", toggle_node)
            expand_icon.bind("<Double-Button-1>", toggle_node)
            folder_icon_canvas.bind("<Double-Button-1>", toggle_node)
            folder_name.bind("<Double-Button-1>", toggle_node)
            
            print(f"[DEBUG] _create_expandable_node completed for key: {key}")
            print(f"[DEBUG] node_container children: {len(node_container.winfo_children())}")
        
        def _toggle_node(self, node_data):
            """Toggle the expansion state of a tree node"""
            try:
                if not isinstance(node_data, dict) or 'key' not in node_data:
                    print(f"[ERROR] Invalid node_data: {node_data}")
                    return
                    
                print(f"[DEBUG] Toggling node: {node_data.get('key', 'Unknown')}, current expanded state: {node_data.get('expanded', False)}")
                print(f"[DEBUG] Node value type: {type(node_data.get('value'))}, value: {node_data.get('value')}")
                
                # Validate required widgets exist
                if 'content_frame' not in node_data or not hasattr(node_data['content_frame'], 'winfo_children') or \
                   'expand_icon' not in node_data or not hasattr(node_data['expand_icon'], 'config'):
                    print("[ERROR] Missing or invalid widget references in node_data")
                    return
                
                if node_data.get('expanded', False):
                    # Collapse the node
                    if 'content_frame' in node_data and hasattr(node_data['content_frame'], 'pack_forget'):
                        node_data['content_frame'].pack_forget()
                    if 'expand_icon' in node_data and hasattr(node_data['expand_icon'], 'config'):
                        node_data['expand_icon'].config(text="▶")
                    node_data['expanded'] = False
                    print(f"[DEBUG] Collapsed node: {node_data.get('key', 'Unknown')}")
                else:
                    # Expand the node - pack within the node container
                    if 'content_frame' in node_data and hasattr(node_data['content_frame'], 'pack'):
                        node_data['content_frame'].pack(fill=tk.X)
                    if 'expand_icon' in node_data and hasattr(node_data['expand_icon'], 'config'):
                        node_data['expand_icon'].config(text="▼")
                    node_data['expanded'] = True
                    print(f"[DEBUG] Expanded node: {node_data.get('key', 'Unknown')}")
                    
                    # Render children if not already rendered
                    if 'content_frame' in node_data and hasattr(node_data['content_frame'], 'winfo_children'):
                        try:
                            if not node_data['content_frame'].winfo_children():
                                print(f"[DEBUG] Rendering children for node: {node_data.get('key', 'Unknown')}")
                                # Check if this is a levels data structure (from API)
                                if isinstance(node_data.get('value'), list):
                                    # This is levels data from the API
                                    print(f"[DEBUG] Using _render_levels_structure for {node_data.get('key', 'Unknown')}")
                                    self._render_levels_structure(
                                        node_data['value'], 
                                        node_data['content_frame'], 
                                        node_data.get('level', 0)
                                    )
                                elif isinstance(node_data.get('value'), dict):
                                    # This is regular tree structure
                                    print(f"[DEBUG] Using _render_tree_structure for {node_data.get('key', 'Unknown')}")
                                    self._render_tree_structure(
                                        node_data['value'], 
                                        node_data['content_frame'], 
                                        node_data.get('level', 0)
                                    )
                                else:
                                    # This might be a primitive value
                                    print(f"[DEBUG] Unknown value type for {node_data.get('key', 'Unknown')}: {type(node_data.get('value'))}")
                        except Exception as e:
                            print(f"[ERROR] Error rendering children for node {node_data.get('key', 'Unknown')}: {str(e)}")
                            import traceback
                            traceback.print_exc()
            
                # Update canvas scroll region after expansion/collapse
                if hasattr(self, 'tree_canvas') and hasattr(self.tree_canvas, 'update_idletasks'):
                    self.tree_canvas.update_idletasks()
                    if hasattr(self.tree_canvas, 'configure'):
                        self.tree_canvas.configure(scrollregion=self.tree_canvas.bbox("all"))
                        
                # Update breadcrumb to show the expanded folder
                if hasattr(self, 'breadcrumb_label') and hasattr(self.breadcrumb_label, 'config'):
                    self.breadcrumb_label.config(text=f"Suites > {node_data.get('key', 'Unknown')}")
                
                self.selected_node = node_data.get('key')
                
                # Display content for the expanded node in the right panel
                if hasattr(self, '_display_grid_items') and 'key' in node_data:
                    self._display_grid_items(node_data['key'])
                
                # Store navigation history for back functionality
                if not hasattr(self, 'navigation_history'):
                    self.navigation_history = []
                self.navigation_history.append({
                    'node': node_data.get('key'),
                    'parent': getattr(self, 'selected_node', None),
                    'children': self._get_direct_children(node_data.get('key')) if hasattr(self, '_get_direct_children') else []
                })
                
                # Update back button visibility
                if hasattr(self, '_update_back_button_visibility'):
                    self._update_back_button_visibility()
                    
            except Exception as e:
                print(f"[ERROR] Error in _toggle_node: {str(e)}")
                import traceback
                traceback.print_exc()
        
        def _create_project_tree(self):
            """Create project-based tree structure"""
            main_section = self._create_nav_section("Projects", is_expanded=True)
            
            for project in self.agent_data.get("data", []):
                project_name = project.get("project_name", "Unknown Project")
                
                # Create project folder
                project_frame = tk.Frame(main_section, bg=COLOR_SIDEBAR_BG)
                project_frame.pack(fill=tk.X, padx=15, pady=1)
                
                # Custom pixelated folder icon canvas for project
                project_icon_canvas = tk.Canvas(project_frame, width=16, height=16, 
                                              bg=COLOR_SIDEBAR_BG, highlightthickness=0)
                project_icon_canvas.pack(side=tk.LEFT, padx=(0, 5))
                
                # Draw pixelated folder icon (darker golden yellow main body, lighter yellow tab)
                # Main folder body (darker golden yellow)
                project_icon_canvas.create_rectangle(2, 4, 14, 14, fill="#D4A017", outline="#D4A017")
                # Folder tab (lighter yellow) - positioned on top left
                project_icon_canvas.create_rectangle(3, 2, 11, 6, fill="#FFD966", outline="#FFD966")
                
                project_name_label = tk.Label(project_frame, text=project_name, font=(FONT_FAMILY_PRIMARY, 10), 
                                            fg=COLOR_TEXT_LIGHT, bg=COLOR_SIDEBAR_BG, anchor="w")
                project_name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                # Add tasks
                for subtype in project.get("subtypes_status", []):
                    task_name = subtype.get("type", "Unnamed Task")
                    
                    task_frame = tk.Frame(main_section, bg=COLOR_SIDEBAR_BG)
                    task_frame.pack(fill=tk.X, padx=30, pady=1)
                    
                    task_icon = tk.Label(task_frame, text="📄", font=(FONT_FAMILY_PRIMARY, 10), 
                                       fg="#F0F0F0", bg=COLOR_SIDEBAR_BG)
                    task_icon.pack(side=tk.LEFT, padx=(0, 5))
                    
                    task_name_label = tk.Label(task_frame, text=task_name, font=(FONT_FAMILY_PRIMARY, 9), 
                                             fg=COLOR_TEXT_LIGHT, bg=COLOR_SIDEBAR_BG, anchor="w")
                    task_name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
                    
                    # Add click handler
                    task_frame.bind("<Button-1>", lambda e, t=task_name: self._on_item_click(t))
                    task_icon.bind("<Button-1>", lambda e, t=task_name: self._on_item_click(t))
                    task_name_label.bind("<Button-1>", lambda e, t=task_name: self._on_item_click(t))
        
        def _on_folder_click(self, folder_name):
            """Handle folder click - update breadcrumb and display items"""
            print(f"DEBUG: Folder clicked: {folder_name}")
            
            # Update breadcrumb
            self.breadcrumb_label.config(text=f"Suites > {folder_name}")
            
            # Update selected node
            self.selected_node = folder_name
            
            # Display items for this folder in the grid
            self._display_grid_items(folder_name)
            
            # Update breadcrumb to show the full path
            self._update_breadcrumb_path(folder_name)
            
            # Store navigation history for back functionality
            if not hasattr(self, 'navigation_history'):
                self.navigation_history = []
            self.navigation_history.append({
                'node': folder_name,
                'parent': getattr(self, 'selected_node', None),
                'children': self._get_direct_children(folder_name)
            })
            
            # Update back button visibility
            self._update_back_button_visibility()
            
            # Also expand the corresponding node in the tree to show selection
            self._expand_tree_node(folder_name)
            
            # Try direct tree expansion as well
            self._direct_expand_tree_node(folder_name)
        
        def _on_item_click(self, item_name, item_id=""):
            """Handle item click - update breadcrumb and display items in grid"""
            print(f"DEBUG: Item clicked: {item_name}")
            
            # Update breadcrumb
            self.breadcrumb_label.config(text=f"Suites > {item_name}")
            
            # Update selected node
            self.selected_node = item_name
            
            # Check if this item has children (is a folder)
            children = self._get_direct_children(item_name)
            if children:
                print(f"DEBUG: Item '{item_name}' has {len(children)} children, treating as folder")
                # This is a folder, expand it in tree and show children
                self._expand_folder_in_tree(item_name)
                
                # Try direct tree expansion as well
                self._direct_expand_tree_node(item_name)
                self._display_grid_items(item_name, item_id)
                
                # Store navigation history for back functionality
                if not hasattr(self, 'navigation_history'):
                    self.navigation_history = []
                self.navigation_history.append({
                    'node': item_name,
                    'parent': getattr(self, 'selected_node', None),
                    'children': children
                })
                
                # Update back button visibility
                self._update_back_button_visibility()
            else:
                print(f"DEBUG: Item '{item_name}' is a leaf node, showing single card")
                # This is a leaf node, show it as a single card
                self._display_grid_items(item_name, item_id)
            
            # Update breadcrumb to show the full path
            self._update_breadcrumb_path(item_name)
        
        def _expand_folder_in_tree(self, folder_name):
            """Expand a folder in the tree view when clicked"""
            print(f"DEBUG: Expanding folder in tree: {folder_name}")
            
            # Find the folder in the tree and expand it
            # This method will be called when a folder is clicked to ensure tree sync
            self._expand_tree_node(folder_name)
        
        # This method has been renamed to _expand_tree_node_by_name for clarity
        
        def _find_and_expand_tree_node(self, target_name):
            """Find and expand a specific node in the tree"""
            print(f"DEBUG: Looking for tree node: {target_name}")
            
            if not hasattr(self, 'tree_frame'):
                print(f"DEBUG: No tree_frame found")
                return False
            
            # Try a simpler approach - search through all tree widgets directly
            print(f"DEBUG: Searching all tree widgets for: {target_name}")
            found = self._search_all_tree_widgets(self.tree_frame, target_name)
            if found:
                print(f"DEBUG: Found and expanded node: {target_name}")
                return True
            
            # Fallback to the original search method
            print(f"DEBUG: Fallback to original search method")
            if hasattr(self, 'tree_frame'):
                # Look for the main section first
                main_section = None
                for widget in self.tree_frame.winfo_children():
                    if isinstance(widget, tk.Frame):
                        # Check if this is the main section by looking for "Suites" label
                        for child in widget.winfo_children():
                            if isinstance(child, tk.Frame):
                                for grandchild in child.winfo_children():
                                    if isinstance(grandchild, tk.Label) and grandchild.cget('text') == "Suites":
                                        main_section = child
                                        break
                                if main_section:
                                    break
                        if main_section:
                            break
                
                if main_section:
                    print(f"DEBUG: Found main section, searching for target: {target_name}")
                    # Search through the main section for the target node
                    return self._search_and_expand_in_section(main_section, target_name)
                else:
                    print(f"DEBUG: Main section not found")
                    return False
            
            return False
        
        def _search_all_tree_widgets(self, widget, target_name):
            """Search through all tree widgets recursively for the target"""
            print(f"DEBUG: Searching widget: {type(widget).__name__}")
            
            # Check if this widget is a label with the target name
            if isinstance(widget, tk.Label) and hasattr(widget, 'cget'):
                try:
                    widget_text = widget.cget('text')
                    print(f"DEBUG: Found label with text: '{widget_text}'")
                    if widget_text == target_name:
                        print(f"DEBUG: Found target label: {target_name}")
                        # Find the parent container and expand it
                        parent = widget.master
                        while parent and not isinstance(parent, tk.Frame):
                            parent = parent.master
                        if parent:
                            print(f"DEBUG: Found parent container, expanding")
                            return self._expand_target_node(parent)
                        return False
                except Exception as e:
                    print(f"DEBUG: Error checking label text: {e}")
            
            # Recursively search in all children
            for child in widget.winfo_children():
                if self._search_all_tree_widgets(child, target_name):
                    return True
            
            return False
        
        def _direct_expand_tree_node(self, node_name):
            """Directly expand a tree node by simulating a click on it"""
            print(f"DEBUG: Directly expanding tree node: {node_name}")
            
            # Find the tree node and simulate a click on it
            if hasattr(self, 'tree_frame'):
                # Search for the node in the tree
                node_widget = self._find_tree_node_widget(self.tree_frame, node_name)
                if node_widget:
                    print(f"DEBUG: Found tree node widget, simulating click")
                    # Simulate a click on the node to expand it
                    self._simulate_node_click(node_widget)
                    return True
                else:
                    print(f"DEBUG: Could not find tree node widget for: {node_name}")
                    
                    # Try to find the parent folder that contains this content
                    parent_folder = self._find_parent_folder_for_content(node_name)
                    if parent_folder:
                        print(f"DEBUG: Found parent folder: {parent_folder}, expanding it")
                        return self._direct_expand_tree_node(parent_folder)
            
            return False
        
        def _find_parent_folder_for_content(self, content_name):
            """Find the parent folder that contains the given content"""
            print(f"DEBUG: Looking for parent folder of content: {content_name}")
            
            if not self.child_types_data:
                return None
            
            # Search through the API data to find which folder contains this content
            if isinstance(self.child_types_data, dict) and 'data' in self.child_types_data:
                for type1_item in self.child_types_data['data']:
                    type1_name = type1_item.get('type1_name', 'Unknown')
                    levels = type1_item.get('levels', [])
                    
                    # Search in levels for this content
                    parent = self._search_content_in_levels(levels, content_name, type1_name)
                    if parent:
                        return parent
            
            return None
        
        def _search_content_in_levels(self, levels, content_name, current_parent):
            """Search for content in levels and return the parent folder name"""
            for level in levels:
                level_name = level.get('name', '')
                children = level.get('children', [])
                
                # Check if this level contains the content
                for child in children:
                    if isinstance(child, dict):
                        child_name = child.get('name', '')
                        if child_name == content_name:
                            print(f"DEBUG: Found content '{content_name}' in folder '{current_parent}'")
                            return current_parent
                
                # Recursively search in children
                if children:
                    result = self._search_content_in_levels(children, content_name, level_name)
                    if result:
                        return result
            
            return None
        
        def _expand_current_folder_context(self):
            """Expand the tree to show the current folder context"""
            print(f"DEBUG: Expanding current folder context")
            
            # Safety check - ensure tree_frame is properly initialized
            if not hasattr(self, 'tree_frame') or not self.tree_frame:
                print(f"DEBUG: tree_frame not ready yet")
                return
            
            # Get the current navigation context
            if hasattr(self, 'navigation_history') and self.navigation_history:
                current_context = self.navigation_history[-1]
                current_folder = current_context.get('node')
                if current_folder:
                    print(f"DEBUG: Current folder context: {current_folder}")
                    # Try to expand this folder in the tree
                    self._direct_expand_tree_node(current_folder)
            else:
                # No navigation history, try to expand based on current breadcrumb
                if hasattr(self, 'breadcrumb_label') and self.breadcrumb_label:
                    try:
                        breadcrumb_text = self.breadcrumb_label.cget('text')
                        print(f"DEBUG: Breadcrumb text: {breadcrumb_text}")
                        
                        # Extract folder name from breadcrumb
                        if ' > ' in breadcrumb_text:
                            parts = breadcrumb_text.split(' > ')
                            if len(parts) > 1:
                                current_folder = parts[1].replace(' (Selected)', '')
                                print(f"DEBUG: Extracted folder from breadcrumb: {current_folder}")
                                # Try to expand this folder in the tree
                                self._direct_expand_tree_node(current_folder)
                    except Exception as e:
                        print(f"DEBUG: Error processing breadcrumb: {e}")
            
            # If we still can't find the context, try to expand the main folders
            # This ensures that at least the top-level structure is visible
            try:
                if not self._is_any_tree_node_expanded():
                    print(f"DEBUG: No tree nodes expanded, expanding main folders")
                    self._expand_main_folders()
            except Exception as e:
                print(f"DEBUG: Error expanding main folders: {e}")
        
        def _is_any_tree_node_expanded(self):
            """Check if any tree nodes are currently expanded"""
            if not hasattr(self, 'tree_frame') or not self.tree_frame:
                return False
            
            try:
                # Look for any expanded nodes (▼ icon)
                return self._check_expanded_nodes_recursive(self.tree_frame)
            except Exception as e:
                print(f"DEBUG: Error checking expanded nodes: {e}")
                return False
        
        def _check_expanded_nodes_recursive(self, widget):
            """Recursively check for expanded nodes"""
            # Safety check - ensure widget is valid
            if not widget or not hasattr(widget, 'winfo_children'):
                return False
            
            try:
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label) and hasattr(child, 'cget'):
                        try:
                            text = child.cget('text')
                            if text == "▼":
                                print(f"DEBUG: Found expanded node")
                                return True
                        except:
                            pass
                    
                    # Recursively check children
                    if self._check_expanded_nodes_recursive(child):
                        return True
                
                return False
            except Exception as e:
                print(f"DEBUG: Error in _check_expanded_nodes_recursive: {e}")
                return False
        
        def _expand_main_folders(self):
            """Expand the main folder structure to show the hierarchy"""
            print(f"DEBUG: Expanding main folders")
            
            # Safety check - ensure tree_frame is properly initialized
            if not hasattr(self, 'tree_frame') or not self.tree_frame:
                print(f"DEBUG: tree_frame not ready yet")
                return
            
            try:
                # Try to expand the main "Suites" section
                for widget in self.tree_frame.winfo_children():
                    if isinstance(widget, tk.Frame):
                        # Check if this is the main section
                        for child in widget.winfo_children():
                            if isinstance(child, tk.Frame):
                                for grandchild in child.winfo_children():
                                    if isinstance(grandchild, tk.Label) and hasattr(grandchild, 'cget'):
                                        try:
                                            if grandchild.cget('text') == "Suites":
                                                print(f"DEBUG: Found main section, expanding")
                                                # This should already be expanded, but let's make sure
                                                # Look for the expand icon and ensure it's expanded
                                                self._ensure_main_section_expanded(child)
                                                return
                                        except Exception as e:
                                            print(f"DEBUG: Error checking grandchild text: {e}")
            except Exception as e:
                print(f"DEBUG: Error expanding main folders: {e}")
        
        def _ensure_main_section_expanded(self, main_section):
            """Ensure the main section is expanded and visible"""
            print(f"DEBUG: Ensuring main section is expanded")
            
            # Safety check - ensure main_section is valid
            if not main_section or not hasattr(main_section, 'winfo_children'):
                print(f"DEBUG: main_section not valid")
                return
            
            try:
                # Look for the expand icon in the main section
                for widget in main_section.winfo_children():
                    if isinstance(widget, tk.Frame):
                        for child in widget.winfo_children():
                            if isinstance(child, tk.Label) and hasattr(child, 'cget'):
                                try:
                                    text = child.cget('text')
                                    if text in ["▶", "▶", "▼"]:
                                        print(f"DEBUG: Found expand icon: {text}")
                                        # If it's collapsed, expand it
                                        if text == "▶":
                                            print(f"DEBUG: Main section is collapsed, expanding")
                                            # Find the content frame and expand it
                                            for content_child in widget.winfo_children():
                                                if isinstance(content_child, tk.Frame) and len(content_child.winfo_children()) == 0:
                                                    content_child.pack(fill=tk.X)
                                                    child.config(text="▼")
                                                    print(f"DEBUG: Main section expanded")
                                                    break
                                        else:
                                            print(f"DEBUG: Main section is already expanded")
                                        break
                                except Exception as e:
                                    print(f"DEBUG: Error checking expand icon: {e}")
            except Exception as e:
                print(f"DEBUG: Error in _ensure_main_section_expanded: {e}")
        
        def _find_tree_node_widget(self, widget, target_name):
            """Find the actual tree node widget"""
            # Safety check - ensure widget is valid
            if not widget or not hasattr(widget, 'winfo_children'):
                return None
            
            # Check if this widget is a label with the target name
            if isinstance(widget, tk.Label) and hasattr(widget, 'cget'):
                try:
                    widget_text = widget.cget('text')
                    if widget_text == target_name:
                        print(f"DEBUG: Found tree node label: {target_name}")
                        return widget
                except Exception as e:
                    print(f"DEBUG: Error checking label text: {e}")
            
            try:
                # Recursively search in all children
                for child in widget.winfo_children():
                    result = self._find_tree_node_widget(child, target_name)
                    if result:
                        return result
            except Exception as e:
                print(f"DEBUG: Error searching children: {e}")
            
            return None
        
        def _simulate_node_click(self, node_widget):
            """Simulate a click on a tree node to expand it"""
            print(f"DEBUG: Simulating click on node widget")
            
            # Find the parent container that has the expand functionality
            parent = node_widget.master
            while parent and not isinstance(parent, tk.Frame):
                parent = parent.master
            
            if parent:
                print(f"DEBUG: Found parent container, checking for expand functionality")
                # Look for expand icon and content frame in the parent
                expand_icon = None
                content_frame = None
                
                for child in parent.winfo_children():
                    if isinstance(child, tk.Frame):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, tk.Label) and grandchild.cget('text') in ["▶", "▶", "▼"]:
                                expand_icon = grandchild
                            elif isinstance(grandchild, tk.Frame) and len(grandchild.winfo_children()) == 0:
                                content_frame = grandchild
                
                if expand_icon and content_frame:
                    print(f"DEBUG: Found expand icon and content frame")
                    # Check if node is collapsed
                    if expand_icon.cget('text') == "▶":
                        print(f"DEBUG: Node is collapsed, expanding it")
                        # Expand the node
                        content_frame.pack(fill=tk.X)
                        expand_icon.config(text="▼")
                        
                        # Update canvas scroll region
                        if hasattr(self, 'tree_canvas'):
                            self.tree_canvas.update_idletasks()
                            self.tree_canvas.configure(scrollregion=self.tree_canvas.bbox("all"))
                        
                        return True
                    else:
                        print(f"DEBUG: Node is already expanded")
                        return True
                else:
                    print(f"DEBUG: Could not find expand icon or content frame")
            
            return False
        

        
        def _search_and_expand_in_section(self, section_frame, target_name):
            """Search for and expand a target node within a section"""
            print(f"DEBUG: Searching section for target: {target_name}")
            
            # Search through all widgets in the section
            for widget in section_frame.winfo_children():
                if isinstance(widget, tk.Frame):
                    # This might be a node container
                    if self._search_in_node_container(widget, target_name):
                        return True
            
            return False
        
        def _search_in_node_container(self, node_container, target_name):
            """Search within a node container for the target"""
            print(f"DEBUG: Searching node container for: {target_name}")
            
            # Look for the header frame and check the folder name
            for widget in node_container.winfo_children():
                if isinstance(widget, tk.Frame):
                    # This is likely the header frame
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Label) and hasattr(child, 'cget'):
                            try:
                                child_text = child.cget('text')
                                print(f"DEBUG: Checking label text: '{child_text}' against target: '{target_name}'")
                                if child_text == target_name:
                                    print(f"DEBUG: Found target node: {target_name}")
                                    # This is the target node - expand it
                                    self._expand_target_node(node_container)
                                    return True
                            except Exception as e:
                                print(f"DEBUG: Error checking label: {e}")
                                pass
                    
                    # If not found in header, check if this is a content frame with children
                    if widget.winfo_children():
                        # Recursively search in child nodes
                        if self._search_in_node_container(widget, target_name):
                            return True
            
            return False
        
        def _expand_target_node(self, node_container):
            """Expand the target node and collapse others"""
            print(f"DEBUG: Expanding target node container")
            
            # Find the node data for this container
            # We need to find the expand_icon and content_frame
            expand_icon = None
            content_frame = None
            
            for widget in node_container.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Label) and child.cget('text') in ["▶", "▶", "▼"]:
                            expand_icon = child
                        elif isinstance(child, tk.Frame) and len(child.winfo_children()) == 0:
                            # This is likely the content frame
                            content_frame = child
            
            if expand_icon and content_frame:
                # Check if node is already expanded
                if expand_icon.cget('text') == "▶":
                    # Node is collapsed, expand it
                    print(f"DEBUG: Expanding collapsed node")
                    content_frame.pack(fill=tk.X)
                    expand_icon.config(text="▼")
                    
                    # If content frame is empty, we need to render the children
                    if not content_frame.winfo_children():
                        print(f"DEBUG: Content frame is empty, need to render children")
                        # This would require accessing the original node data
                        # For now, we'll just expand it
                        pass
                else:
                    print(f"DEBUG: Node is already expanded")
                
                # Ensure all parent nodes are expanded so the target is visible
                self._ensure_parent_nodes_expanded(node_container)
                
                # Update canvas scroll region after expansion
                if hasattr(self, 'tree_canvas'):
                    self.tree_canvas.update_idletasks()
                    self.tree_canvas.configure(scrollregion=self.tree_canvas.bbox("all"))
                
                return True
            else:
                print(f"DEBUG: Could not find expand_icon or content_frame")
                return False
        
        def _ensure_parent_nodes_expanded(self, target_container):
            """Ensure all parent nodes are expanded so the target is visible"""
            print(f"DEBUG: Ensuring parent nodes are expanded")
            
            # Walk up the widget hierarchy to find and expand parent nodes
            current = target_container
            while current and hasattr(current, 'master') and current.master:
                parent = current.master
                if parent and hasattr(parent, 'winfo_children'):
                    # Check if this parent is a node container that needs expansion
                    for child in parent.winfo_children():
                        if isinstance(child, tk.Frame):
                            for grandchild in child.winfo_children():
                                if isinstance(grandchild, tk.Label) and grandchild.cget('text') in ["▶", "▶", "▼"]:
                                    # This is an expand icon - check if parent is collapsed
                                    if grandchild.cget('text') == "▶":
                                        # Find the content frame and expand it
                                        for content_child in child.winfo_children():
                                            if isinstance(content_child, tk.Frame) and len(content_child.winfo_children()) == 0:
                                                print(f"DEBUG: Expanding parent node")
                                                content_child.pack(fill=tk.X)
                                                grandchild.config(text="▼")
                                                break
                                    break
                current = parent
            
            # Update canvas scroll region after all expansions
            if hasattr(self, 'tree_canvas'):
                self.tree_canvas.update_idletasks()
                self.tree_canvas.configure(scrollregion=self.tree_canvas.bbox("all"))
        
        def _expand_matching_tree_nodes(self, target_name):
            """Expand tree nodes that match the target name"""
            print(f"DEBUG: Expanding matching tree nodes for: {target_name}")
            
            # This method is now deprecated in favor of the new tree expansion system
            # Update breadcrumb to show the current navigation
            if hasattr(self, 'breadcrumb_label'):
                current_path = f"Suites > {target_name}"
                self.breadcrumb_label.config(text=current_path)
                print(f"DEBUG: Updated breadcrumb to: {current_path}")
        
        def _highlight_tree_node(self, node_name):
            """Highlight the selected tree node"""
            print(f"DEBUG: Highlighting tree node: {node_name}")
            
            # Clear previous highlights
            self._clear_tree_highlights()
            
            # Find and highlight the target node
            if hasattr(self, 'tree_frame'):
                self._find_and_highlight_node(self.tree_frame, node_name)
            
            # Also highlight the entire path to the node
            self._highlight_tree_path(node_name)
        
        def _highlight_tree_path(self, node_name):
            """Highlight the entire path to the selected node"""
            print(f"DEBUG: Highlighting tree path to: {node_name}")
            
            # Get the current navigation context
            if hasattr(self, 'navigation_history') and self.navigation_history:
                # Highlight the current active folder
                current_context = self.navigation_history[-1]
                current_folder = current_context.get('node')
                if current_folder:
                    print(f"DEBUG: Highlighting current folder: {current_folder}")
                    self._highlight_specific_node(self.tree_frame, current_folder)
            else:
                # Try to highlight based on breadcrumb
                if hasattr(self, 'breadcrumb_label'):
                    breadcrumb_text = self.breadcrumb_label.cget('text')
                    print(f"DEBUG: Breadcrumb text: {breadcrumb_text}")
                    
                    # Extract folder name from breadcrumb
                    if ' > ' in breadcrumb_text:
                        parts = breadcrumb_text.split(' > ')
                        if len(parts) > 1:
                            current_folder = parts[1].replace(' (Selected)', '')
                            print(f"DEBUG: Extracted folder from breadcrumb: {current_folder}")
                            self._highlight_specific_node(self.tree_frame, current_folder)
            
            # Also try to highlight the target node itself
            self._highlight_specific_node(self.tree_frame, node_name)
        
        def _highlight_specific_node(self, widget, target_name):
            """Highlight a specific node in the tree"""
            # Safety check - ensure widget is valid
            if not widget or not hasattr(widget, 'winfo_children'):
                return False
            
            # Check if this widget is a label with the target name
            if isinstance(widget, tk.Label) and hasattr(widget, 'cget'):
                try:
                    widget_text = widget.cget('text')
                    if widget_text == target_name:
                        print(f"DEBUG: Highlighting specific node: {target_name}")
                        # Find the parent container and highlight it
                        parent = widget.master
                        while parent and not isinstance(parent, tk.Frame):
                            parent = parent.master
                        if parent:
                            self._highlight_node_container(parent)
                            return True
                except Exception as e:
                    print(f"DEBUG: Error checking label text: {e}")
            
            try:
                # Recursively search in all children
                for child in widget.winfo_children():
                    if self._highlight_specific_node(child, target_name):
                        return True
            except Exception as e:
                print(f"DEBUG: Error searching children in _highlight_specific_node: {e}")
            
            return False
        
        def _clear_tree_highlights(self):
            """Clear all tree node highlights"""
            if hasattr(self, 'tree_frame'):
                self._clear_highlights_recursive(self.tree_frame)
        
        def _clear_highlights_recursive(self, widget):
            """Recursively clear highlights from all tree widgets"""
            if hasattr(widget, 'configure'):
                try:
                    # Reset background to default
                    if hasattr(widget, 'cget'):
                        current_bg = widget.cget('bg')
                        if current_bg != COLOR_SIDEBAR_BG:
                            widget.configure(bg=COLOR_SIDEBAR_BG)
                except:
                    pass
            
            # Recursively clear children
            for child in widget.winfo_children():
                self._clear_highlights_recursive(child)
        
        def _find_and_highlight_node(self, widget, target_name):
            """Find and highlight a specific node in the tree"""
            for child in widget.winfo_children():
                if isinstance(child, tk.Frame):
                    # Check if this is a node container
                    if self._is_node_container(child, target_name):
                        # Highlight this node
                        self._highlight_node_container(child)
                        return True
                    
                    # Recursively search in children
                    if self._find_and_highlight_node(child, target_name):
                        return True
            
            return False
        
        def _is_node_container(self, widget, target_name):
            """Check if a widget is a node container for the target name"""
            for child in widget.winfo_children():
                if isinstance(child, tk.Frame):
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, tk.Label) and hasattr(grandchild, 'cget'):
                            try:
                                child_text = grandchild.cget('text')
                                if child_text == target_name:
                                    return True
                            except:
                                pass
            return False
        
        def _highlight_node_container(self, node_container):
            """Highlight a specific node container"""
            try:
                # Highlight the main container
                node_container.configure(bg=COLOR_SECONDARY)
                
                # Also highlight the header frame if it exists
                for child in node_container.winfo_children():
                    if isinstance(child, tk.Frame):
                        child.configure(bg=COLOR_SECONDARY)
                        # Highlight labels in the header
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, tk.Label):
                                grandchild.configure(bg=COLOR_SECONDARY)
            except:
                pass
        
        def _scroll_tree_to_node(self, node_name):
            """Scroll the tree to make the selected node visible"""
            print(f"DEBUG: Scrolling tree to node: {node_name}")
            
            if not hasattr(self, 'tree_canvas'):
                return
            
            # Find the node widget
            node_widget = self._find_node_widget(self.tree_frame, node_name)
            if node_widget:
                # Calculate the position to scroll to
                try:
                    # Get the widget's position relative to the tree frame
                    widget_y = node_widget.winfo_y()
                    
                    # Scroll to make the widget visible
                    self.tree_canvas.yview_moveto(max(0, (widget_y - 50) / self.tree_frame.winfo_height()))
                    
                    print(f"DEBUG: Scrolled tree to y position: {widget_y}")
                except Exception as e:
                    print(f"DEBUG: Error scrolling tree: {e}")
            else:
                print(f"DEBUG: Could not find node widget for scrolling: {node_name}")
        
        def _find_node_widget(self, widget, target_name):
            """Find the widget for a specific node name"""
            for child in widget.winfo_children():
                if isinstance(child, tk.Frame):
                    # Check if this is the target node
                    if self._is_node_container(child, target_name):
                        return child
                    
                    # Recursively search in children
                    result = self._find_node_widget(child, target_name)
                    if result:
                        return result
            
            return None
        
        def expand_tree_to_path(self, path_parts):
            """Expand the tree to show a specific path (e.g., ['ITSAR', 'subfolder'])"""
            print(f"DEBUG: Expanding tree to path: {path_parts}")
            
            if not path_parts:
                return False
            
            # Start from the root and expand each level
            current_node = path_parts[0]
            success = self._expand_tree_node(current_node)
            
            if success and len(path_parts) > 1:
                # Recursively expand to deeper levels
                for i in range(1, len(path_parts)):
                    next_node = path_parts[i]
                    print(f"DEBUG: Expanding to next level: {next_node}")
                    # Wait a bit for the previous expansion to complete
                    self.after(100, lambda n=next_node: self._expand_tree_node(n))
            
            return success
        
        def _clear_grid(self):
            """Clear the grid display"""
            for widget in self.grid_frame.winfo_children():
                widget.destroy()
        
        def _get_items_for_node(self, node_name, item_id=""):
            """Extract items from API data for the selected node"""
            items = []
            
            if not self.child_types_data:
                return items
            
            # Search through the API data to find items for this node
            if isinstance(self.child_types_data, dict) and 'data' in self.child_types_data:
                for type1_item in self.child_types_data['data']:
                    levels = type1_item.get('levels', [])
                    items.extend(self._search_items_in_levels(levels, node_name, item_id))
            
            return items
        
        def _get_direct_children(self, node_name):
            """Get only the direct children of a specific node"""
            direct_children = []
            
            if not self.child_types_data:
                print(f"DEBUG: No child_types_data available")
                return direct_children
            
            print(f"DEBUG: child_types_data structure: {type(self.child_types_data)}")
            if isinstance(self.child_types_data, dict):
                # print(f"DEBUG: Keys in child_types_data: {list(self.child_types_data.keys())}")
                if 'data' in self.child_types_data:
                    print(f"DEBUG: Number of type1 items: {len(self.child_types_data['data'])}")
                    for i, type1_item in enumerate(self.child_types_data['data']):
                        type1_name = type1_item.get('type1_name', 'Unknown')
                        print(f"DEBUG: Type1 item {i}: {type1_name}")
                        
                        # Check if the clicked node is this type1 item
                        if type1_name == node_name:
                            print(f"DEBUG: Found type1 item '{node_name}', getting its level children")
                            levels = type1_item.get('levels', [])
                            print(f"DEBUG: Number of levels: {len(levels)}")
                            # Get the names of the top-level items under this type1
                            for level in levels:
                                level_name = level.get('name', 'Unknown')
                                direct_children.append(level_name)
                                print(f"DEBUG: Added top-level child: {level_name}")
                            return direct_children
                        
                        # If not found in type1, search in levels
                        levels = type1_item.get('levels', [])
                        print(f"DEBUG: Number of levels: {len(levels)}")
                        found = self._find_node_and_get_children(levels, node_name, direct_children)
                        if found:
                            break
                else:
                    print(f"DEBUG: No 'data' key found in child_types_data")
            else:
                print(f"DEBUG: child_types_data is not a dict, it's: {type(self.child_types_data)}")
            
            # Debug: Print what we found
            print(f"DEBUG: Looking for children of '{node_name}'")
            print(f"DEBUG: Found {len(direct_children)} children: {direct_children}")
            
            return direct_children
        
        def _find_node_and_get_children(self, levels, target_name, children_list):
            """Find a specific node and get its direct children"""
            for level in levels:
                level_name = level.get('name', '')
                
                if level_name == target_name:
                    # Found the target node, get its direct children
                    direct_children = level.get('children', [])
                    print(f"DEBUG: Found node '{target_name}' with {len(direct_children)} children")
                    for child in direct_children:
                        child_name = child.get('name', 'Unknown')
                        children_list.append(child_name)
                        print(f"DEBUG: Added child: {child_name}")
                    return True
                
                # Recursively search in children
                child_levels = level.get('children', [])
                if child_levels:
                    found = self._find_node_and_get_children(child_levels, target_name, children_list)
                    if found:
                        return True
            
            return False
        
        def _search_items_in_levels(self, levels, target_name, target_id=""):
            """Recursively search for items in levels"""
            items = []
            
            for level in levels:
                level_name = level.get('name', '')
                level_id = level.get('id', '')
                children = level.get('children', [])
                
                # Check if this is the target level
                if (level_name == target_name and 
                    (not target_id or level_id == target_id)):
                    # This is the target level, extract its children as items
                    for child in children:
                        if not child.get('children'):  # Only leaf nodes
                            items.append(child.get('name', 'Unknown'))
                    break
                
                # Recursively search in children
                if children:
                    items.extend(self._search_items_in_levels(children, target_name, target_id))
            
            return items
        
        def _get_all_tree_items(self):
            """Extract all items from the entire tree structure"""
            all_items = []
            
            if not self.child_types_data:
                return all_items
            
            # Search through the API data to find all leaf nodes
            if isinstance(self.child_types_data, dict) and 'data' in self.child_types_data:
                for type1_item in self.child_types_data['data']:
                    levels = type1_item.get('levels', [])
                    all_items.extend(self._extract_all_leaf_items(levels))
            
            return all_items
        
        def _extract_all_leaf_items(self, levels):
            """Recursively extract all leaf items from levels"""
            items = []
            
            for level in levels:
                children = level.get('children', [])
                
                if not children:
                    # This is a leaf node, add it
                    level_name = level.get('name', 'Unknown')
                    items.append(level_name)
                else:
                    # This has children, recursively extract from them
                    items.extend(self._extract_all_leaf_items(children))
            
            return items
        
        def _display_grid_items(self, node_name, item_id=""):
            """Display items in the grid based on selected node"""
            # Clear existing grid
            for widget in self.grid_frame.winfo_children():
                widget.destroy()
            
            # Extract items from the API data based on the selected node
            items = self._get_items_for_node(node_name, item_id)
            
            # If no items found, get direct children of the clicked node
            if not items:
                items = self._get_direct_children(node_name)
            
            # If still no items, create a single card for the clicked node itself
            if not items:
                # Create a single card for the clicked node
                item_frame = tk.Frame(self.grid_frame, bg=COLOR_PANEL_BG, relief=tk.FLAT, bd=1)
                item_frame.pack(pady=50)
                
                # Create icon canvas
                icon_canvas = tk.Canvas(item_frame, width=80, height=80, 
                                        bg=COLOR_PANEL_BG, highlightthickness=0)
                icon_canvas.pack(pady=(15, 8))
                
                # Check if this item is a folder (has children)
                children = self._get_direct_children(node_name)
                
                # Debug logging for folder detection
                print(f"DEBUG: Single item '{node_name}' - children: {children}, len: {len(children) if children else 0}")
                
                # Improved folder detection logic
                # If we can't determine children, assume it's a folder for now
                # This ensures consistent yellow coloring until we fix the API data parsing
                is_folder = True if not children else len(children) > 0
                
                if is_folder:
                    # This is a folder - draw pixelated folder icon with same design as tree
                    # Main folder body (darker golden yellow)
                    icon_canvas.create_rectangle(10, 30, 70, 70, fill="#D4A017", outline="#D4A017")
                    # Folder tab (lighter yellow) - positioned on top left
                    icon_canvas.create_rectangle(20, 15, 50, 40, fill="#FFD966", outline="#FFD966")
                else:
                    # This is a file - draw file icon with proper colors and better contrast
                    icon_canvas.create_rectangle(10, 30, 70, 70, fill="#F0F0F0", outline="#B0B0B0", width=2)
                    icon_canvas.create_rectangle(20, 15, 50, 40, fill="#FFFFFF", outline="#B0B0B0", width=2)
                    
                    # Add file indicator text with better visibility
                    icon_canvas.create_text(40, 75, text="📄", font=(FONT_FAMILY_PRIMARY, 16), fill="#444444")
                
                # Node name label
                name_label = tk.Label(item_frame, text=node_name, font=(FONT_FAMILY_PRIMARY, 11), 
                                    fg=COLOR_TEXT_LIGHT, bg=COLOR_PANEL_BG, 
                                    wraplength=200, justify="center")
                name_label.pack(pady=(0, 15))
                
                # Add hover effect
                def on_enter(e, frame=item_frame):
                    frame.configure(bg=COLOR_SECONDARY)
                
                def on_leave(e, frame=item_frame):
                    frame.configure(bg=COLOR_PANEL_BG)
                
                item_frame.bind("<Enter>", on_enter)
                item_frame.bind("<Leave>", on_leave)
                
                # Add click handler
                item_frame.bind("<Button-1>", lambda e, n=node_name: self._on_grid_item_click(n))
                icon_canvas.bind("<Button-1>", lambda e, n=node_name: self._on_grid_item_click(n))
                name_label.bind("<Button-1>", lambda e, n=node_name: self._on_grid_item_click(n))
                
                # Add double-click handler
                item_frame.bind("<Double-Button-1>", lambda e, n=node_name: self._on_grid_item_double_click(n))
                icon_canvas.bind("<Double-Button-1>", lambda e, n=node_name: self._on_grid_item_double_click(n))
                name_label.bind("<Double-Button-1>", lambda e, n=node_name: self._on_grid_item_double_click(n))
                return
            
            # Display the items as cards
            self._display_grid_items_from_list(items, node_name)
            
            # Update breadcrumb to show current selection
            self._update_breadcrumb_path(node_name)
            
            # Update back button visibility
            self._update_back_button_visibility()
        
        def _display_grid_items_from_list(self, items, parent_name):
            """Display a list of items as cards in the grid"""
            # Clear existing grid
            for widget in self.grid_frame.winfo_children():
                widget.destroy()
            
            if not items:
                return
            
            # Update navigation context to track current folder
            self._update_navigation_context(parent_name)
            
            # Create grid layout with more columns for better space utilization
            max_cols = 8
            for idx, item in enumerate(items):
                row = idx // max_cols
                col = idx % max_cols
                
                # Create item frame with better styling
                item_frame = tk.Frame(self.grid_frame, bg=COLOR_PANEL_BG, relief=tk.FLAT, bd=1)
                item_frame.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
                
                # Create icon canvas
                icon_canvas = tk.Canvas(item_frame, width=60, height=60, 
                                        bg=COLOR_PANEL_BG, highlightthickness=0)
                icon_canvas.pack(pady=(15, 8))
                
                # Item name label with better text handling
                if isinstance(item, dict):
                    item_name = item.get('name', str(item))
                else:
                    item_name = str(item)
                
                # Check if this item is a folder (has children)
                children = self._get_direct_children(item_name)
                
                # Debug logging for folder detection
                print(f"DEBUG: Item '{item_name}' - children: {children}, len: {len(children) if children else 0}")
                
                # Improved folder detection logic
                # If we can't determine children, assume it's a folder for now
                # This ensures consistent yellow coloring until we fix the API data parsing
                is_folder = True if not children else len(children) > 0
                
                if is_folder:
                    # This is a folder - draw pixelated folder icon with same design as tree
                    # Main folder body (darker golden yellow)
                    icon_canvas.create_rectangle(8, 22, 52, 52, fill="#D4A017", outline="#D4A017")
                    # Folder tab (lighter yellow) - positioned on top left
                    icon_canvas.create_rectangle(15, 11, 37, 30, fill="#FFD966", outline="#FFD966")
                else:
                    # This is a file - draw file icon with proper colors and better contrast
                    icon_canvas.create_rectangle(8, 22, 52, 52, fill="#F0F0F0", outline="#B0B0B0", width=2)
                    icon_canvas.create_rectangle(15, 11, 37, 30, fill="#FFFFFF", outline="#B0B0B0", width=2)
                    
                    # Add file indicator text with better visibility
                    icon_canvas.create_text(30, 55, text="📄", font=(FONT_FAMILY_PRIMARY, 12), fill="#444444")
                
                # Truncate long names and add ellipsis if needed
                max_chars = 25
                if len(item_name) > max_chars:
                    display_name = item_name[:max_chars] + "..."
                else:
                    display_name = item_name
                
                name_label = tk.Label(item_frame, text=display_name, font=(FONT_FAMILY_PRIMARY, 9), 
                                    fg=COLOR_TEXT_LIGHT, bg=COLOR_PANEL_BG, 
                                    wraplength=100, justify="center")
                name_label.pack(pady=(0, 15))
                
                # Add hover effect
                def on_enter(e, frame=item_frame):
                    frame.configure(bg=COLOR_SECONDARY)
                
                def on_leave(e, frame=item_frame):
                    frame.configure(bg=COLOR_PANEL_BG)
                
                item_frame.bind("<Enter>", on_enter)
                item_frame.bind("<Leave>", on_leave)
                
                # Add click handler - pass the item name for better handling
                item_frame.bind("<Button-1>", lambda e, i=item_name: self._on_grid_item_click(i))
                icon_canvas.bind("<Button-1>", lambda e, i=item_name: self._on_grid_item_click(i))
                name_label.bind("<Button-1>", lambda e, i=item_name: self._on_grid_item_click(i))
                
                # Add double-click handler for folders
                item_frame.bind("<Double-Button-1>", lambda e, i=item_name: self._on_grid_item_double_click(i))
                icon_canvas.bind("<Double-Button-1>", lambda e, i=item_name: self._on_grid_item_double_click(i))
                name_label.bind("<Double-Button-1>", lambda e, i=item_name: self._on_grid_item_double_click(i))
                
                # Add right-click context menu for folders
                if is_folder:
                    item_frame.bind("<Button-3>", lambda e, i=item_name: self._show_folder_context_menu(e, i))
                    icon_canvas.bind("<Button-3>", lambda e, i=item_name: self._show_folder_context_menu(e, i))
                    name_label.bind("<Button-3>", lambda e, i=item_name: self._show_folder_context_menu(e, i))
            
            # Configure grid columns
            for i in range(max_cols):
                self.grid_frame.grid_columnconfigure(i, weight=1)
            
            # Update breadcrumb to show current parent
            self._update_breadcrumb_path(parent_name)
            
            # Show back button when displaying folder contents
            self._update_back_button_visibility()
        
        def _update_navigation_context(self, folder_name):
            """Update the navigation context to track current folder"""
            print(f"DEBUG: Updating navigation context to: {folder_name}")
            
            # Store the current folder context
            if not hasattr(self, 'current_folder_context'):
                self.current_folder_context = {}
            
            self.current_folder_context['folder'] = folder_name
            self.current_folder_context['timestamp'] = time.time()
            
            # Also update the breadcrumb to show the current folder
            if hasattr(self, 'breadcrumb_label') and self.breadcrumb_label:
                try:
                    self.breadcrumb_label.config(text=f"Suites > {folder_name}")
                except Exception as e:
                    print(f"DEBUG: Error updating breadcrumb: {e}")
            
            # Try to expand and highlight this folder in the tree
            try:
                self._expand_tree_node(folder_name)
                self._highlight_tree_node(folder_name)
            except Exception as e:
                print(f"DEBUG: Error expanding/highlighting tree node: {e}")
            
            # print(f"DEBUG: Navigation context updated: {self.current_folder_context}")
        
        def _on_grid_item_click(self, item_name):
            """Handle grid item single click - select item only"""
            print(f"Grid item clicked (single): {item_name}")
            print(f"DEBUG: Starting tree expansion for: {item_name}")
            
            # Single click = Select item (highlight it)
            # Clear previous selection
            self._clear_grid_selection()
            
            # Highlight the clicked item
            self._select_grid_item(item_name)
            
            # Update selected node for reference
            self.selected_node = item_name
            
            # Update breadcrumb to show selection (but don't navigate)
            if hasattr(self, 'breadcrumb_label'):
                self.breadcrumb_label.config(text=f"Suites > {item_name} (Selected)")
            
            # Also expand the corresponding node in the tree to show selection
            # This helps users see which folder is selected in the tree view
            # For top-level folders, this will expand the tree to show the selection
            print(f"DEBUG: Calling _expand_tree_node_by_name for: {item_name}")
            self._expand_tree_node_by_name(item_name)
            
            # Ensure the tree scrolls to show the selected item
            print(f"DEBUG: Calling _scroll_tree_to_node for: {item_name}")
            self._scroll_tree_to_node(item_name)
            
            # Try direct tree expansion as well
            print(f"DEBUG: Calling _direct_expand_tree_node for: {item_name}")
            result = self._direct_expand_tree_node(item_name)
            print(f"DEBUG: Direct expansion result: {result}")
            
            # Also try to expand the current folder context
            self._expand_current_folder_context()
            
            print(f"DEBUG: Item '{item_name}' selected (single click)")
        
        def _show_folder_context_menu(self, event, item_name):
            """Show context menu for folder items with Open/Execute options"""
            menu = tk.Menu(self, tearoff=0)
            
            # Add menu items
            menu.add_command(
                label="Open",
                command=lambda: self._navigate_into_folder(item_name)
            )
            menu.add_separator()
            menu.add_command(
                label="Execute Security Report",
                command=lambda: self._execute_security_report_for_folder(item_name)
            )
            
            # Store the menu as an instance variable
            self._context_menu = menu
            
            def on_click_outside(event):
                # Check if the click was outside the menu
                widget = event.widget
                while widget:
                    if widget == menu:
                        return
                    widget = widget.master
                # If we got here, the click was outside the menu
                menu.unpost()
            
            def on_menu_unmap(event):
                # Clean up bindings when menu is closed
                if hasattr(self, '_click_binding'):
                    self.unbind_all("<Button-1>")
                    delattr(self, '_click_binding')
                if hasattr(self, '_context_menu'):
                    delattr(self, '_context_menu')
            
            # Bind the unmap event
            menu.bind("<Unmap>", on_menu_unmap, add='+')
            
            # Show the menu
            try:
                menu.tk_popup(event.x_root, event.y_root)
                # Bind click outside to close menu
                self._click_binding = self.bind_all("<Button-1>", on_click_outside, add='+')
            except Exception as e:
                print(f"Error showing context menu: {e}")
                menu.destroy()
                if hasattr(self, '_context_menu'):
                    delattr(self, '_context_menu')
                
        def _navigate_into_folder(self, item_name):
            """Navigate into the specified folder"""
            children = self._get_direct_children(item_name)
            if children:
                self._navigate_to_folder(item_name, children)
                
        def _get_folder_id_by_name(self, folder_name):
            """Find the folder ID by its name in the child_types_data"""
            if not hasattr(self, 'child_types_data') or not self.child_types_data:
                return None
                
            if isinstance(self.child_types_data, dict) and 'data' in self.child_types_data:
                for type1_item in self.child_types_data['data']:
                    levels = type1_item.get('levels', [])
                    folder_id = self._find_folder_id_in_levels(levels, folder_name)
                    if folder_id:
                        return folder_id
            return None
            
        def _find_folder_id_in_levels(self, levels, target_name):
            """Recursively search for a folder by name and return its ID"""
            for level in levels:
                if level.get('name') == target_name:
                    return level.get('id')
                children = level.get('children', [])
                if children:
                    found_id = self._find_folder_id_in_levels(children, target_name)
                    if found_id:
                        return found_id
            return None
        
        def _clean_input_directory(self):
            """Clean the Input directory by removing all files and subdirectories"""
            try:
                cwd = os.getcwd()
                generator_dir = os.path.join(cwd, 'Report_Generator_Automation-main')
                input_dir = os.path.join(generator_dir, 'Input')
                
                if os.path.exists(input_dir):
                    log_debug(f"Cleaning Input directory: {input_dir}")
                    for filename in os.listdir(input_dir):
                        file_path = os.path.join(input_dir, filename)
                        try:
                            if os.path.isfile(file_path) or os.path.islink(file_path):
                                os.unlink(file_path)
                                log_debug(f"Removed file: {filename}")
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                                log_debug(f"Removed directory: {filename}")
                        except Exception as e:
                            log_warning(f"Failed to delete {file_path}. Reason: {e}")
                    log_debug("Input directory cleaned successfully")
                else:
                    log_debug("Input directory does not exist, nothing to clean")
            except Exception as e:
                log_error(f"Failed to clean Input directory: {e}")
        
        def _execute_security_report_for_folder(self, item_name):
            """Execute security report for the specified folder"""
            import os
            log_debug(f"Executing security report for folder: {item_name}")
            
            # Get the folder ID
            folder_id = self._get_folder_id_by_name(item_name)
            if folder_id:
                log_debug(f"Found folder ID: {folder_id}")
                
                # Make GET request to configuration/download/{folder_id}
                try:
                    import requests
                    from urllib.parse import urljoin
                    
                    # Get base URL from config or use instance variable
                    base_url = getattr(self, 'base_url', 'https://wingzai.deltaphi.in/')
                    
                    # Construct the download URL
                    download_url = urljoin(base_url, f"api/configuration/download/{folder_id}")
                    log_debug(f"Making GET request to: {download_url}")
                    
                    # Make the GET request
                    response = requests.get(
                        download_url,
                        headers={"Authorization": f"Bearer {self.token}"},
                        stream=True
                    )
                    
                    if response.status_code == 200:
                        log_debug("Successfully downloaded configuration")
                        
                        # Ensure Report_Generator_Automation-main/Input exists
                        cwd = os.getcwd()
                        generator_dir = os.path.join(cwd, 'Report_Generator_Automation-main')
                        input_dir = os.path.join(generator_dir, 'Input')
                        
                        # Create Input directory if it doesn't exist
                        os.makedirs(input_dir, exist_ok=True)
                        
                        # Create a temporary zip file
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
                            zip_path = tmp_zip.name
                            # Save the content to the temp file
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:  # filter out keep-alive new chunks
                                    tmp_zip.write(chunk)
                        
                        log_debug("Saved configuration to temporary file")
                        
                        # Extract the zip file directly to Input directory
                        try:
                            import zipfile
                            import shutil
                            
                            # First, clear the Input directory
                            for filename in os.listdir(input_dir):
                                file_path = os.path.join(input_dir, filename)
                                try:
                                    if os.path.isfile(file_path) or os.path.islink(file_path):
                                        os.unlink(file_path)
                                    elif os.path.isdir(file_path):
                                        shutil.rmtree(file_path)
                                except Exception as e:
                                    log_warning(f'Failed to delete {file_path}. Reason: {e}')
                            
                            # Extract the zip contents directly to Input directory
                            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                log_debug("ZIP file contents:")
                                for name in zip_ref.namelist():
                                    log_debug(f"  - {name}")
                                
                                # Extract all files directly to Input directory
                                for member in zip_ref.namelist():
                                    log_debug(f"Processing zip member: {member}")
                                    
                                    # Skip directories
                                    if not member.endswith('/'):
                                        # Use the member path as-is (no root folder removal needed)
                                        member_path = member
                                        
                                        log_debug(f"Member path: {member_path}")
                                        
                                        # Ensure the target directory exists
                                        target_path = os.path.join(input_dir, member_path)
                                        target_dir = os.path.dirname(target_path)
                                        
                                        if target_dir:
                                            os.makedirs(target_dir, exist_ok=True)
                                            log_debug(f"Created directory: {target_dir}")
                                        
                                        log_debug(f"Extracting to: {target_path}")
                                        
                                        # Extract the file
                                        with zip_ref.open(member) as source, open(target_path, 'wb') as target:
                                            shutil.copyfileobj(source, target)
                            
                            log_debug(f"Extracted files to {input_dir}")
                            
                        except Exception as e:
                            log_error(f"Could not extract zip file: {str(e)}")
                            raise
                        finally:
                            # Clean up the temporary zip file
                            try:
                                os.remove(zip_path)
                            except Exception as e:
                                log_warning(f"Could not remove temporary file {zip_path}: {e}")
                    elif response.status_code == 404:
                        log_debug("No configuration files found on server for this testcase")
                        # Clean the Input directory since no files exist on server
                        self._clean_input_directory()
                    else:
                        log_warning(f"Failed to download configuration. Status code: {response.status_code}")
                        log_warning(f"Response: {response.text}")
                        
                except Exception as e:
                    log_error(f"Exception while downloading configuration: {str(e)}")
            else:
                log_warning(f"Could not find ID for folder: {item_name}")
                # If no folder ID found, clean the Input directory since no files exist on server
                self._clean_input_directory()
            
            import subprocess
            import os
            from tkinter import messagebox
            
            try:
                # Look for Report_Generator_Automation-main in the same directory as this script
                script_dir = os.path.dirname(os.path.abspath(__file__))
                generator_dir = os.path.join(script_dir, 'Report_Generator_Automation-main')
                log_debug(f"Looking for generator in: {generator_dir}")
                
                if not generator_dir or not os.path.isdir(generator_dir):
                    error_msg = "Report_Generator_Automation-main directory not found in current working directory"
                    log_error(error_msg)
                    messagebox.showerror("Error", error_msg)
                    return
                

                
                # ✅ Load config values first (token and base_url)
                config = load_config()
                token = getattr(self, 'token', None) or config.get('token', '')
                base_url = getattr(self, 'base_url', None) or config.get('base_url', 'https://wingzai.deltaphi.in/')

                # ✅ Prepare JSON data
                data = {
                    "token": token,
                    "base_url": base_url,
                    "testcase_id": folder_id,
                    "testcase_name": item_name
                }

                # ✅ Path to JSON file - use home directory to avoid permission issues in .deb installation
                input_json_path = os.path.expanduser("~/1.json")
                log_debug(f"Writing test JSON: {input_json_path}")

                try:
                    with open(input_json_path, "w") as f:
                        json.dump(data, f, indent=4)
                    log_debug(f"Updated {input_json_path} with {data}")
                except Exception as e:
                    log_error(f"Could not write JSON file: {e}")


                # Look for security_report_generator.py in the found directory
                script_path = os.path.join(generator_dir, "security_report_generator.py")
                log_debug(f"Looking for script at: {script_path}")
                
                if not os.path.exists(script_path):
                    error_msg = f"security_report_generator.py not found in {generator_dir}"
                    log_error(error_msg)
                    messagebox.showerror("Error", error_msg)
                    return
                
                # Prepare the command to run the script with the folder name as testcase
                cmd = ["python3", script_path, "--testcase", item_name]
                
                log_debug(f"Executing command: {' '.join(cmd)}")
                
                # Run the script in a non-blocking way without capturing output
                try:
                    # Use os.devnull to discard output instead of capturing it
                    with open(os.devnull, 'w') as devnull:
                        process = subprocess.Popen(
                            cmd,
                            stdout=devnull,
                            stderr=devnull,
                            start_new_session=True
                        )
                    messagebox.showinfo(
                        "Success",
                        f"Started security report generation for: {item_name}"
                    )
                except Exception as e:
                    error_msg = f"Failed to start security report generator: {str(e)}"
                    log_error(error_msg)
                    messagebox.showerror("Error", error_msg)
                    
            except Exception as e:
                error_msg = f"Error executing security report: {str(e)}"
                log_error(error_msg)
                messagebox.showerror("Error", error_msg)
            
        def _navigate_to_folder(self, item_name, children):
            """Common method to navigate to a folder"""
            print(f"DEBUG: Navigating into folder '{item_name}' with {len(children)} children")
            
            # Update breadcrumb to show the deeper navigation
            if hasattr(self, 'selected_node') and self.selected_node:
                self.breadcrumb_label.config(text=f"Suites > {self.selected_node} > {item_name}")
            else:
                self.breadcrumb_label.config(text=f"Suites > {item_name}")
            
            # Update selected node to the clicked folder
            self.selected_node = item_name
            
            # Display the contents of this folder
            self._display_grid_items_from_list(children, item_name)
            
            # Store navigation history for back functionality
            if not hasattr(self, 'navigation_history'):
                self.navigation_history = []
            self.navigation_history.append({
                'node': item_name,
                'parent': getattr(self, 'selected_node', None),
                'children': children
            })
            
            # Update back button visibility
            self._update_back_button_visibility()
            
            # Also expand the corresponding node in the tree
            self._expand_tree_node_by_name(item_name)
            
            # Ensure the tree scrolls to show the expanded item
            self._scroll_tree_to_node(item_name)
            
            # Try direct tree expansion as well
            self._direct_expand_tree_node(item_name)
            
            # Update breadcrumb to show the current navigation path
            self._update_breadcrumb_path(item_name)
            
        def _on_grid_item_double_click(self, item_name):
            """Handle grid item double-click - open/navigate into folder or execute test case"""
            print(f"Grid item double-clicked: {item_name}")
            
            # First check if this is a test case item that should execute the security report
            # Look for the item in the test cases data structure
            is_test_case = False
            if hasattr(self, 'test_cases_data'):
                for status, test_cases in self.test_cases_data.items():
                    if item_name in test_cases:
                        is_test_case = True
                        break
            
            if is_test_case:
                print(f"DEBUG: Double-clicked test case '{item_name}', executing security report")
                # Use the same handler as the Kanban view
                self._on_task_double_click(item_name)
                return
                
            # If not a test case, treat as folder navigation
            children = self._get_direct_children(item_name)
            if children:
                self._navigate_to_folder(item_name, children)
            
            if children:
                # This is a folder - navigate into it
                print(f"DEBUG: Double-clicked folder '{item_name}' with {len(children)} children")
                
                # Update breadcrumb to show the deeper navigation
                if hasattr(self, 'selected_node') and self.selected_node:
                    self.breadcrumb_label.config(text=f"Suites > {self.selected_node} > {item_name}")
                else:
                    self.breadcrumb_label.config(text=f"Suites > {item_name}")
                
                # Update selected node to the clicked folder
                self.selected_node = item_name
                
                # Display the contents of this folder
                self._display_grid_items_from_list(children, item_name)
                
                # Store navigation history for back functionality
                if not hasattr(self, 'navigation_history'):
                    self.navigation_history = []
                self.navigation_history.append({
                    'node': item_name,
                    'parent': getattr(self, 'selected_node', None),
                    'children': children
                })
                
                # Update back button visibility
                self._update_back_button_visibility()
                
                # Also expand the corresponding node in the tree
                self._expand_tree_node_by_name(item_name)
                
                # Ensure the tree scrolls to show the expanded item
                self._scroll_tree_to_node(item_name)
                
                # Try direct tree expansion as well
                self._direct_expand_tree_node(item_name)
                
                # Update breadcrumb to show the current navigation path
                self._update_breadcrumb_path(item_name)
                
            else:
                # This is a file - show detailed content
                print(f"DEBUG: Double-clicked file '{item_name}', showing detailed content")
                
                # Update breadcrumb to show the selected item
                if hasattr(self, 'selected_node') and self.selected_node:
                    self.breadcrumb_label.config(text=f"Suites > {self.selected_node} > {item_name}")
                else:
                    self.breadcrumb_label.config(text=f"Suites > {item_name}")
                
                # Update selected node
                self.selected_node = item_name
                
                # Display content for this specific item
                self._display_item_content(item_name)
        
        def _clear_grid_selection(self):
            """Clear any existing grid item selection"""
            # Reset all grid items to default background
            for widget in self.grid_frame.winfo_children():
                if hasattr(widget, 'configure'):
                    try:
                        widget.configure(bg=COLOR_PANEL_BG)
                        # Also reset icon canvas backgrounds
                        for child in widget.winfo_children():
                            if isinstance(child, tk.Canvas):
                                child.configure(bg=COLOR_PANEL_BG)
                    except:
                        pass
        
        def _select_grid_item(self, item_name):
            """Highlight the selected grid item"""
            # Find the item frame and highlight it
            for widget in self.grid_frame.winfo_children():
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Label) and hasattr(child, 'cget'):
                            try:
                                child_text = child.cget('text')
                                # Check if this is the name label with the item name
                                if child_text == item_name or (len(child_text) > 25 and child_text.endswith('...') and item_name.startswith(child_text[:-3])):
                                    # Highlight the parent frame
                                    widget.configure(bg=COLOR_SECONDARY)
                                    # Also highlight the icon canvas if it exists
                                    for canvas_child in widget.winfo_children():
                                        if isinstance(canvas_child, tk.Canvas):
                                            canvas_child.configure(bg=COLOR_SECONDARY)
                                    return
                            except:
                                pass
        
        def _update_breadcrumb_path(self, node_name):
            """Update breadcrumb to show the current navigation path"""
            if hasattr(self, 'breadcrumb_label'):
                # Build the path based on the current selection
                path_parts = ["Suites"]
                
                # Add the current node
                if node_name:
                    path_parts.append(node_name)
                
                # Update breadcrumb
                breadcrumb_text = " > ".join(path_parts)
                self.breadcrumb_label.config(text=breadcrumb_text)
                
                # Update breadcrumb styling to show current level
                if node_name:
                    self.breadcrumb_label.config(fg=COLOR_PRIMARY, font=(FONT_FAMILY_PRIMARY, 10, "bold"))
                else:
                    self.breadcrumb_label.config(fg=COLOR_TEXT_MUTED_DARK_BG, font=(FONT_FAMILY_PRIMARY, 10))
        
        def _display_item_content(self, item_name):
            """Display detailed content for a specific item"""
            # Clear existing grid
            for widget in self.grid_frame.winfo_children():
                widget.destroy()
            
            # Create a detailed view for the selected item
            content_frame = tk.Frame(self.grid_frame, bg=COLOR_PANEL_BG, relief=tk.FLAT, bd=1)
            content_frame.pack(pady=50, padx=50, fill=tk.BOTH, expand=True)
            
            # Item header
            header_frame = tk.Frame(content_frame, bg=COLOR_PANEL_BG)
            header_frame.pack(fill=tk.X, pady=(20, 30))
            
            # Item icon (larger folder icon)
            icon_canvas = tk.Canvas(header_frame, width=100, height=100, 
                                  bg=COLOR_PANEL_BG, highlightthickness=0)
            icon_canvas.pack(pady=(0, 20))
            
            # Draw larger pixelated folder icon with same design as tree
            # Main folder body (darker golden yellow)
            icon_canvas.create_rectangle(15, 40, 85, 90, fill="#D4A017", outline="#D4A017")
            # Folder tab (lighter yellow) - positioned on top left
            icon_canvas.create_rectangle(25, 20, 65, 50, fill="#FFD966", outline="#FFD966")
            
            # Item name
            name_label = tk.Label(header_frame, text=item_name, font=(FONT_FAMILY_PRIMARY, 16, "bold"), 
                                    fg=COLOR_TEXT_LIGHT, bg=COLOR_PANEL_BG, 
                                wraplength=400, justify="center")
            name_label.pack(pady=(0, 20))
            
            # Item details section
            details_frame = tk.Frame(content_frame, bg=COLOR_PANEL_BG)
            details_frame.pack(fill=tk.BOTH, expand=True, padx=40)
            
            # Get item details from API data
            item_details = self._get_item_details(item_name)
            
            if item_details:
                # Display item details
                for key, value in item_details.items():
                    detail_frame = tk.Frame(details_frame, bg=COLOR_PANEL_BG)
                    detail_frame.pack(fill=tk.X, pady=5)
                    
                    key_label = tk.Label(detail_frame, text=f"{key}:", font=(FONT_FAMILY_PRIMARY, 11, "bold"), 
                                       fg=COLOR_PRIMARY, bg=COLOR_PANEL_BG, anchor="w")
                    key_label.pack(side=tk.LEFT, padx=(0, 10))
                    
                    value_label = tk.Label(detail_frame, text=str(value), font=(FONT_FAMILY_PRIMARY, 11), 
                                         fg=COLOR_TEXT_LIGHT, bg=COLOR_PANEL_BG, anchor="w")
                    value_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            else:
                # No details available
                no_details_label = tk.Label(details_frame, text="No additional details available for this item.", 
                                         font=(FONT_FAMILY_PRIMARY, 11), fg=COLOR_TEXT_MUTED_DARK_BG, 
                                         bg=COLOR_PANEL_BG, anchor="center")
                no_details_label.pack(pady=50)
            
            # Add back button to return to grid view
            back_btn = tk.Button(content_frame, text="← Back to Grid", 
                               bg=COLOR_SECONDARY, fg=COLOR_TEXT_LIGHT,
                               font=(FONT_FAMILY_PRIMARY, 11, "bold"), relief=tk.FLAT, bd=0,
                               activebackground=COLOR_PRIMARY, activeforeground=COLOR_TEXT_LIGHT,
                               padx=15, pady=8, command=self._return_to_grid_view)
            back_btn.pack(pady=(30, 20))
        
        def _get_item_details(self, item_name):
            """Get detailed information for a specific item from API data"""
            if not self.child_types_data:
                return {}
            
            # Search through the API data to find details for this item
            if isinstance(self.child_types_data, dict) and 'data' in self.child_types_data:
                for type1_item in self.child_types_data['data']:
                    levels = type1_item.get('levels', [])
                    details = self._search_item_details_in_levels(levels, item_name)
                    if details:
                        return details
            
            return {}
        
        def _search_item_details_in_levels(self, levels, target_name):
            """Recursively search for item details in levels"""
            for level in levels:
                level_name = level.get('name', '')
                level_id = level.get('id', '')
                
                # Check if this is the target level
                if level_name == target_name:
                    # Return all available details for this item
                    details = {}
                    for key, value in level.items():
                        if key not in ['children']:  # Exclude children from details
                            details[key] = value
                    return details
                
                # Recursively search in children
                children = level.get('children', [])
                if children:
                    details = self._search_item_details_in_levels(children, target_name)
                    if details:
                        return details
            
            return {}
        
        def _return_to_grid_view(self):
            """Return to the grid view from item detail view"""
            if hasattr(self, 'selected_node') and self.selected_node:
                # Display the grid for the previously selected node
                self._display_grid_items(self.selected_node)
                
                # Update breadcrumb
                self._update_breadcrumb_path(self.selected_node)
            else:
                # Fallback to default view
                self.refresh_tree()
        
        def _setup_initial_content(self):
            """Set up initial content display when the tree page is loaded"""
            # Display default content (Configuration level)
            if self.child_types_data and isinstance(self.child_types_data, dict) and 'data' in self.child_types_data:
                # Get the first type1 item's direct children
                first_type = self.child_types_data['data'][0] if self.child_types_data['data'] else None
                if first_type:
                    first_type_name = first_type.get('type1_name', 'Configuration')
                    # Get the direct children of the first type
                    direct_children = self._get_direct_children(first_type_name)
                    if direct_children:
                        # Display the direct children as cards
                        self._display_grid_items_from_list(direct_children, first_type_name)
                    else:
                        # Fallback to single item display
                        self._display_grid_items(first_type_name)
            else:
                # Fallback to project data
                self._display_project_tree()
            
            # Ensure ITSAR folder is always visible in the grid
            self._ensure_itsar_visibility()
        
        def _on_search_input(self, event):
            """Handle search input as user types"""
            search_term = self.search_var.get().strip()
            if search_term and search_term != "Search items...":
                # Filter content based on search term
                self._filter_content_by_search(search_term)
        
        def _on_search_submit(self, event):
            """Handle search submission (Enter key)"""
            search_term = self.search_var.get().strip()
            if search_term and search_term != "Search items...":
                # Perform search and display results
                self._perform_search(search_term)
        
        def _filter_content_by_search(self, search_term):
            """Filter the current content based on search term"""
            if not hasattr(self, 'selected_node') or not self.selected_node:
                return
            
            # Get current items and filter them
            current_items = self._get_direct_children(self.selected_node)
            if current_items:
                filtered_items = [item for item in current_items if search_term.lower() in item.lower()]
                if filtered_items:
                    self._display_grid_items_from_list(filtered_items, f"{self.selected_node} (Search: {search_term})")
                else:
                    # Show no results message
                    self._show_no_search_results(search_term)
        
        def _perform_search(self, search_term):
            """Perform a comprehensive search across all content"""
            # Search through all available data
            all_items = self._get_all_tree_items()
            if all_items:
                # Filter items by search term
                search_results = [item for item in all_items if search_term.lower() in item.lower()]
                if search_results:
                    # Display search results
                    self._display_grid_items_from_list(search_results, f"Search Results: {search_term}")
                else:
                    # Show no results message
                    self._show_no_search_results(search_term)
            else:
                # Show no results message
                self._show_no_search_results(search_term)
        
        def _show_no_search_results(self, search_term):
            """Display a message when no search results are found"""
            # Clear existing grid
            for widget in self.grid_frame.winfo_children():
                widget.destroy()
            
            # Create a simple message without background, icon, or back button
            message_label = tk.Label(self.grid_frame, 
                                   text=f"No items match your search.", 
                                   font=(FONT_FAMILY_PRIMARY, 12), 
                                   fg=COLOR_TEXT_MUTED_DARK_BG, 
                                   bg=COLOR_CONTENT_BG)
            message_label.pack(pady=20)
        
        def _ensure_itsar_visibility(self):
            """Ensure ITSAR folder is always visible in the grid"""
            print(f"DEBUG: Ensuring ITSAR visibility")
            
            # Check if ITSAR is already displayed in the grid
            itsar_visible = False
            for widget in self.grid_frame.winfo_children():
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Label) and hasattr(child, 'cget'):
                            try:
                                child_text = child.cget('text')
                                if child_text == "ITSAR" or (len(child_text) > 25 and child_text.startswith("ITSAR")):
                                    itsar_visible = True
                                    break
                            except:
                                pass
                    if itsar_visible:
                        break
            
            if not itsar_visible:
                print(f"DEBUG: ITSAR not visible, adding to grid")
                # Add ITSAR to the grid if it's not already there
                # This ensures the root folder is always accessible
                if not self.grid_frame.winfo_children():
                    # Grid is empty, populate with default folders
                    default_folders = ["ITSAR", "Test2", "Test3", "Test4", "Test5", "Test6", "Test7", "Test8"]
                    self._display_grid_items_from_list(default_folders, "Suites")
                else:
                    # Grid has content but no ITSAR, add it at the beginning
                    self._add_itsar_to_grid()
        
        def _add_itsar_to_grid(self):
            """Add ITSAR folder to the beginning of the grid"""
            print(f"DEBUG: Adding ITSAR to grid")
            
            # Get current grid items
            current_items = []
            for widget in self.grid_frame.winfo_children():
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Label) and hasattr(child, 'cget'):
                            try:
                                child_text = child.cget('text')
                                if child_text and child_text != "Search items...":
                                    # Remove ellipsis if present
                                    if child_text.endswith("..."):
                                        child_text = child_text[:-3]
                                    current_items.append(child_text)
                            except:
                                pass
            
            # Add ITSAR at the beginning if not already present
            if "ITSAR" not in current_items:
                current_items.insert(0, "ITSAR")
                # Redisplay the grid with ITSAR at the beginning
                self._display_grid_items_from_list(current_items, "Suites")
        
        def _return_to_previous_view(self):
            """Return to the previous view after search"""
            if hasattr(self, 'selected_node') and self.selected_node:
                # Display the grid for the previously selected node
                self._display_grid_items(self.selected_node)
                
                # Update breadcrumb
                self._update_breadcrumb_path(self.selected_node)
            else:
                # Fallback to default view
                self.refresh_tree()
        
        def _navigate_back(self):
            """Navigate back to the previous folder level"""
            if hasattr(self, 'navigation_history') and self.navigation_history:
                # Get the previous navigation state
                previous_state = self.navigation_history.pop()
                
                if previous_state['parent']:
                    # Navigate back to parent folder
                    print(f"DEBUG: Navigating back to parent: {previous_state['parent']}")
                    
                    # Update selected node
                    self.selected_node = previous_state['parent']
                    
                    # Get parent's children to display
                    parent_children = self._get_direct_children(previous_state['parent'])
                    if parent_children:
                        self._display_grid_items_from_list(parent_children, previous_state['parent'])
                    else:
                        self._display_grid_items(previous_state['parent'])
                    
                    # Update breadcrumb
                    self._update_breadcrumb_path(previous_state['parent'])
                    
                    # Also update the tree to show the parent node
                    self._expand_tree_node(previous_state['parent'])
                    
                else:
                    # Navigate back to root level
                    print(f"DEBUG: Navigating back to root level")
                    self._navigate_to_root()
                
                # Update back button visibility
                self._update_back_button_visibility()
            else:
                # No history, go back to root
                self._navigate_to_root()
        
        def _navigate_to_root(self):
            """Navigate back to the root level (Configuration)"""
            print(f"DEBUG: Navigating to root level")
            
            # Reset to root level
            self.selected_node = None
            
            # Display root level content
            self._setup_initial_content()
            
            # Update breadcrumb
            self._update_breadcrumb_path(None)
            
            # Hide back button
            self._update_back_button_visibility()
            
            # Ensure ITSAR is visible in the grid
            self._ensure_itsar_visibility()
        
        def _update_back_button_visibility(self):
            """Update back button visibility based on navigation state"""
            if hasattr(self, 'back_btn'):
                if hasattr(self, 'navigation_history') and self.navigation_history:
                    # Show back button if we have navigation history
                    self.back_btn.pack(side=tk.RIGHT, padx=(0, 10))
                else:
                    # Hide back button if we're at root level
                    self.back_btn.pack_forget()
        
        def _restore_selection(self, node_name):
            """Restore a previous selection after refresh"""
            try:
                # Try to find and select the node in the tree
                if self._find_and_select_node_in_tree(node_name):
                    # Display the content for this node
                    self._display_grid_items(node_name)
                    # Update breadcrumb
                    self._update_breadcrumb_path(node_name)
                    print(f"DEBUG: Restored selection to: {node_name}")
                else:
                    print(f"DEBUG: Could not restore selection to: {node_name}")
            except Exception as e:
                print(f"DEBUG: Error restoring selection: {e}")
        
        def _find_and_select_node_in_tree(self, target_name):
            """Find and select a specific node in the tree"""
            # This is a simplified implementation - you can enhance it based on your needs
            # For now, just try to display the content for the target node
            try:
                # Check if the node exists in the current data
                if self._get_direct_children(target_name):
                    return True
                else:
                    # Try to get items for this node
                    items = self._get_items_for_node(target_name)
                    if items:
                        return True
                    return False
            except Exception as e:
                print(f"DEBUG: Error finding node: {e}")
                return False
        
        def _on_folder_card_double_click(self, item_name):
            """Handle double-click on folder card - expand in tree and show children"""
            print(f"Folder card double-clicked: {item_name}")
            
            # Find and expand this node in the tree
            self._expand_node_in_tree(item_name)
            
            # Display the children of this folder
            self._display_grid_items(item_name)
            
            # Update breadcrumb to show the full path
            self._update_breadcrumb_path(item_name)
            self.selected_node = item_name
        
        def _expand_node_in_tree(self, node_name):
            """Expand a specific node in the tree view"""
            print(f"Expanding node in tree: {node_name}")
            
            # Find the node in the tree and expand it
            # This will search through the tree structure and expand the matching node
            self._find_and_expand_node(self.tree_frame, node_name)
        
        def _find_and_expand_node(self, parent_frame, target_name):
            """Recursively find and expand a node in the tree"""
            for child in parent_frame.winfo_children():
                # Check if this child is a frame with a name label
                if isinstance(child, tk.Frame):
                    # Look for name labels in this frame
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, tk.Label) and hasattr(grandchild, 'cget'):
                            try:
                                label_text = grandchild.cget('text')
                                if label_text == target_name:
                                    print(f"Found node '{target_name}' in tree, expanding...")
                                    # Find the expandable node and expand it
                                    self._expand_node_by_name(target_name)
                                    return True
                            except:
                                pass
                    
                    # Recursively search in this frame
                    if self._find_and_expand_node(child, target_name):
                        return True
            
            return False
        
        def _expand_node_by_name(self, node_name):
            """Expand a node by name in the tree structure"""
            # This method will be called when we found the node
            print(f"Should expand node: {node_name}")
            # TODO: Implement actual tree expansion logic
        
        def _expand_folder_in_tree(self, folder_name):
            """Expand a folder in the tree view to show its children"""
            print(f"DEBUG: Expanding folder in tree: {folder_name}")
            
            # Find the folder in the tree and expand it
            if self._find_and_expand_folder(self.tree_frame, folder_name):
                print(f"DEBUG: Successfully expanded folder: {folder_name}")
            else:
                print(f"DEBUG: Could not find folder to expand: {folder_name}")
        
        def _find_and_expand_folder(self, parent_frame, target_name):
            """Recursively find and expand a folder in the tree"""
            for child in parent_frame.winfo_children():
                if isinstance(child, tk.Frame):
                    # Look for the folder name in this frame
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, tk.Label) and hasattr(grandchild, 'cget'):
                            try:
                                label_text = grandchild.cget('text')
                                if label_text == target_name:
                                    print(f"DEBUG: Found folder '{target_name}' in tree")
                                    # Check if this is an expandable node
                                    if hasattr(child, 'expandable') and child.expandable:
                                        # Expand the node
                                        self._expand_tree_node(child)
                                        return True
                            except:
                                pass
                    
                    # Recursively search in this frame
                    if self._find_and_expand_folder(child, target_name):
                        return True
            
            return False
        
        def _expand_tree_node_by_name(self, node_name):
            """Expand a specific node in the tree view by its name"""
            print(f"DEBUG: Expanding tree node by name: {node_name}")
            
            # Update selected node
            self.selected_node = node_name
            
            # Find and expand the corresponding tree node
            print(f"DEBUG: Starting tree search for node: {node_name}")
            found = self._find_and_expand_tree_node(node_name)
            if found:
                print(f"DEBUG: Successfully expanded tree node: {node_name}")
                # Highlight the expanded node
                self._highlight_tree_node(node_name)
                # Scroll the tree to make the selected node visible
                self._scroll_tree_to_node(node_name)
            else:
                print(f"DEBUG: Failed to find or expand tree node: {node_name}")
        
        def _expand_tree_node(self, node_frame):
            """Expand a specific tree node widget to show its children"""
            print(f"DEBUG: Expanding tree node widget")
            
            # Find the expand/collapse icon and change it to expanded state
            for child in node_frame.winfo_children():
                if isinstance(child, tk.Label) and child.cget('text') in ['▶', '▼']:
                    # Change icon to expanded state
                    child.config(text='▼')
                    print(f"DEBUG: Changed icon to expanded state")
                    break
            
            # Mark as expanded
            if hasattr(node_frame, 'expanded'):
                node_frame.expanded = True
                print(f"DEBUG: Node marked as expanded")
            
            # Show the children in the tree
            self._show_children_in_tree(node_frame)
        
        def _show_children_in_tree(self, parent_frame):
            """Show the children of a node in the tree view"""
            print(f"DEBUG: Showing children in tree for node")
            
            # Get the node name from the parent frame
            node_name = None
            for child in parent_frame.winfo_children():
                if isinstance(child, tk.Label) and not child.cget('text') in ['▶', '▼']:
                    node_name = child.cget('text')
                    break
            
            if node_name:
                print(f"DEBUG: Found node name: {node_name}")
                # Get the children data for this node
                children = self._get_direct_children(node_name)
                if children:
                    print(f"DEBUG: Adding {len(children)} children to tree")
                    # Add children to the tree view
                    self._add_children_to_tree(parent_frame, children)
        
        def _add_children_to_tree(self, parent_frame, children):
            """Add children nodes to the tree view"""
            # Create a container for children
            children_container = tk.Frame(parent_frame, bg=COLOR_SIDEBAR_BG)
            children_container.pack(fill=tk.X, padx=(20, 0))  # Indent children
            
            for child_name in children:
                # Create child node frame
                child_frame = tk.Frame(children_container, bg=COLOR_SIDEBAR_BG)
                child_frame.pack(fill=tk.X, pady=1)
                
                # Check if this child has its own children
                child_children = self._get_direct_children(child_name)
                has_children = len(child_children) > 0
                
                # Create expand/collapse icon
                icon_text = "▶" if has_children else "  "  # Space if no children
                icon_label = tk.Label(child_frame, text=icon_text, font=("Arial", 8), 
                                    fg=COLOR_TEXT_LIGHT, bg=COLOR_SIDEBAR_BG)
                icon_label.pack(side=tk.LEFT, padx=(0, 3))
                
                # Create child name label
                name_label = tk.Label(child_frame, text=child_name, font=("Arial", 9), 
                                    fg=COLOR_TEXT_LIGHT, bg=COLOR_SIDEBAR_BG, anchor="w")
                name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                # Add click handlers
                if has_children:
                    # This is a folder, bind to folder click
                    child_frame.bind("<Button-1>", lambda e, n=child_name: self._on_folder_click(n))
                    icon_label.bind("<Button-1>", lambda e, n=child_name: self._on_folder_click(n))
                    name_label.bind("<Button-1>", lambda e, n=child_name: self._on_folder_click(n))
                else:
                    # This is a leaf node, bind to item click
                    child_frame.bind("<Button-1>", lambda e, n=child_name: self._on_item_click(n))
                    name_label.bind("<Button-1>", lambda e, n=child_name: self._on_item_click(n))
                
                # Store reference to children container
                parent_frame.children_container = children_container
        
        def _display_full_tree(self, tree_data):
            """Display the complete tree structure from API response"""
            try:
                # Clear any existing content
                for widget in self.tree_frame.winfo_children():
                    widget.destroy()
                
                # Display the full tree structure
                self._render_tree_node(tree_data, level=0, parent_frame=self.tree_frame)
                
            except Exception as e:
                print(f"Error displaying full tree: {e}")
                # Fallback to simple display
                self._display_simple_tree(tree_data)
        
        def _render_tree_node(self, node_data, level=0, parent_frame=None):
            """Recursively render tree nodes"""
            if parent_frame is None:
                parent_frame = self.tree_frame
            
            # Handle different data types
            if isinstance(node_data, dict):
                # Render dictionary as node
                self._render_dict_node(node_data, level, parent_frame)
            elif isinstance(node_data, list):
                # Render list items
                for item in node_data:
                    self._render_tree_node(item, level, parent_frame)
            elif isinstance(node_data, (str, int, float, bool)):
                # Render primitive values
                self._render_primitive_node(node_data, level, parent_frame)
            else:
                # Render unknown types as string
                self._render_primitive_node(str(node_data), level, parent_frame)
        
        def _render_dict_node(self, node_data, level, parent_frame):
            """Render a dictionary node"""
            # Create node frame
            node_frame = tk.Frame(parent_frame, bg=COLOR_PANEL_BG, relief=tk.FLAT, bd=0)
            node_frame.pack(fill=tk.X, padx=10 + (level * 20), pady=1)
            
            # Node header with key-value pairs
            header_frame = tk.Frame(node_frame, bg=COLOR_PANEL_BG)
            header_frame.pack(fill=tk.X)
            
            # Add expand/collapse functionality for complex nodes
            has_children = any(isinstance(v, (dict, list)) for v in node_data.values())
            
            if has_children:
                # Create expandable node
                expand_btn = tk.Label(header_frame, text="▶", font=("Arial", 8), 
                                    fg=COLOR_TEXT_LIGHT, bg=COLOR_PANEL_BG, cursor="hand2")
                expand_btn.pack(side=tk.LEFT, padx=(0, 5))
                
                # Node content frame (initially hidden)
                content_frame = tk.Frame(node_frame, bg=COLOR_PANEL_BG)
                
                # Toggle function
                def toggle_node():
                    if content_frame.winfo_children():
                        for child in content_frame.winfo_children():
                            child.pack_forget()
                        expand_btn.config(text="▶")
                    else:
                        for key, value in node_data.items():
                            if isinstance(value, (dict, list)):
                                # Create child node
                                child_frame = tk.Frame(content_frame, bg=COLOR_PANEL_BG)
                                child_frame.pack(fill=tk.X, padx=10, pady=1)
                                
                                # Child key label
                                key_label = tk.Label(child_frame, text=f"📋 {key}:", 
                                                   font=("Arial", 9, "bold"), 
                                                   fg=COLOR_TEXT_LIGHT, bg=COLOR_PANEL_BG, anchor="w")
                                key_label.pack(side=tk.LEFT)
                                
                                # Render child value
                                self._render_tree_node(value, level + 1, child_frame)
                        expand_btn.config(text="▼")
                
                expand_btn.bind("<Button-1>", lambda e: toggle_node())
                
                # Show key-value pairs that are not complex
                for key, value in node_data.items():
                    if not isinstance(value, (dict, list)):
                        key_value_frame = tk.Frame(header_frame, bg=COLOR_PANEL_BG)
                        key_value_frame.pack(fill=tk.X, padx=20, pady=1)
                        
                        key_label = tk.Label(key_value_frame, text=f"🔑 {key}:", 
                                           font=("Arial", 9), fg=COLOR_PRIMARY, 
                                           bg=COLOR_PANEL_BG, anchor="w")
                        key_label.pack(side=tk.LEFT)
                        
                        value_label = tk.Label(key_value_frame, text=str(value), 
                                             font=("Arial", 9), fg=COLOR_TEXT_SECONDARY_TABLE, 
                                             bg=COLOR_PANEL_BG, anchor="w")
                        value_label.pack(side=tk.LEFT, padx=(5, 0))
                
                content_frame.pack(fill=tk.X, padx=20)
                
            else:
                # Simple node without children
                for key, value in node_data.items():
                    key_value_frame = tk.Frame(header_frame, bg=COLOR_PANEL_BG)
                    key_value_frame.pack(fill=tk.X, padx=5, pady=1)
                    
                    key_label = tk.Label(key_value_frame, text=f"🔑 {key}:", 
                                       font=("Arial", 9), fg=COLOR_PRIMARY, 
                                       bg=COLOR_PANEL_BG, anchor="w")
                    key_label.pack(side=tk.LEFT)
                    
                    value_label = tk.Label(key_value_frame, text=str(value), 
                                         font=("Arial", 9), fg=COLOR_TEXT_SECONDARY_TABLE, 
                                         bg=COLOR_PANEL_BG, anchor="w")
                    value_label.pack(side=tk.LEFT, padx=(5, 0))
        
        def _render_primitive_node(self, value, level, parent_frame):
            """Render primitive values (string, int, float, bool)"""
            node_frame = tk.Frame(parent_frame, bg=COLOR_PANEL_BG, relief=tk.FLAT, bd=0)
            node_frame.pack(fill=tk.X, padx=10 + (level * 20), pady=1)
            
            # Determine icon based on value type
            if isinstance(value, bool):
                icon = "✅" if value else "❌"
                color = "#2ecc71" if value else "#e74c3c"
            elif isinstance(value, (int, float)):
                icon = "🔢"
                color = "#f39c12"
            elif isinstance(value, str):
                icon = "📝"
                color = COLOR_TEXT_SECONDARY_TABLE
            else:
                icon = "📄"
                color = COLOR_TEXT_SECONDARY_TABLE
            
            value_label = tk.Label(node_frame, text=f"{icon} {value}", 
                                 font=("Arial", 9), fg=color, 
                                 bg=COLOR_PANEL_BG, anchor="w")
            value_label.pack(side=tk.LEFT)
        
        def _display_simple_tree(self, tree_data):
            """Fallback simple tree display"""
            # Clear existing content
            for widget in self.tree_frame.winfo_children():
                widget.destroy()
            
            # Create root node
            root_frame = self._create_node_frame("📊 API Response Tree", is_root=True)
            root_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Display as JSON-like structure
            json_text = json.dumps(tree_data, indent=2)
            text_widget = tk.Text(self.tree_frame, bg=COLOR_PANEL_BG, fg=COLOR_TEXT_LIGHT,
                                font=("Consolas", 9), wrap=tk.WORD, height=20)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            text_widget.insert(tk.END, json_text)
            text_widget.config(state=tk.DISABLED)
        
        def _display_project_tree(self):
            """Display the original project tree structure"""
            # Root node
            root_frame = self._create_node_frame("📁 Projects", is_root=True)
            root_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Add projects
            for project in self.agent_data.get("data", []):
                project_name = project.get("project_name", "Unknown Project")
                project_id = project.get("project_id")
                project_status = project.get("progress", "Unknown")
                
                # Create project node
                project_frame = self._create_node_frame(f"📋 {project_name}", level=1)
                project_frame.pack(fill=tk.X, padx=20, pady=2)
                
                # Project details
                details_frame = tk.Frame(project_frame, bg=COLOR_PANEL_BG)
                details_frame.pack(fill=tk.X, padx=30, pady=2)
                
                # Status indicator
                status_color = self._get_status_color(project_status)
                status_label = tk.Label(details_frame, text=f"Status: {project_status}", 
                                      font=("Arial", 9), fg=status_color, bg=COLOR_PANEL_BG)
                status_label.pack(side=tk.LEFT)
                
                # Progress info
                subtypes = project.get("subtypes_status", [])
                total_tasks = len(subtypes)
                completed_tasks = sum(1 for s in subtypes if s.get("status", "").strip().lower() in ("done", "completed"))
                progress_text = f"Progress: {completed_tasks}/{total_tasks} tasks completed"
                progress_label = tk.Label(details_frame, text=progress_text, 
                                        font=("Arial", 9), fg=COLOR_TEXT_MUTED_DARK_BG, 
                                        bg=COLOR_PANEL_BG)
                progress_label.pack(side=tk.RIGHT)
                
                # Add test cases/tasks
                for subtype in subtypes:
                    task_name = subtype.get("type", "Unnamed Task")
                    task_status = subtype.get("status", "Unknown")
                    task_id = subtype.get("id")
                    
                    # Create task node
                    task_frame = self._create_node_frame(f"⚡ {task_name}", level=2)
                    task_frame.pack(fill=tk.X, padx=40, pady=1)
                    
                    # Task details
                    task_details_frame = tk.Frame(task_frame, bg=COLOR_PANEL_BG)
                    task_details_frame.pack(fill=tk.X, padx=50, pady=1)
                    
                    task_status_color = self._get_status_color(task_status)
                    task_status_label = tk.Label(task_details_frame, text=f"Status: {task_status}", 
                                               font=("Arial", 8), fg=task_status_color, 
                                               bg=COLOR_PANEL_BG)
                    task_status_label.pack(side=tk.LEFT)
                    
                    # Add click handler for task
                    task_frame.bind("<Button-1>", lambda e, p=project_name, t=task_name, 
                                  pid=project_id, tid=task_id: self._on_task_click(p, t, pid, tid))
                    for child in task_frame.winfo_children():
                        child.bind("<Button-1>", lambda e, p=project_name, t=task_name, 
                                 pid=project_id, tid=task_id: self._on_task_click(p, t, pid, tid))
            
            # Add projects
            for project in self.agent_data.get("data", []):
                project_name = project.get("project_name", "Unknown Project")
                project_id = project.get("project_id")
                project_status = project.get("progress", "Unknown")
                
                # Create project node
                project_frame = self._create_node_frame(f"📋 {project_name}", level=1)
                project_frame.pack(fill=tk.X, padx=20, pady=2)
                
                # Project details
                details_frame = tk.Frame(project_frame, bg=COLOR_PANEL_BG)
                details_frame.pack(fill=tk.X, padx=30, pady=2)
                
                # Status indicator
                status_color = self._get_status_color(project_status)
                status_label = tk.Label(details_frame, text=f"Status: {project_status}", 
                                      font=("Arial", 9), fg=status_color, bg=COLOR_PANEL_BG)
                status_label.pack(side=tk.LEFT)
                
                # Progress info
                subtypes = project.get("subtypes_status", [])
                total_tasks = len(subtypes)
                completed_tasks = sum(1 for s in subtypes if s.get("status", "").strip().lower() in ("done", "completed"))
                progress_text = f"Progress: {completed_tasks}/{total_tasks} tasks completed"
                progress_label = tk.Label(details_frame, text=progress_text, 
                                        font=("Arial", 9), fg=COLOR_TEXT_MUTED_DARK_BG, 
                                        bg=COLOR_PANEL_BG)
                progress_label.pack(side=tk.RIGHT)
                
                # Add test cases/tasks
                for subtype in subtypes:
                    task_name = subtype.get("type", "Unnamed Task")
                    task_status = subtype.get("status", "Unknown")
                    task_id = subtype.get("id")
                    
                    # Create task node
                    task_frame = self._create_node_frame(f"⚡ {task_name}", level=2)
                    task_frame.pack(fill=tk.X, padx=40, pady=1)
                    
                    # Task details
                    task_details_frame = tk.Frame(task_frame, bg=COLOR_PANEL_BG)
                    task_details_frame.pack(fill=tk.X, padx=50, pady=1)
                    
                    task_status_color = self._get_status_color(task_status)
                    task_status_label = tk.Label(task_details_frame, text=f"Status: {task_status}", 
                                               font=("Arial", 8), fg=task_status_color, 
                                               bg=COLOR_PANEL_BG)
                    task_status_label.pack(side=tk.LEFT)
                    
                    # Add click handler for task
                    task_frame.bind("<Button-1>", lambda e, p=project_name, t=task_name, 
                                  pid=project_id, tid=task_id: self._on_task_click(p, t, pid, tid))
                    for child in task_frame.winfo_children():
                        child.bind("<Button-1>", lambda e, p=project_name, t=task_name, 
                                 pid=project_id, tid=task_id: self._on_task_click(p, t, pid, tid))
        
        def _create_node_frame(self, text, level=0, is_root=False):
            frame = tk.Frame(self.tree_frame, bg=COLOR_PANEL_BG, relief=tk.FLAT, bd=0)
            
            # Icon and text
            icon_label = tk.Label(frame, text=text, font=("Arial", 10 if is_root else 9), 
                                fg=COLOR_TEXT_LIGHT if is_root else COLOR_TEXT_SECONDARY_TABLE, 
                                bg=COLOR_PANEL_BG, anchor="w")
            icon_label.pack(side=tk.LEFT, padx=5, pady=3)
            
            # Hover effect
            def on_enter(e):
                if not is_root:
                    frame.config(bg=COLOR_HOVER_BG)
                    icon_label.config(bg=COLOR_HOVER_BG)
            
            def on_leave(e):
                if not is_root:
                    frame.config(bg=COLOR_PANEL_BG)
                    icon_label.config(bg=COLOR_PANEL_BG)
            
            if not is_root:
                frame.bind("<Enter>", on_enter)
                frame.bind("<Leave>", on_leave)
                icon_label.bind("<Enter>", on_enter)
                icon_label.bind("<Leave>", on_leave)
            
            return frame
        
        def _get_status_color(self, status):
            status_lower = status.strip().lower()
            if status_lower in ("done", "completed"):
                return "#2ecc71"  # Green
            elif status_lower in ("in progress", "progress"):
                return "#f1c40f"  # Yellow
            elif status_lower in ("to-do", "todo", "pending", "not yet started"):
                return "#3498db"  # Blue
            else:
                return COLOR_TEXT_MUTED_DARK_BG
        
        def _on_task_click(self, project_name, task_name, project_id, task_id):
            # Handle task click - could open details or switch to test cases page
            print(f"Clicked task: {task_name} in project: {project_name}")
            # You can implement navigation to test cases page here
            # self.switch_page_callback("TestCases")
        
        def update_agent_data(self, new_agent_data):
            self.agent_data = new_agent_data
            # Update token if provided in new data
            if new_agent_data.get("token"):
                self.token = new_agent_data.get("token")
            self.refresh_tree()
        
        def tkraise(self, aboveThis=None):
            super().tkraise(aboveThis)
            # Refresh tree when page is shown
            self.refresh_tree()

    # ============================================
    # End of NEW TreePage Class
    # ============================================


    # --- REVISED TestCasesPage (Dark Theme) ---
    class TestCasesPage(tk.Frame):
        def __init__(self, parent, switch_page_callback, base_url, pages,token=None, *args, **kwargs):
            super().__init__(parent, bg=COLOR_CONTENT_BG, *args, **kwargs)
            self.switch_page_callback = switch_page_callback
            self.pages = pages
            self.base_url = base_url 
            self.project_name = ""
            self.task_widgets = {}
            self.column_content_frames = {}
            self.column_id_map = {}
            self.token = token

            # Top Frame uses Dark BG
            top_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
            top_frame.pack(fill=tk.X, padx=5, pady=(10, 5))

            # Back Button (moved to left, styled same as DownloadPage)
            back_btn = tk.Button(
                top_frame, text="← Back",  # Same style and arrow like DownloadPage
                command=lambda: switch_page_callback("Project"),
                bg=COLOR_PANEL_BG, fg=COLOR_TEXT_LIGHT,
                font=("Segoe UI", 10, "bold"),
                relief=tk.FLAT, bd=0, padx=10, pady=5,
                activebackground=COLOR_PRIMARY,
                activeforeground=COLOR_TEXT_LIGHT,
            )
            back_btn.pack(anchor="w", padx=5, pady=(20, 10))


            # Title Label: Dark BG, Light Text
            # self.title_label = tk.Label(top_frame, text="", font=("Arial", 16, "bold"), bg=COLOR_CONTENT_BG, fg=COLOR_TEXT_LIGHT)
            # self.title_label.pack(side=tk.LEFT, pady=5, padx=(5, 10))

            # Kanban Columns Container: Dark BG
            columns_container = tk.Frame(self, bg=COLOR_CONTENT_BG)
            columns_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
            columns_container.grid_columnconfigure(0, weight=1, uniform="kanban_col")
            columns_container.grid_columnconfigure(1, weight=1, uniform="kanban_col")
            columns_container.grid_columnconfigure(2, weight=1, uniform="kanban_col")
            columns_container.grid_rowconfigure(0, weight=1)

            # Create columns with dark theme header backgrounds
            self._create_kanban_column(columns_container, "To Do", 0, "todo", KANBAN_HEADER_TODO_BG)
            self._create_kanban_column(columns_container, "In Progress", 1, "inprogress", KANBAN_HEADER_INPROGRESS_BG)
            self._create_kanban_column(columns_container, "Completed", 2, "completed", KANBAN_HEADER_COMPLETED_BG)

            self.drag_data = {"widget": None, "text": None, "source_column_frame": None}

        def _create_kanban_column(self, parent, title, col_index, column_key, header_bg_color):
            # Column Outer Frame: Dark Content BG
            column_outer_frame = tk.Frame(parent, bg=COLOR_CONTENT_BG)
            column_outer_frame.grid(row=0, column=col_index, sticky="nsew", padx=5, pady=0)
            column_outer_frame.grid_rowconfigure(1, weight=1)
            column_outer_frame.grid_columnconfigure(0, weight=1)

            # Header uses specific Dark BG color, Light Text
            header = tk.Label(column_outer_frame, text=title, bg=header_bg_color, fg=KANBAN_TEXT_HEADER, font=KANBAN_FONT_HEADER, anchor='w', padx=10, pady=8)
            header.grid(row=0, column=0, sticky="ew")

            # Content Frame uses Dark Kanban Column BG
            content_frame = tk.Frame(column_outer_frame, bg=KANBAN_COLUMN_BG, bd=0, relief="flat")
            content_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 0))
            content_frame.grid_columnconfigure(0, weight=1)
            self.column_content_frames[column_key] = content_frame
            self.column_id_map[content_frame] = column_key
            content_frame.original_bg = content_frame.cget("bg") # Store original dark bg
            content_frame.bind("<Enter>", self.on_column_content_enter)
            content_frame.bind("<Leave>", self.on_column_content_leave)

        def _create_task_widget(self, parent_column_frame, task_text):
            print(f"DEBUG: Creating task widget for: {task_text}")
            if not parent_column_frame or not parent_column_frame.winfo_exists():
                print(f"DEBUG: Parent frame doesn't exist for task: {task_text}")
                return None
                
            if task_text in self.task_widgets and self.task_widgets[task_text].winfo_exists():
                print(f"DEBUG: Task widget already exists for: {task_text}")
                return self.task_widgets[task_text]

            # Task Frame: Dark Task BG, Dark Task Border
            task_frame = tk.Frame(parent_column_frame, bg=KANBAN_TASK_BG, highlightbackground=KANBAN_TASK_BORDER, highlightcolor=KANBAN_TASK_BORDER, highlightthickness=1, bd=0)
            task_frame.pack(fill=tk.X, padx=8, pady=(8, 0))
            # Task Label: Dark Task BG, Light Task Text
            task_label = tk.Label(task_frame, text=task_text, bg=KANBAN_TASK_BG, fg=KANBAN_TEXT_TASK, font=KANBAN_FONT_TASK, anchor="w", justify="left", padx=10, pady=6)
            task_label.pack(fill=tk.X)

            scan_endpoint = "api/scan/create"  # Define the endpoint here
            
            # Single click handler
            task_label.bind("<Button-1>", lambda e, text=task_text, ep=scan_endpoint: self._on_task_click(text, scan_endpoint=ep, token=self.token))
            
            # Double click handler for security report generation
            def handle_double_click(e, text=task_text):
                print(f"DEBUG: Double-click event triggered for task: {text}")
                self._on_task_double_click(text)
            
            task_label.bind("<Double-Button-1>", handle_double_click)

            for widget in (task_frame, task_label):
                # widget.bind("<ButtonPress-1>", self.on_start_drag)
                # widget.bind("<B1-Motion>", self.on_drag)
                # widget.bind("<ButtonRelease-1>", self.on_drop)
                widget.bind("<Enter>", self.on_task_enter)
                widget.bind("<Leave>", self.on_task_leave)
                # Add double-click to the frame as well
                if widget != task_label:
                    def handle_frame_double_click(e, text=task_text):
                        print(f"DEBUG: Frame double-click event triggered for task: {text}")
                        self._on_task_double_click(text)
                    widget.bind("<Double-Button-1>", handle_frame_double_click)

            self.task_widgets[task_text] = task_frame
            task_frame.task_text = task_text
            task_frame.parent_column_frame = parent_column_frame
            return task_frame
            
        def _on_task_double_click(self, task_text):
            """Handle double-click event on a task to execute security report generator"""
            print(f"DEBUG: _on_task_double_click called with task_text: {task_text}")
            import subprocess
            import os
            from tkinter import messagebox
            
            try:
                # Try multiple possible locations for the security report generator
                possible_paths = [
                    # Standard installation path
                    "/usr/share/wingzai-agent/Report_Generator_Automation-main/security_report_generator.py",
                    # Development/relative path
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               "Report_Generator_Automation-main", "security_report_generator.py"),
                    # Alternative relative path
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               "../Report_Generator_Automation-main/security_report_generator.py"),
                ]
                
                script_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        script_path = os.path.abspath(path)
                        break
                
                if not script_path:
                    error_msg = """Security report generator not found in any of the expected locations.
                    
                    Tried the following paths:
                    - /usr/share/wingzai-agent/Report_Generator_Automation-main/security_report_generator.py
                    - <app_dir>/Report_Generator_Automation-main/security_report_generator.py
                    - <app_dir>/../Report_Generator_Automation-main/security_report_generator.py
                    
                    Please ensure the security report generator is properly installed.
                    """
                    print(f"ERROR: {error_msg}")
                    messagebox.showerror("Error", error_msg)
                    return
                
                print(f"DEBUG: Using script at: {script_path}")
                
                # Ensure the script is executable
                if not os.access(script_path, os.X_OK):
                    try:
                        os.chmod(script_path, 0o755)  # Make it executable
                        print(f"DEBUG: Made script executable: {script_path}")
                    except Exception as e:
                        print(f"WARNING: Could not make script executable: {e}")
                
                print(f"DEBUG: Looking up testcase_id for: {task_text}")
                print(f"DEBUG: Current subtype_id_map: {getattr(self, 'subtype_id_map', 'Not found')}")
                
                # Get the test case ID from the subtype_id_map
                testcase_id = getattr(self, 'subtype_id_map', {}).get(task_text)
                if not testcase_id:
                    error_msg = f"Could not find ID for test case: {task_text}"
                    print(f"ERROR: {error_msg}")
                    messagebox.showerror("Error", error_msg)
                    return
                
                # Prepare environment with Python path if needed
                env = os.environ.copy()
                script_dir = os.path.dirname(script_path)
                
                # Add script directory to PYTHONPATH if not already there
                python_path = env.get('PYTHONPATH', '')
                if script_dir not in python_path.split(os.pathsep):
                    env['PYTHONPATH'] = f"{script_dir}{os.pathsep}{python_path}" if python_path else script_dir
                
                # Prepare the command to run the script
                cmd = [
                    sys.executable,  # Use the same Python interpreter
                    script_path,
                    "--testcase", 
                    testcase_id,
                    "--debug"  # Add debug flag if supported by the script
                ]
                
                print(f"DEBUG: Running command: {' '.join(cmd)}")
                print(f"DEBUG: Working directory: {os.getcwd()}")
                print(f"DEBUG: PYTHONPATH: {env.get('PYTHONPATH', 'Not set')}")
                
                # Run the script in a non-blocking way
                try:
                    # Create a log file for the subprocess
                    log_dir = os.path.expanduser("~/.wingzai-agent/logs")
                    os.makedirs(log_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    log_file = os.path.join(log_dir, f"security_report_{timestamp}.log")
                    
                    with open(log_file, 'w') as f:
                        f.write(f"Command: {' '.join(cmd)}\n")
                        f.write(f"Timestamp: {datetime.now()}\n")
                        f.write("="*80 + "\n")
                    
                    # Start the process with output redirection to log file
                    with open(log_file, 'a') as log_fd:
                        process = subprocess.Popen(
                            cmd,
                            stdout=log_fd,
                            stderr=subprocess.STDOUT,
                            env=env,
                            cwd=os.path.dirname(script_path),  # Set working directory to script's directory
                            start_new_session=True
                        )
                    
                    message = (
                        f"Started security report generation for: {task_text}\n\n"
                        f"Log file: {log_file}"
                    )
                    messagebox.showinfo("Success", message)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to start security report generator: {str(e)}")
                    
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

        def _on_task_click(self, task_text, scan_endpoint, token=None):
            # Import required modules
            import tempfile
            import os
            import zipfile
            import shutil
            import time
            from tkinter import messagebox
            
            # Debug: Print test_cases_data structure
            print("\n[DEBUG] Task clicked:", task_text)
            print("[DEBUG] Current test_cases_data:", self.test_cases_data)
            print("[DEBUG] subtype_id_map:", self.subtype_id_map)
            
            # Find the task's status from test_cases_data
            task_status = None
            for status, tasks in self.test_cases_data.items():
                if task_text in tasks:
                    task_status = status.lower()
                    print(f"[DEBUG] Found task '{task_text}' with status: {status}")
                    break

            # Only proceed if task is in "todo" status
            if task_status != "todo":
                messagebox.showinfo("Info", "Only 'To Do' tasks can be accessed for automation and download.")
                return
            subtype_id = self.subtype_id_map.get(task_text)
            if not subtype_id or not self.project_id or not self.agent_id:
                return
            scan_url = f"{self.base_url.rstrip('/')}/{scan_endpoint.strip()}"

            try:
                # Get fresh token from configuration file to avoid stale token issues
                current_token = None
                try:
                    with open('client.conf.json', 'r') as f:
                        config = json.load(f)
                        current_token = config.get('token')
                except Exception as e:
                    print(f"Error reading token from config: {e}")
                    # Fallback to stored token if config read fails
                    current_token = self.token

                payload = {
                    "project_id": self.project_id,
                    "testcase_id": subtype_id,
                    "created_by": self.agent_id
                }
                headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {current_token}" if current_token else ""
                    }


                print("Fetching data from server...")

                response = requests.post(scan_url, json=payload, headers=headers)
                print("scan_response: ", response)
                if response.status_code == 200:
                    data = response.json()
                    print("scan_response: ", data)
                    
                    # Extract scan_id and repo_dir from response
                    scan_id = data.get('scan_id')
                    repo_dir = data.get('repo_dir')
                    print(f"[DEBUG] Extracted scan_id: {scan_id}")
                    print(f"[DEBUG] Extracted repo_dir: {repo_dir}")
                    
                    # Validate that we have the required data
                    if not scan_id or not repo_dir:
                        print(f"[WARNING] Missing scan_id or repo_dir in response. scan_id: {scan_id}, repo_dir: {repo_dir}")
                        print("[INFO] Will proceed with fallback values")
                    
                else:
                    messagebox.showerror("Server Error", f"Failed to fetch data. Status code: {response.status_code}")
                    return

            except Exception as e:
                messagebox.showerror("Network Error", f"Could not connect to server: {str(e)}")


            subtype_id = self.subtype_id_map.get(task_text)

            if not subtype_id or not self.project_id or not self.agent_id:
                print(f"[ERROR] Missing required IDs - subtype_id: {subtype_id}, project_id: {self.project_id}, agent_id: {self.agent_id}")
                return

            # Create a simple loading popup
            loading_window = tk.Toplevel(self.master, bg='#2c3e50')
            loading_window.title("Downloading...")
            loading_window.geometry("300x100")
            loading_window.resizable(False, False)
            
            # Center the window
            window_width = 300
            window_height = 100
            screen_width = loading_window.winfo_screenwidth()
            screen_height = loading_window.winfo_screenheight()
            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)
            loading_window.geometry(f'{window_width}x{window_height}+{x}+{y}')
            
            # Make it modal after the window is visible
            def set_grab():
                loading_window.grab_set()
            loading_window.after(100, set_grab)
            
            # Simple label
            tk.Label(loading_window, 
                    text="Downloading...", 
                    font=('Segoe UI', 12), 
                    bg='#2c3e50', 
                    fg='#ecf0f1').pack(expand=True)
            
            # Progress bar
            progress_bar = ttk.Progressbar(loading_window, 
                                         orient='horizontal', 
                                         length=100, 
                                         mode='determinate')
            progress_bar.pack(fill='x', padx=20, pady=10)
            
            # Status label (kept for functionality but hidden)
            status_label = tk.Label(loading_window, 
                                  text="", 
                                  font=('Segoe UI', 1), 
                                  bg='#2c3e50', 
                                  fg='#2c3e50')  # Same as background to hide
            status_label.pack()
            
            # Progress text (kept for functionality but hidden)
            progress_text = tk.Label(loading_window, 
                                   text="", 
                                   font=('Segoe UI', 1), 
                                   bg='#2c3e50', 
                                   fg='#2c3e50')  # Same as background to hide
            progress_text.pack()
            
            # Debug functions (kept for functionality but hidden)
            def update_debug_info(msg):
                print(f"[DEBUG] {msg}")
                loading_window.update()
                
            def update_debug_error(msg):
                print(f"[ERROR] {msg}")
                loading_window.update()
            
            # Add debug info
            update_debug_info(f"Starting download for test case: {subtype_id}")
            update_debug_info(f"Project ID: {self.project_id}")
            update_debug_info(f"Agent ID: {self.agent_id}")
            update_debug_info(f"Base URL: {self.base_url}")
            
            # Define paths - save in cwd/release/<testcase-id>/
            cwd = os.getcwd()
            release_dir = os.path.join(cwd, 'release')
            testcase_dir = os.path.join(release_dir, f"{subtype_id}")
            zip_path = os.path.join(release_dir, f"{subtype_id}.zip")
            
            # Look for execute.sh in the testcase directory
            automation_script = os.path.join(testcase_dir, "execute.sh")
            
            # If execute.sh exists, make it executable
            if os.path.exists(automation_script):
                try:
                    os.chmod(automation_script, 0o755)
                    update_debug_info(f"Found and made executable: {automation_script}")
                except Exception as e:
                    update_debug_error(f"Could not make script executable: {str(e)}")
            else:
                update_debug_info(f"execute.sh not found in {testcase_dir}")
            
            # Create release directory if it doesn't exist
            os.makedirs(release_dir, exist_ok=True)
            
            # Debug output for file locations
            update_debug_info(f"Release directory: {release_dir}")
            update_debug_info(f"ZIP file will be saved to: {zip_path}")
            update_debug_info(f"Files will be extracted to: {testcase_dir}")
            update_debug_info(f"Expected automation script: {automation_script}")
            
            # Check if already exists
            if os.path.exists(testcase_dir) and os.path.exists(automation_script):
                update_debug_info(f"Test case {subtype_id} already exists at {testcase_dir}")
                
                # Ask user if they want to redownload
                if messagebox.askyesno(
                    "Test Case Exists",
                    f"Test case already exists at:\n{testcase_dir}\n\n"
                    "Would you like to download it again?",
                    parent=loading_window
                ):
                    update_debug_info("User chose to redownload the test case")
                    try:
                        import shutil
                        shutil.rmtree(testcase_dir)
                        if os.path.exists(zip_path):
                            os.remove(zip_path)
                        update_debug_info(f"Removed existing test case at {testcase_dir}")
                    except Exception as e:
                        error_msg = f"Failed to remove existing test case: {str(e)}"
                        update_debug_error(error_msg)
                        messagebox.showerror("Error", error_msg, parent=loading_window)
                        loading_window.destroy()
                        return
                else:
                    update_debug_info("Using existing test case files")
                    # Skip to running the automation script
                    self.run_automation_script(automation_script, loading_window, status_label, progress_text, progress_bar, subtype_id, task_text, scan_id, repo_dir)
                    return

            try:
                # Get fresh token from configuration file
                current_token = None
                try:
                    with open('client.conf.json', 'r') as f:
                        config = json.load(f)
                        current_token = config.get('token')
                except Exception as e:
                    update_debug_error(f"Error reading token from config: {e}")
                    current_token = self.token

                # 1. Download the test case with progress tracking
                download_url = f"{self.base_url.rstrip('/')}/api/release/{subtype_id}"
                update_debug_info(f"Downloading from: {download_url}")
                update_debug_info(f"Saving to: {zip_path}")
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {current_token}" if current_token else ""
                }

                # Update UI with download progress
                status_label.config(text="Connecting to server...")
                progress_bar['value'] = 0
                loading_window.update()
                
                # Debug logging
                update_debug_info(f"Initiating download from: {download_url}")
                update_debug_info(f"Using token: {current_token[:15]}..." if current_token else "No token provided")

                try:
                    # Add timeout and stream the download
                    response = requests.get(
                        download_url,
                        headers=headers,
                        stream=True,
                        timeout=300  # 5 minutes timeout
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"Failed to download test case. Status code: {response.status_code}")

                    # Get total size for progress calculation
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    start_time = time.time()
                    
                    # Create temp directory
                    temp_dir = tempfile.mkdtemp()
                    zip_path = os.path.join(temp_dir, f"{subtype_id}.zip")
                    
                    # Save the downloaded zip file with progress updates
                    with open(zip_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if not chunk:  # Skip keep-alive chunks
                                continue
                                
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                    # Update progress every 1MB or when done
                    if downloaded % (1024 * 1024) == 0 or downloaded == total_size:
                        elapsed = time.time() - start_time
                        speed = (downloaded / (1024 * 1024)) / max(1, elapsed)  # MB/s
                        percent = (downloaded / max(1, total_size)) * 100
                        
                        # Update progress bar
                        progress_bar['value'] = percent
                        
                        # Update status text
                        status_text = "Downloading test case..."
                        if percent > 95:
                            status_text = "Finalizing download..."
                        
                        # Update UI elements
                        status_label.config(text=status_text)
                        progress_text.config(
                            text=f"{downloaded/(1024*1024):.1f}MB / {total_size/(1024*1024):.1f}MB • {percent:.1f}% • {speed:.1f} MB/s"
                        )
                        
                        # Debug logging
                        if downloaded % (5 * 1024 * 1024) == 0:  # Log every 5MB
                            update_debug_info(
                                f"Downloaded: {downloaded/(1024*1024):.1f}MB "
                                f"({percent:.1f}%) at {speed:.1f} MB/s"
                            )
                        
                        loading_window.update()  # Force UI update
            
                except requests.exceptions.Timeout:
                    raise Exception("Download timed out after 5 minutes")
                except requests.exceptions.RequestException as e:
                    raise Exception(f"Download failed: {str(e)}")
                
                # Update status for extraction
                status_label.config(text="Extracting files...")
                progress_text.config(text="Preparing extraction...")
                progress_bar['value'] = 0
                
                # Use the testcase_dir we already defined
                extract_dir = testcase_dir
                update_debug_info(f"Extracting to: {extract_dir}")
                
                # Create directory if it doesn't exist
                os.makedirs(extract_dir, exist_ok=True)
                update_debug_info(f"Using directory: {extract_dir}")
                loading_window.update()
                
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        file_list = zip_ref.namelist()
                        total_files = len(file_list)
                        update_debug_info(f"Found {total_files} files to extract")
                        
                        # Create a temporary directory for extraction
                        with tempfile.TemporaryDirectory() as temp_dir:
                            # Extract to temp directory first
                            zip_ref.extractall(temp_dir)
                            
                            # Move all files and directories from temp_dir to extract_dir
                            for item in os.listdir(temp_dir):
                                src = os.path.join(temp_dir, item)
                                
                                # If the item is a directory, move its contents directly to extract_dir
                                if os.path.isdir(src):
                                    for subitem in os.listdir(src):
                                        sub_src = os.path.join(src, subitem)
                                        sub_dst = os.path.join(extract_dir, subitem)
                                        if os.path.exists(sub_dst):
                                            if os.path.isdir(sub_dst):
                                                shutil.rmtree(sub_dst)
                                            else:
                                                os.remove(sub_dst)
                                        shutil.move(sub_src, extract_dir)
                                    # Remove the now-empty directory
                                    shutil.rmtree(src)
                                else:
                                    # For regular files, move them directly
                                    dst = os.path.join(extract_dir, item)
                                    if os.path.exists(dst):
                                        os.remove(dst)
                                    shutil.move(src, extract_dir)
                            
                            # Update progress
                            progress_bar['value'] = 100
                            progress_text.config(text="Files moved successfully")
                            loading_window.update()
                                    
                    update_debug_info("Extraction completed successfully")
                    
                except Exception as e:
                    update_debug_error(f"Extraction failed: {str(e)}")
                    raise
                
                # Run the automation script
                self.run_automation_script(automation_script, loading_window, status_label, progress_text, progress_bar, subtype_id, task_text, scan_id, repo_dir)
                
            except Exception as e:
                error_msg = f"Failed to process test case: {str(e)}"
                update_debug_error(error_msg)
                messagebox.showerror("Error", error_msg, parent=loading_window)
                loading_window.destroy()

        def run_automation_script(self, script_path, window, status_label, progress_text, progress_bar, subtype_id, task_text, scan_id=None, repo_dir=None):
            """Helper function to run the automation script using TerminalWindow"""
            def update_debug_info(msg):
                if hasattr(self, 'debug_text') and self.debug_text.winfo_exists():
                    self.debug_text.config(state='normal')
                    self.debug_text.insert('end', f"[DEBUG] {msg}\n")
                    self.debug_text.see('end')
                    self.debug_text.config(state='disabled')
                    window.update()
                print(f"[DEBUG] {msg}")
            
            def update_debug_error(msg):
                if hasattr(self, 'debug_text') and self.debug_text.winfo_exists():
                    self.debug_text.config(state='normal')
                    self.debug_text.insert('end', f"[ERROR] {msg}\n", 'error')
                    self.debug_text.tag_configure('error', foreground='#e74c3c')
                    self.debug_text.see('end')
                    self.debug_text.config(state='disabled')
                    window.update()
                print(f"[ERROR] {msg}")
                
            try:
                # Check if script exists
                if not os.path.exists(script_path):
                    error_msg = f"execute.sh not found at {script_path}"
                    update_debug_error(error_msg)
                    messagebox.showerror("Script Not Found", error_msg, parent=window)
                    return False
                
                # Make sure the script is executable
                try:
                    os.chmod(script_path, 0o755)
                    update_debug_info(f"Made script executable: {script_path}")
                except Exception as e:
                    update_debug_error(f"Could not make script executable: {str(e)}")
                
                # Get the directory containing the script
                script_dir = os.path.dirname(script_path)
                
                # Get current working directory and create result directory structure
                cwd = os.getcwd()
                project_name = self.project_name.replace(" ", "_")
                test_case_name = task_text.replace(" ", "_")
                # Use the scan_id from response if available, otherwise fall back to subtype_id
                actual_scan_id = scan_id if scan_id else subtype_id
                # Use the repo_dir from response if available, otherwise fall back to script directory
                actual_repo_dir = repo_dir if repo_dir else os.path.dirname(script_dir)
                # Construct result path as cwd + /tmp/project_name/testcase_name/scan_id/
                result_dir = os.path.join(cwd, "tmp", project_name, test_case_name, actual_scan_id)
                os.makedirs(result_dir, exist_ok=True, mode=0o755)  # 0o755 in octal
                
                update_debug_info(f"Results will be saved to: {result_dir}")
                update_debug_info(f"Launching terminal for script: {script_path}")
                update_debug_info(f"Using scan_id from response: {actual_scan_id}")
                update_debug_info(f"Using repo_dir from response: {actual_repo_dir}")
                
                # Use terminal_window.py for execution
                try:
                    from terminal_window import run_terminal_app
                    
                    # Create result directory if it doesn't exist
                    os.makedirs(result_dir, exist_ok=True, mode=0o755)
                    
                    # Run the terminal app
                    run_terminal_app(
                        scan_id=actual_scan_id,
                        repo_dir=actual_repo_dir,
                        base_url=self.base_url,
                        folder_path=script_dir,
                        result_path=result_dir,
                        agent_name="Automation Agent",
                        on_terminal_close=lambda: update_debug_info("Terminal closed"),
                        token=self.token
                    )
                    save_scan_repo_mapping(actual_scan_id, actual_repo_dir)
                    
                    update_debug_info("Automation script execution completed")
                    window.after(500, window.destroy)
                    return True
                    
                except Exception as e:
                    update_debug_error(f"Failed to start terminal: {str(e)}")
                    window.after(500, window.destroy)
                    return False
                
            except Exception as e:
                error_msg = f"Error in run_automation_script: {str(e)}"
                print(f"[ERROR] {error_msg}")
                update_debug_error(error_msg)
                messagebox.showerror("Script Error", error_msg, parent=window)
                window.after(500, window.destroy)
                return False
                
        def load_project(self, project_name, test_cases_data, project_id=None, subtype_id_map=None, agent_id=None):
            print(f"\n[DEBUG] Loading project: {project_name}")
            print(f"[DEBUG] Project ID: {project_id}, Agent ID: {agent_id}")
            print(f"[DEBUG] Initial test_cases_data: {test_cases_data}")
            print(f"[DEBUG] Initial subtype_id_map: {subtype_id_map}")
            
            self.project_name = project_name
            self.test_cases_data = test_cases_data
            self.project_id = project_id
            self.agent_id = agent_id
            self.subtype_id_map = subtype_id_map or {}
            
            print(f"[DEBUG] Current test_cases_data: {self.test_cases_data}")
            print(f"[DEBUG] Current subtype_id_map: {self.subtype_id_map}")

            # Update title label, clear old tasks, and populate new tasks
            if hasattr(self, 'title_label') and self.title_label.winfo_exists():
                self.title_label.config(text=f"Test Cases: {project_name}")

            # clear old tasks
            for task_text in list(self.task_widgets.keys()):
                widget = self.task_widgets.pop(task_text, None)
                if widget and widget.winfo_exists():
                    widget.destroy()

            # Add tasks based on test_cases_data dictionary
            if isinstance(test_cases_data, dict):
                todo_frame = self.column_content_frames.get("todo")
                inprogress_frame = self.column_content_frames.get("inprogress")
                completed_frame = self.column_content_frames.get("completed")

                if todo_frame and todo_frame.winfo_exists():
                    for task_text in test_cases_data.get("todo", []):
                        self._create_task_widget(todo_frame, task_text)
                if inprogress_frame and inprogress_frame.winfo_exists():
                    for task_text in test_cases_data.get("inprogress", []):
                        self._create_task_widget(inprogress_frame, task_text)
                if completed_frame and completed_frame.winfo_exists():
                    for task_text in test_cases_data.get("completed", []):
                        self._create_task_widget(completed_frame, task_text)
            else:
                print("Warning: Test cases data format not as expected (dict). Loading all into 'To Do'.")
                todo_frame = self.column_content_frames.get("todo")
                if todo_frame and todo_frame.winfo_exists() and isinstance(test_cases_data, (list, tuple)):
                    for test_case in test_cases_data:
                        self._create_task_widget(todo_frame, str(test_case))
                else:
                    print("Error: Cannot load tasks, invalid data format or 'To Do' frame missing.")

        def _get_task_frame_from_event(self, event_widget):
            """ Helper to find the main task Frame from an event source (Label or Frame). """
            if not event_widget or not event_widget.winfo_exists(): return None
            current_widget = event_widget
            for _ in range(2):
                if isinstance(current_widget, tk.Frame) and hasattr(current_widget, 'task_text'):
                    if current_widget.task_text in self.task_widgets and self.task_widgets[current_widget.task_text] == current_widget:
                        return current_widget
                if hasattr(current_widget, 'master'):
                    current_widget = current_widget.master
                else:
                    break
            return None

        def on_start_drag(self, event):
            task_frame = self._get_task_frame_from_event(event.widget)
            if task_frame and task_frame.winfo_exists() and hasattr(task_frame, 'parent_column_frame'):
                if task_frame.task_text in self.task_widgets:
                    self.drag_data["widget"] = task_frame
                    self.drag_data["text"] = task_frame.task_text
                    self.drag_data["source_column_frame"] = task_frame.parent_column_frame
                    task_frame.configure(cursor="hand2")
                    # Use bright drag border
                    task_frame.config(highlightbackground=KANBAN_DRAG_BORDER, highlightcolor=KANBAN_DRAG_BORDER)

        def on_drag(self, event):
            pass # Kept for consistency

        def on_drop(self, event):
            original_drag_widget = self.drag_data["widget"]
            task_text = self.drag_data["text"]
            source_column_frame = self.drag_data["source_column_frame"]
            self.drag_data = {"widget": None, "text": None, "source_column_frame": None}

            if original_drag_widget and original_drag_widget.winfo_exists():
                original_drag_widget.configure(cursor="")
                # Reset to dark theme task border
                original_drag_widget.config(highlightbackground=KANBAN_TASK_BORDER, highlightcolor=KANBAN_TASK_BORDER)

            if not original_drag_widget or not task_text or not source_column_frame:
                return

            try:
                x_root, y_root = event.x_root, event.y_root
                widget_below_mouse = self.winfo_containing(x_root, y_root)
                target_column_frame = None
                if widget_below_mouse and widget_below_mouse.winfo_exists():
                    current = widget_below_mouse
                    while current is not None and current != self:
                        if current in self.column_id_map:
                            target_column_frame = current
                            break
                        task_frame_below = self._get_task_frame_from_event(current)
                        if task_frame_below and hasattr(task_frame_below, 'parent_column_frame'):
                            target_column_frame = task_frame_below.parent_column_frame
                            break
                        if isinstance(current, tk.Label) and hasattr(current, 'master') and current.master.winfo_children():
                            outer_frame = current.master
                            for key, content_f in self.column_content_frames.items():
                                if content_f.master == outer_frame:
                                    target_column_frame = content_f
                                    break
                            if target_column_frame: break
                        if hasattr(current, 'master'): current = current.master
                        else: break

                if target_column_frame and target_column_frame.winfo_exists() and target_column_frame != source_column_frame:
                    source_col_key = self.column_id_map.get(source_column_frame, '?')
                    target_col_key = self.column_id_map.get(target_column_frame, '?')
                    print(f"Moving '{task_text}' from '{source_col_key}' to '{target_col_key}'")
                    if original_drag_widget.winfo_exists(): original_drag_widget.destroy()
                    if task_text in self.task_widgets: del self.task_widgets[task_text]
                    self._create_task_widget(target_column_frame, task_text) # Recreates with dark theme colors
                    print(f"Move complete for '{task_text}'.")
                else:
                    if not target_column_frame or not target_column_frame.winfo_exists(): print(f"Drop failed for '{task_text}': Invalid or no target column.")
                    elif target_column_frame == source_column_frame: print(f"Drop ignored for '{task_text}': Same column.")
            except Exception as e:
                print(f"Unexpected error during drag/drop finalization for task '{task_text}': {e}")
                if original_drag_widget and original_drag_widget.winfo_exists():
                    original_drag_widget.configure(cursor="")
                    original_drag_widget.config(highlightbackground=KANBAN_TASK_BORDER, highlightcolor=KANBAN_TASK_BORDER)

        def on_task_enter(self, event):
            task_frame = self._get_task_frame_from_event(event.widget)
            if task_frame and task_frame.winfo_exists() and self.drag_data["widget"] != task_frame:
                # Use dark theme task hover BG
                task_frame.config(bg=KANBAN_TASK_HOVER_BG)
                for child in task_frame.winfo_children():
                    if isinstance(child, tk.Label) and child.winfo_exists():
                        child.config(bg=KANBAN_TASK_HOVER_BG)

        def on_task_leave(self, event):
            task_frame = self._get_task_frame_from_event(event.widget)
            if task_frame and task_frame.winfo_exists():
                if self.drag_data["widget"] != task_frame:
                    # Reset to dark theme task BG
                    task_frame.config(bg=KANBAN_TASK_BG)
                    for child in task_frame.winfo_children():
                        if isinstance(child, tk.Label) and child.winfo_exists():
                            child.config(bg=KANBAN_TASK_BG)

        def on_column_content_enter(self, event):
            widget = event.widget
            if widget in self.column_id_map and widget.winfo_exists():
                if self.drag_data["widget"]:
                    # Use dark theme column hover BG
                    widget.config(bg=KANBAN_COLUMN_HOVER_BG)

        def on_column_content_leave(self, event):
            widget = event.widget
            if widget in self.column_id_map and widget.winfo_exists() and hasattr(widget, 'original_bg'):
                # Reset to original dark theme column BG
                widget.config(bg=widget.original_bg)

    try:
        if "Dashboard" not in pages:
            messagebox.showerror("Initialization Error", "Dashboard page frame not found.")
            root.destroy()
            exit()

        # Instantiate pages (they will inherit the dark theme constants)
        fonts = {
            "TABLE_FONT_HEADER": TABLE_FONT_HEADER,
            "TABLE_FONT_PROJECT_NAME": TABLE_FONT_PROJECT_NAME,
            "TABLE_FONT_BODY_SMALL": TABLE_FONT_BODY_SMALL,
            "TABLE_FONT_STATUS": TABLE_FONT_STATUS,
            "TABLE_FONT_BODY_REGULAR": TABLE_FONT_BODY_REGULAR
        }

        # This must be after page_container is created
        project_page = ProjectPage(page_container, switch_page, fonts, projects_data, token=agent_data.get("token"), base_url=base_url)
        project_page.grid(row=0, column=0, sticky="nsew")
        pages["Project"] = project_page

        pages["Job"] = JobPage(page_container, switch_page)
        pages["Job"].load_jobs_from_agent_data(agent_data)  # <- Pass the live agent data
        pages["Job"].grid(row=0, column=0, sticky="nsew")


        pages["TestCases"] = TestCasesPage(
            page_container,
            switch_page,
            base_url,
            pages,
            token=agent_data.get("token")
        )

        pages["TestCases"].grid(row=0, column=0, sticky="nsew")

       

        report_page = ReportPage(page_container, switch_page, fonts, projects_data, base_url=base_url, agent_id=agent_data.get('agentid'),token=agent_data.get('token'))
        report_page.grid(row=0, column=0, sticky="nsew")
        pages["Report"] = report_page

        # Add Suites page
        tree_page = TreePage(page_container, switch_page, agent_data=agent_data, base_url=base_url, token=agent_data.get("token"))
        tree_page.grid(row=0, column=0, sticky="nsew")
        pages["Suites"] = tree_page

        # pages["Terminal"] = RealTerminal(
        #     parent=page_container,
        #     base_url=base_url,
        #     run_on_start=False,  # <-- prevent auto-run at creation
        #     repo_dir="/path/to/repo",
        #     username="demo_user",
        #     password="secret",
        #     folder_path=os.getcwd(),
        #     result_path=os.path.join(os.getcwd(), "results"),
        #     agent_name="agent42",
        #     on_terminal_close=lambda: switch_page("TestCaseOptions"),
        #     interface="eth0",
        #     ipv4="192.168.0.10",
        #     ipv6="::1",
        #     back_callback=lambda: switch_page("TestCaseOptions")
        # )
        # pages["Terminal"].grid(row=0, column=0, sticky="nsew")




    except Exception as e:
        messagebox.showerror("Initialization Error", f"Failed to create application pages: {e}")
        root.destroy()
        exit()

    # --- Start Animations (Only for Dashboard page) ---
    initial_delay = 500

    # --- Final donut + triangle animation start ---
    def start_animations():
        try:
            # Donut animation removed as it's not part of the new layout
            pass
        except Exception as e:
            print("Animation error:", e)

    # Delay start after widgets are drawn
    root.after(500, start_animations)

    # --- Add TestCaseOptions Page ---
    class TestCaseOptionsPage(tk.Frame):
        def __init__(self, parent, switch_page_callback, base_url=None, token=None):
            super().__init__(parent, bg=COLOR_CONTENT_BG)
            self.switch_page_callback = switch_page_callback
            self.base_url = base_url
            self.token = token
            
            # Title
            title_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
            title_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
            
            # Back button
            back_btn = tk.Button(
                title_frame, 
                text="← Back",
                command=lambda: switch_page("TestCases"),
                bg=COLOR_PANEL_BG,
                fg=COLOR_TEXT_LIGHT,
                font=("Segoe UI", 10, "bold"),
                relief=tk.FLAT,
                bd=0,
                padx=10,
                pady=5,
                activebackground=COLOR_PRIMARY,
                activeforeground=COLOR_TEXT_LIGHT
            )
            back_btn.pack(side=tk.LEFT)
            
            # Title
            title = tk.Label(
                title_frame,
                text="Test Case Options",
                font=("Arial", 18, "bold"),
                fg=COLOR_TEXT_LIGHT,
                bg=COLOR_CONTENT_BG
            )
            title.pack(side=tk.LEFT, padx=10)
            
            # Content
            content_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # Add your test case options here
            options_label = tk.Label(
                content_frame,
                text="Test case options will be displayed here.",
                font=("Arial", 12),
                fg=COLOR_TEXT_LIGHT,
                bg=COLOR_CONTENT_BG
            )
            options_label.pack(pady=20)
    
    # Register TestCaseOptions page
    test_case_options_page = TestCaseOptionsPage(
        page_container,
        switch_page,
        base_url=base_url,
        token=agent_data.get('token')
    )
    test_case_options_page.grid(row=0, column=0, sticky="nsew")
    pages["TestCaseOptions"] = test_case_options_page

    # --- Show Initial Page ---
    if "Dashboard" in pages and pages["Dashboard"].winfo_exists():
        switch_page("Dashboard") # Switches with dark theme sidebar styling
    else:
        messagebox.showerror("Startup Error", "Initial 'Dashboard' page not found or invalid.")
        available_pages = [name for name, page in pages.items() if page.winfo_exists()]
        if available_pages:
            first_page = available_pages[0]
            print(f"Switching to first available page: {first_page}")
            switch_page(first_page)
        else:
            root.destroy()
            exit()


    root.mainloop()

# class ReportDetailPage(tk.Frame):
#     def __init__(self, parent, switch_page_callback, project_data):
#         super().__init__(parent, bg=COLOR_CONTENT_BG)
#         self.switch_page_callback = switch_page_callback
#         self.project_data = project_data
#         # Title
#         title_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
#         title_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
#         title = tk.Label(title_frame, text=f"{project_data[0]} - Details", font=("Arial", 18, "bold"), fg=COLOR_TEXT_LIGHT, bg=COLOR_CONTENT_BG)
#         title.pack(side=tk.LEFT)
#         back_btn = tk.Button(title_frame, text="← Back", command=lambda: switch_page_callback("Report"), bg=COLOR_PANEL_BG, fg=COLOR_TEXT_LIGHT, font=("Segoe UI", 10, "bold"), relief=tk.FLAT, bd=0, padx=10, pady=5, activebackground=COLOR_PRIMARY, activeforeground=COLOR_TEXT_LIGHT)
#         back_btn.pack(side=tk.RIGHT)
#         # Subtypes list
#         subtypes = project_data[6]
#         list_frame = tk.Frame(self, bg=COLOR_CONTENT_BG)
#         list_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
#         for subtype in subtypes:
#             folder = tk.Frame(list_frame, bg="#23272e", bd=2, relief=tk.RIDGE, padx=24, pady=18)
#             folder.pack(fill=tk.X, pady=12)
#             name_label = tk.Label(folder, text=subtype.get("type", "Unnamed"), font=("Arial", 15, "bold"), fg=COLOR_TEXT_LIGHT, bg="#23272e", anchor="w")
#             name_label.pack(side=tk.LEFT, padx=(0, 30))
#             status = subtype.get("status", "Unknown")
#             status_label = tk.Label(folder, text=status.title(), font=("Arial", 13, "bold"), fg="#2ecc71" if status.lower() in ("done", "completed") else "#f1c40f", bg="#23272e", anchor="e")
#             status_label.pack(side=tk.RIGHT)
    def preview_file(self, fname, files_path):
        import os
        import subprocess
        from tkinter import messagebox, Toplevel, scrolledtext
        from PIL import Image, ImageTk
        ext = fname.lower().split('.')[-1]
        src_path = os.path.join(files_path, fname)
        if ext in ["png", "jpg", "jpeg"]:
            # Image preview (minimal popup)
            img = Image.open(src_path)
            # Get screen size and set preview to half screen
            screen_width = self.winfo_toplevel().winfo_screenwidth()
            screen_height = self.winfo_toplevel().winfo_screenheight()
            max_width = screen_width // 2
            max_height = screen_height // 2
            img.thumbnail((max_width, max_height), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            win = Toplevel(self)
            win.title(fname)
            win.configure(bg=COLOR_CONTENT_BG)
            win.resizable(False, False)
            # Center the window on the screen
            win.update_idletasks()
            width, height = photo.width(), photo.height()
            width = min(width, max_width)
            height = min(height, max_height)
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
            win.geometry(f"{width}x{height}+{x}+{y}")
            lbl = tk.Label(win, image=photo, bg=COLOR_CONTENT_BG)
            lbl.image = photo
            lbl.pack(expand=True, fill="both")
        elif ext == "txt":
            # Text preview
            win = Toplevel(self)
            win.title(fname)
            win.configure(bg=COLOR_CONTENT_BG)
            win.resizable(False, False)
            with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            txt = scrolledtext.ScrolledText(win, width=80, height=30, bg=COLOR_PANEL_BG, fg=COLOR_TEXT_LIGHT, insertbackground=COLOR_TEXT_LIGHT)
            txt.insert(tk.END, content)
            txt.pack(expand=True, fill="both")
            bind_text_mousewheel(txt)
            def block_edit(event):
                return "break"
            txt.bind("<Key>", block_edit)
        elif ext == "docx":
            # Open with LibreOffice
            try:
                subprocess.Popen(["libreoffice", src_path])
            except Exception as e:
                messagebox.showerror("Preview Error", f"Could not open DOCX: {e}")
        elif ext == "mp4":
            # Open with system default player
            try:
                subprocess.Popen(["xdg-open", src_path])
            except Exception as e:
                messagebox.showerror("Preview Error", f"Could not open video: {e}")
        else:
            messagebox.showinfo("Preview", f"No preview available for this file type: {ext}")

def get_tmp_file_structure(tmp_root=None):
    import os
    structure = {}
    
    # Use cwd/tmp by default (current working directory + tmp)
    if tmp_root is None:
        tmp_root = os.path.join(os.getcwd(), "tmp")
    
    if not os.path.exists(tmp_root):
        print(f"DEBUG: {tmp_root} does not exist")
        return structure

    for project in os.listdir(tmp_root):
        project_path = os.path.join(tmp_root, project)
        if not os.path.isdir(project_path):
            continue
        structure[project] = {}
        for testcase in os.listdir(project_path):
            testcase_path = os.path.join(project_path, testcase)
            if not os.path.isdir(testcase_path):
                continue
            structure[project][testcase] = {}
            for scan_id in os.listdir(testcase_path):
                scan_id_path = os.path.join(testcase_path, scan_id)
                if not os.path.isdir(scan_id_path):
                    continue
                files = []
                for f in os.listdir(scan_id_path):
                    fpath = os.path.join(scan_id_path, f)
                    if os.path.isfile(fpath):
                        files.append(f)
                structure[project][testcase][scan_id] = files
                print(f"DEBUG: {scan_id_path} files: {files}")
    # print('DEBUG: Nested structure:', structure)
    return structure

def save_scan_repo_mapping(scan_id, repo_dir, map_file='scan_repo_map.json'):
    try:
        if os.path.exists(map_file):
            with open(map_file, 'r') as f:
                try:
                    mapping = json.load(f)
                except Exception:
                    mapping = {}
        else:
            mapping = {}
        mapping[scan_id] = repo_dir
        with open(map_file, 'w') as f:
            json.dump(mapping, f, indent=2)
    except Exception as e:
        print(f"Error saving scan-repo mapping: {e}")

def get_repo_dir_for_scan(scan_id, map_file='scan_repo_map.json'):
    try:
        with open(map_file, 'r') as f:
            mapping = json.load(f)
        return mapping.get(scan_id)
    except Exception as e:
        print(f"Error reading scan-repo mapping: {e}")
        return None

# Utility function to get a unique name with (1), (2), ... pattern
import re

def get_unique_name(dest_dir, name):
    import os
    base, ext = os.path.splitext(name)
    # For folders, ext will be ''
    pattern = re.compile(r"^(.*)\((\d+)\)$")
    candidate = name
    counter = 1
    while os.path.exists(os.path.join(dest_dir, candidate)):
        m = pattern.match(base)
        if m:
            base_name = m.group(1).rstrip()
            counter = int(m.group(2)) + 1
        else:
            base_name = base
        if ext:
            candidate = f"{base_name}({counter}){ext}"
        else:
            candidate = f"{base_name}({counter})"
        counter += 1
    return candidate

# Utility function to check if a path is a subpath of another
import os

def is_subpath(child, parent):
    child = os.path.abspath(child)
    parent = os.path.abspath(parent)
    try:
        return os.path.commonpath([child]) == os.path.commonpath([child, parent])
    except Exception:
        return False

def bind_text_mousewheel(widget):
    def _on_mousewheel(event):
        widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"
    def _on_mousewheel_linux(event):
        if event.num == 4:
            widget.yview_scroll(-1, "units")
        elif event.num == 5:
            widget.yview_scroll(1, "units")
        return "break"
    widget.bind("<MouseWheel>", _on_mousewheel)
    widget.bind("<Button-4>", _on_mousewheel_linux)
    widget.bind("<Button-5>", _on_mousewheel_linux)
