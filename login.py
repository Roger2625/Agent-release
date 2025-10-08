import requests
import json
import gi
import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox,simpledialog
import zipfile
from PIL import Image, ImageTk
import base64
import psutil
import sys
import tkinter.simpledialog
from dotenv import load_dotenv
import os
 
 
BG_COLOR = "#1a1a1a"
ENTRY_BG = "#2a2a2a"
ENTRY_BORDER = "#444444"
TEXT_COLOR = "#ffffff"
BUTTON_BG = "#ff6600"
BUTTON_HOVER = "#ff8533"
 
load_dotenv()
 
class SimpleApp:    
    """Main Tkinter App that embeds GTK terminal"""
    config_file = 'client.conf.json'
 
    def __init__(self, callback=None):
        # Store the callback function
        self.root = tk.Tk()
        self.callback = callback
        self.root.title("Agent")
        self.root.tk.call('wm', 'title', self.root._w, "Agent")
       
        self.root.configure(bg=BG_COLOR)
 
        style = ttk.Style()
        style.configure('Custom.TButton', background='#ddd2c9', foreground='white', padding=10, borderwidth=0)
        style.map('Custom.TButton', background=[('active', '#0d5da3')])
 
        # Set hover color for Treeview rows
        style.map("Custom.Treeview",
                  background=[('active', '#add8e6'), ('selected', '#add8e6')],
                  foreground=[('active', 'black'), ('selected', 'black')])
 
 
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}")
        self.root.resizable(True, True)
 
        self.input_frame = None
        self.details_frame = None
        self.dut_details = []
        self.agent_name = ""
        self.config_data = {}
        self.terminal_frame = None
        self.subtypes_dict = {}
        self.selected_interface = None  
        self.target_ipv4 = None  
        self.target_ipv6 = None  
 
        if self.load_configuration():
            self.get_data(self.config_data["server_url"], self.config_data["token"], get_data_endpoint="/api/connection/get_data")
        else:
            self.show_connection_window()
        
        self.root.mainloop()
 
    def load_configuration(self):
        """Load server configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as file:
                try:
                    self.config_data = json.load(file)
                    if "server_url" in self.config_data and "token" in self.config_data:
                        return True
                except json.JSONDecodeError:
                    print("Warning: Configuration file is empty or corrupted.")
        return False
 
    def create_rounded_entry(self, parent, text_var, width=300, height=40, radius=10):
        frame = tk.Frame(parent, bg=BG_COLOR)
        canvas = tk.Canvas(frame, width=width, height=height, bg=BG_COLOR, highlightthickness=0)
        canvas.pack()
 
        self.create_round_rect(canvas, 0, 0, width, height, r=radius, fill=ENTRY_BG, outline=ENTRY_BG)
 
        entry = tk.Entry(frame, textvariable=text_var, font=("Segoe UI", 11),
                        bg=ENTRY_BG, fg=TEXT_COLOR, relief="flat", insertbackground=TEXT_COLOR,
                        highlightthickness=0, borderwidth=0)
        entry.place(x=10, y=8, width=width - 20, height=height - 16)
 
        return frame
 
    def create_round_rect(self, canvas, x1, y1, x2, y2, r=10, **kwargs):
        canvas.create_arc(x1, y1, x1 + 2*r, y1 + 2*r, start=90, extent=90, **kwargs)
        canvas.create_arc(x2 - 2*r, y1, x2, y1 + 2*r, start=0, extent=90, **kwargs)
        canvas.create_arc(x2 - 2*r, y2 - 2*r, x2, y2, start=270, extent=90, **kwargs)
        canvas.create_arc(x1, y2 - 2*r, x1 + 2*r, y2, start=180, extent=90, **kwargs)
        canvas.create_rectangle(x1 + r, y1, x2 - r, y2, **kwargs)
        canvas.create_rectangle(x1, y1 + r, x2, y2 - r, **kwargs)
 
    def create_rounded_button(self, parent, text, command=None, width=300, height=45, radius=10):
        frame = tk.Frame(parent, bg=BG_COLOR)
        canvas = tk.Canvas(frame, width=width, height=height, bg=BG_COLOR, highlightthickness=0)
        canvas.pack()
 
        def draw_button(color):
            canvas.delete("all")  # Clear the canvas on each draw
            self.create_round_rect(canvas, 0, 0, width, height, r=radius, fill=color, outline=color)
            canvas.create_text(width//2, height//2, text=text, fill="white", font=("Segoe UI", 11, "bold"), tags="btn_text")
 
        draw_button(BUTTON_BG)
 
        def on_enter(event): draw_button(BUTTON_HOVER)
        def on_leave(event): draw_button(BUTTON_BG)
        def on_click(event):
            if command: command()
 
        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<Button-1>", on_click)
        canvas.tag_bind("btn_text", "<Button-1>", on_click)
 
        return frame
 
    
    def show_connection_window(self):
 
        """Show window for login"""
 
        if self.input_frame is not None:
 
            self.input_frame.destroy()
 
 
        # Main container
 
        self.input_frame = tk.Frame(self.root, bg=BG_COLOR, padx=0, pady=0)
 
        self.input_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=500, height=500)
 
 
        # Form section
 
        self.form_frame = tk.Frame(self.input_frame, bg=BG_COLOR, padx=60, pady=40)
 
        self.form_frame.grid(row=0, column=1, sticky="nsew")
 
 
        # Header Frame
 
        self.header_frame = tk.Frame(self.form_frame, bg=BG_COLOR)
 
        self.header_frame.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="n")
 
        tk.Label(self.header_frame, text="AGENT", font=("Segoe UI", 28, "bold"), bg=BG_COLOR, fg="#ff6600").pack(pady=(20, 0))
        tk.Label(self.header_frame, text="Login", font=("Segoe UI", 14), bg=BG_COLOR, fg="#bbbbbb").pack(pady=(0, 20))
 
 
        # Ensure form_frame can stretch column 1 (the input field)
        self.form_frame.columnconfigure(1, weight=1)
 
        tk.Label(
            self.form_frame,
            text="Server URL",
            bg=BG_COLOR,
            fg="#777",
            font=("Segoe UI", 11)
        ).grid(row=2, column=0, columnspan=2, sticky='w', pady=(0, 5), padx=(0, 5))
 
        # Server URL entry field (row 3, spans 2 columns)
        self.server_url_var = tk.StringVar()
        server_url_entry = self.create_rounded_entry(self.form_frame, self.server_url_var, radius=5)
        server_url_entry.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(0, 15), padx=(0, 5))
 
        # API Key label (row 4)
        tk.Label(
            self.form_frame,
            text="API Key",
            bg=BG_COLOR,
            fg="#777",
            font=("Segoe UI", 11)
        ).grid(row=4, column=0, columnspan=2, sticky='w', pady=(0, 5), padx=(0, 5))
 
        # API Key entry field (row 5)
        self.api_key_var = tk.StringVar()
        api_key_entry = self.create_rounded_entry(self.form_frame, self.api_key_var, radius=5)
        api_key_entry.grid(row=5, column=0, columnspan=2, sticky='ew', pady=(0, 15), padx=(0, 5))
 
        self.login_button = self.create_rounded_button(self.form_frame, "Login", command=self.connect_to_server, radius=5)
        self.login_button.grid(row=6, column=0, columnspan=2, pady=20)
 
        # Forgot API Key Label
        tk.Label(self.form_frame, text="Forgot API Key?", fg="#999999", bg=BG_COLOR, font=("Segoe UI", 9)).grid(
            row=7, column=0, columnspan=2, pady=(0, 10)
        )
 
        # Hover effect
        self.login_button.bind("<Enter>", lambda e: self.login_button.config(bg="#f8e5d9"))
        self.login_button.bind("<Leave>", lambda e: self.login_button.config(bg="#702c01"))
 
    def connect_to_server(self):
        """Connect to server and validate API key"""
        base_url = self.server_url_var.get().strip()
        validate_endpoint = "/api/connection/validateKey"
    
        if not validate_endpoint:
            messagebox.showerror("Configuration Error", "VALIDATE_ENDPOINT is not set.")
            return
 
        validate_endpoint = validate_endpoint.strip()
        
        # print("validate: ", validate_endpoint)
        if not base_url:
            messagebox.showerror("Input Error", "Please enter the server URL.")
            return
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Input Error", "Please enter an API key.")
            return
 
        try:
            if not base_url.endswith('/'):
                base_url += '/'
            validate_url = base_url + validate_endpoint
            
            request_data = {"api_key": api_key}
            # print("validate_url: ", validate_url)
 
            # Try to connect to the server with API key (First-time connection)
            response = requests.post(validate_url, json=request_data)
            print(response)
 
            if response.status_code == 200:
                data = response.json()
                token = data.get("token")
                if token:
                    # After successful validation, save the configuration and fetch EUT config
                    self.save_configuration(base_url, token)
                    self.get_data(base_url, token, "/api/connection/get_data")
                else:
                    messagebox.showerror("Validation Error", "Server did not return a token.")
            elif response.status_code == 403:
                messagebox.showerror("Validation Error", "This API key has already been validated.")
            else:
                messagebox.showerror("Validation Error", f"Server returned status code {response.status_code}: {response.text}")
 
        except requests.RequestException as e:
            messagebox.showerror("Connection Error", f"Request error occurred: {e}")
 
    def save_configuration(self, base_url, token):
        """Save server URL and token to config file"""
        config = {
            "server_url": base_url,
            "token": token
        }
 
        with open(self.config_file, 'w') as file:
            json.dump(config, file)
        
 
    def get_data(self, base_url, token, get_data_endpoint):
        """Retrieve GetData with additional parameters"""
        try:
            config_url = base_url + get_data_endpoint
            # print("config_url :", config_url )
            request_data = {
                "selected_interface": self.selected_interface,
                "target_ipv4": self.target_ipv4,
                "target_ipv6": self.target_ipv6
            }
 
            headers = {
                "Authorization": f"Bearer {token}"
            }
 
            response = requests.post(config_url, json=request_data, headers=headers)
            #print("response: 281", response)
            
            if response.status_code == 200:
                data = response.json()
                # print("data: ", data)
                new_token = data.get("token")
                if new_token:
                    self.save_configuration(base_url, new_token)
                    if self.callback:
                        self.root.destroy()
                        self.callback(data, base_url)
 
            else:
                if os.path.exists(self.config_file):
                    messagebox.showerror("Data Retrieval Error", f"Server returned status code {response.status_code}: {response.text}")
                else:
                    print("First-time connection, no error shown.")
 
        except requests.RequestException as e:
            messagebox.showerror("Connection Error", f"Request error occurred: {e}")
   