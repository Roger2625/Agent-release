import gi
import os
import json
import threading
from gi.repository import Gtk, Vte, GLib, Gdk
import requests
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
 
# Global dictionary to track status of test cases by scan_id
AGENT_STATUS = {}
 
class TerminalApp(Gtk.Window):
    def __init__(self, scan_id, repo_dir, base_url, folder_path, result_path, agent_name, on_terminal_close, token=None, upload_files_endpoint=None, upload_results_endpoint=None):
        super().__init__(title="Terminal Test")
        self.scan_id = scan_id
        self.repo_dir = repo_dir
        self.base_url = base_url
        self.folder_path = folder_path
        # Use result_path as is, don't append scan_id again
        self.result_path = result_path
        self.agent_name = agent_name
        self.on_terminal_close = on_terminal_close
        self.token = token
        self.upload_files_endpoint = upload_files_endpoint or "api/scan/upload_files"
        self.upload_results_endpoint = upload_results_endpoint or "api/scan/upload"
        # Create result_path if it doesn't exist
        os.makedirs(self.result_path, exist_ok=True)
 
        # print("result_path:", self.result_path)
 
        self.set_decorated(False)
        display = Gdk.Display.get_default()
        monitor = display.get_monitor(0)
        geometry = monitor.get_geometry()
        self.set_default_size(geometry.width, geometry.height)
 
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)
 
        frame = Gtk.Frame()
        frame.set_border_width(10)
        vbox.pack_start(frame, True, True, 0)
 
        self.terminal = Vte.Terminal()
        self.terminal.set_size(80, 24)
 
        self.terminal.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            None,
            ["/bin/bash", "-c", self.get_bash_commands()],
            None,
            GLib.SpawnFlags.DEFAULT,
            None,
            self.folder_path,
        )
 
        self.terminal.connect("child-exited", self.on_process_exit)
        self.terminal.connect("key-press-event", self.on_key_press)
        self.terminal.connect("button-press-event", self.on_right_click)
 
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)
        scrolled_window.add(self.terminal)
        frame.add(scrolled_window)
 
        self.connect("destroy", self.on_window_close)
        self.show_all()
 
    def get_bash_commands(self):
        return f"""
            execute_script=\"{os.path.join(self.folder_path, 'execute.sh')}\"
            exec_status=1
 
            if [ ! -f \"$execute_script\" ]; then
                echo \"Error: execute.sh script not found at $execute_script\"
                echo \"Please verify the path and try again.\"
                echo \"Press ESC to close...\"
                read -p \"Press Enter to close...\"
            else
                chmod +x \"$execute_script\"
                \"$execute_script\" \"{self.scan_id}\" \"{self.folder_path}\" \"{self.result_path}\"
                exec_status=$?
 
                if [ $exec_status -ne 0 ]; then
                    echo \"Warning: The test script exited with error code $exec_status.\"
                    echo \"Press ESC to close...\"
                    read
                else
                    echo \"Test script executed successfully.\"
                    echo \"Press ESC to close...\"
                    read
                fi
            fi
        """
 
    def set_status_inprogress(self):
        """Set the test case status to 'inprogress' in the local agent state."""
        AGENT_STATUS[self.scan_id] = 'inprogress'
        print(f"[AGENT] Status for scan_id {self.scan_id} set to 'inprogress'.")
 
    def show_confirmation_dialog(self):
        """Show a confirmation dialog when user presses ESC."""
        dialog = Gtk.Dialog(
            title="Close Terminal",
            parent=self,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK
            )
        )
        
        dialog.set_default_size(300, 100)
        
        # Create the message label
        label = Gtk.Label()
        label.set_markup("<b>Warning:</b> The terminal will close.\nAre you sure you want to continue?")
        label.set_line_wrap(True)
        label.set_margin_start(20)
        label.set_margin_end(20)
        label.set_margin_top(20)
        label.set_margin_bottom(20)
        
        dialog.get_content_area().add(label)
        dialog.show_all()
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK:
            self.close_terminal()
    
    def close_terminal(self):
        """Close the terminal window and cleanup."""
        # Call the callback before destroying the window
        if self.on_terminal_close:
            GLib.idle_add(self.on_terminal_close)
            
        self.destroy()
        Gtk.main_quit()
 
    def on_process_exit(self, terminal, exit_status):
        print("Process exited with status:", exit_status)
        self.set_status_inprogress()
        
        if exit_status == 0:
            self.upload_files_via_http(self.result_path, self.repo_dir)
            self.upload_results({"agent_name": self.agent_name, "scan_id": self.scan_id})
        else:
            print("Upload skipped due to non-zero exit status.")

        # Call the callback before destroying the window
        if self.on_terminal_close:
            GLib.idle_add(self.on_terminal_close)
            
        self.destroy()
        Gtk.main_quit()
 
    def on_window_close(self, *args):
        Gtk.main_quit()
 
    def on_right_click(self, widget, event):
        if event.button == 3:
            menu = Gtk.Menu()
            copy_item = Gtk.MenuItem(label="Copy")
            copy_item.connect("activate", lambda _: self.terminal.copy_clipboard())
            paste_item = Gtk.MenuItem(label="Paste")
            paste_item.connect("activate", lambda _: self.terminal.paste_clipboard())
            menu.append(copy_item)
            menu.append(paste_item)
            menu.show_all()
            menu.popup_at_pointer(event)
            return True
        return False
 
    def on_key_press(self, widget, event):
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        if ctrl and event.keyval == Gdk.KEY_c:
            self.terminal.copy_clipboard()
            return True
        if ctrl and event.keyval == Gdk.KEY_v:
            self.terminal.paste_clipboard()
            return True
        
        # Handle ESC key
        if event.keyval == Gdk.KEY_Escape:
            self.show_confirmation_dialog()
            return True
            
        return False
 
    def upload_files_via_http(self, result_path, repo_dir):
        """Upload files from the result_path directory to the server via HTTP along with repo_dir."""
        url = f"{self.base_url}{self.upload_files_endpoint}"  # Use endpoint argument
        
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

            # Get all files from the result_path
            files_to_upload = []
            for filename in os.listdir(result_path):
                file_path = os.path.join(result_path, filename)
                if os.path.isfile(file_path):
                    files_to_upload.append(('files', (filename, open(file_path, 'rb'))))
            
            if files_to_upload:
                print("data: ", repo_dir)
                # print(f"Uploading {len(files_to_upload)} files to {url}")
                
                # Include repo_dir in the data
                data = {
                    'repo_dir': repo_dir  # Add repo_dir to the form data
                }
 
                # Make a POST request to upload the files and repo_dir
                headers = {}
                if current_token:
                    headers["Authorization"] = f"Bearer {current_token}"
                response = requests.post(url, files=files_to_upload, data=data, headers=headers)
                response.raise_for_status()  # Check for HTTP errors
 
                # print("Files and repo_dir successfully uploaded to the server:", response.json())
            else:
                print("No files found in result_path to upload.")
        
        except requests.RequestException as e:
            print(f"Error uploading files to server {url}: {e}")
        
 
    def upload_results(self, data):
        """Send the metadata or result JSON output to the server at the /upload endpoint."""
        url = f"{self.base_url}{self.upload_results_endpoint}"  # Use endpoint argument
        try:
            # Get fresh token from configuration file to avoid stale token issues
            current_token = None
            try:
                with open('client.conf.json', 'r') as file:
                    config = json.load(file)
                    current_token = config.get('token')
            except Exception as e:
                print(f"Error reading token from config: {e}")
                # Fallback to stored token if config read fails
                current_token = self.token

            headers = {"Content-Type": "application/json"}
            if current_token:
                headers["Authorization"] = f"Bearer {current_token}"
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()  # Check for HTTP errors
 
            print("Data successfully sent to the server:", response.json())
        except requests.RequestException as e:
            print(f"Error sending data to server {url}: {e}")
 
 
def run_terminal_app(scan_id, repo_dir,base_url, folder_path, result_path, agent_name, on_terminal_close, token=None, upload_files_endpoint=None, upload_results_endpoint=None):
    def gtk_main():
        win = TerminalApp(
            scan_id=scan_id,
            repo_dir=repo_dir,
            base_url=base_url,
            folder_path=folder_path,
            result_path=result_path,
            agent_name=agent_name,
            on_terminal_close=on_terminal_close,
            token=token,
            upload_files_endpoint=upload_files_endpoint,
            upload_results_endpoint=upload_results_endpoint
        )
        Gtk.main()
 
    threading.Thread(target=gtk_main, daemon=True).start()