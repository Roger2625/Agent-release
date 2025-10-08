import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use('TkAgg')

# Color scheme
COLOR_BG = "#1e1e1e"
COLOR_SIDEBAR_BG = "#252526"
COLOR_CONTENT_BG = "#1e1e1e"
COLOR_PANEL_BG = "#2d2d30"
COLOR_TEXT_LIGHT = "#cccccc"
COLOR_TEXT_MUTED_DARK_BG = "#8a8a8a"
COLOR_PRIMARY = "#007acc"
COLOR_SECONDARY = "#6c757d"
COLOR_SUCCESS = "#28a745"
COLOR_WARNING = "#ffc107"
COLOR_DANGER = "#dc3545"
COLOR_INFO = "#17a2b8"

def safe_name(name):
    """Convert name to safe format for file operations"""
    return "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()

def set_testcase_inprogress(agent_data, project_id, testcase_id):
    """Set testcase status to in progress"""
    for project in agent_data.get("data", []):
        if project.get("project_id") == project_id:
            for testcase in project.get("testcases", []):
                if testcase.get("testcase_id") == testcase_id:
                    testcase["status"] = "In Progress"
                    return True
    return False

def start_dashboard(agent_data, base_url):
    """Start the main dashboard application"""
    root = tk.Tk()
    root.title("WingzAI Dashboard")
    root.geometry("1400x800")
    root.configure(bg=COLOR_BG)
    
    # Configure grid weights
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    
    # Top header bar
    header_frame = tk.Frame(root, bg=COLOR_SIDEBAR_BG, height=50)
    header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
    header_frame.grid_propagate(False)
    
    # Header content
    header_label = tk.Label(header_frame, text="Dashboard", font=("Arial", 16, "bold"), 
                          fg=COLOR_TEXT_LIGHT, bg=COLOR_SIDEBAR_BG)
    header_label.pack(expand=True)
    
    # Left sidebar
    sidebar_frame = tk.Frame(root, bg=COLOR_SIDEBAR_BG, width=250)
    sidebar_frame.grid(row=1, column=0, sticky="ns")
    sidebar_frame.grid_propagate(False)
    
    # Sidebar content
    # Demo section
    demo_frame = tk.Frame(sidebar_frame, bg=COLOR_SIDEBAR_BG)
    demo_frame.pack(fill=tk.X, padx=15, pady=15)
    
    demo_icon = tk.Label(demo_frame, text="D4", font=("Arial", 12, "bold"), 
                        bg=COLOR_PANEL_BG, fg=COLOR_TEXT_LIGHT, width=3, height=1)
    demo_icon.pack(side=tk.LEFT, padx=(0, 10))
    
    demo_info = tk.Frame(demo_frame, bg=COLOR_SIDEBAR_BG)
    demo_info.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    demo_title = tk.Label(demo_info, text="Demo 4", font=("Arial", 12, "bold"), 
                         fg=COLOR_PRIMARY, bg=COLOR_SIDEBAR_BG)
    demo_title.pack(anchor="w")
    
    # Separator
    separator = tk.Frame(sidebar_frame, bg=COLOR_PANEL_BG, height=1)
    separator.pack(fill=tk.X, padx=15, pady=10)
    
    # Navigation items
    nav_items = ["Dashboard", "Project", "Job", "Report", "Tree"]
    current_page = tk.StringVar(value="Dashboard")
    
    for item in nav_items:
        nav_frame = tk.Frame(sidebar_frame, bg=COLOR_SIDEBAR_BG)
        nav_frame.pack(fill=tk.X, padx=15, pady=2)
        
        if item == "Tree":
            # Special styling for Tree button
            nav_btn = tk.Button(nav_frame, text=item, font=("Arial", 11, "bold"),
                              bg=COLOR_PRIMARY, fg=COLOR_TEXT_LIGHT,
                              relief=tk.FLAT, bd=0, padx=15, pady=8,
                              activebackground=COLOR_SECONDARY, activeforeground=COLOR_TEXT_LIGHT)
        else:
            nav_btn = tk.Button(nav_frame, text=item, font=("Arial", 11),
                              bg=COLOR_SIDEBAR_BG, fg=COLOR_TEXT_LIGHT,
                              relief=tk.FLAT, bd=0, padx=15, pady=8,
                              activebackground=COLOR_PANEL_BG, activeforeground=COLOR_TEXT_LIGHT)
        
        nav_btn.pack(fill=tk.X)
    
    # Main content area
    content_frame = tk.Frame(root, bg=COLOR_CONTENT_BG)
    content_frame.grid(row=1, column=1, sticky="nsew")
    
    # Create pages
    pages = {}
    
    def create_panel(parent, row, col, rowspan=1, colspan=1):
        # Use dark panel background
        panel = tk.Frame(parent, bg=COLOR_PANEL_BG, relief=tk.FLAT, bd=1)
        panel.grid(row=row, column=col, rowspan=rowspan, columnspan=colspan, 
                  sticky="nsew", padx=10, pady=10)
        return panel
    
    def draw_rounded_rectangle(canvas, x1, y1, x2, y2, radius, **kwargs):
        """Draw a rounded rectangle on canvas"""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        canvas.create_polygon(points, smooth=True, **kwargs)
    
    def switch_page(page_name, **kwargs):
        """Switch to a different page"""
        # Hide all pages
        for page in pages.values():
            page.grid_remove()
        
        # Show selected page
        if page_name in pages:
            pages[page_name].grid()
            if hasattr(pages[page_name], 'tkraise'):
                pages[page_name].tkraise()
            if hasattr(pages[page_name], 'load_data'):
                pages[page_name].load_data(**kwargs)
    
    def logout():
        """Handle logout"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            root.destroy()
    
    # Dashboard page
    dashboard_page = tk.Frame(content_frame, bg=COLOR_CONTENT_BG)
    dashboard_page.grid(row=0, column=0, sticky="nsew")
    pages["Dashboard"] = dashboard_page
    
    # Configure grid weights for dashboard
    dashboard_page.grid_rowconfigure(0, weight=1)
    dashboard_page.grid_columnconfigure(0, weight=1)
    
    # Dashboard content
    dashboard_content = tk.Frame(dashboard_page, bg=COLOR_CONTENT_BG)
    dashboard_content.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
    
    # Configure grid weights for dashboard content
    dashboard_content.grid_rowconfigure(1, weight=1)
    dashboard_content.grid_columnconfigure(0, weight=1)
    dashboard_content.grid_columnconfigure(1, weight=1)
    
    # Status boxes
    status_frame = tk.Frame(dashboard_content, bg=COLOR_CONTENT_BG)
    status_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
    
    # Status boxes in a row
    status_boxes = []
    status_data = [
        {"title": "Total Projects", "value": "12", "color": COLOR_PRIMARY},
        {"title": "Active Jobs", "value": "5", "color": COLOR_SUCCESS},
        {"title": "Completed", "value": "8", "color": COLOR_INFO},
        {"title": "Failed", "value": "2", "color": COLOR_DANGER}
    ]
    
    for i, data in enumerate(status_data):
        box = create_panel(status_frame, 0, i)
        box.configure(width=200, height=100)
        box.grid_propagate(False)
        
        # Status box content
        title_label = tk.Label(box, text=data["title"], font=("Arial", 12),
                             fg=COLOR_TEXT_MUTED_DARK_BG, bg=COLOR_PANEL_BG)
        title_label.pack(pady=(15, 5))
        
        value_label = tk.Label(box, text=data["value"], font=("Arial", 24, "bold"),
                             fg=data["color"], bg=COLOR_PANEL_BG)
        value_label.pack()
        
        status_boxes.append({"box": box, "title": title_label, "value": value_label})
    
    # Charts area
    charts_frame = tk.Frame(dashboard_content, bg=COLOR_CONTENT_BG)
    charts_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
    
    # Configure grid weights for charts
    charts_frame.grid_rowconfigure(0, weight=1)
    charts_frame.grid_columnconfigure(0, weight=1)
    charts_frame.grid_columnconfigure(1, weight=1)
    
    # Left chart panel
    left_chart_panel = create_panel(charts_frame, 0, 0)
    left_chart_panel.configure(width=400, height=300)
    left_chart_panel.grid_propagate(False)
    
    # Right chart panel
    right_chart_panel = create_panel(charts_frame, 0, 1)
    right_chart_panel.configure(width=400, height=300)
    right_chart_panel.grid_propagate(False)
    
    # Create charts
    def get_random_color():
        """Generate a random color"""
        import random
        return f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"
    
    def rgb_to_hex(rgb_tuple):
        """Convert RGB tuple to hex color"""
        return f"#{rgb_tuple[0]:02x}{rgb_tuple[1]:02x}{rgb_tuple[2]:02x}"
    
    def render_avatar_square():
        """Render avatar as a square with rounded corners"""
        canvas = tk.Canvas(demo_icon, width=40, height=40, bg=COLOR_PANEL_BG, 
                          highlightthickness=0, bd=0)
        canvas.pack(expand=True, fill=tk.BOTH)
        
        # Draw rounded rectangle
        draw_rounded_rectangle(canvas, 2, 2, 38, 38, 8, 
                             fill=COLOR_PRIMARY, outline=COLOR_PRIMARY)
        
        # Add text
        canvas.create_text(20, 20, text="D4", font=("Arial", 12, "bold"), 
                          fill=COLOR_TEXT_LIGHT)
    
    # Render avatar
    render_avatar_square()
    
    # Create sample charts
    def create_sample_chart(parent, title):
        """Create a sample chart"""
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor(COLOR_PANEL_BG)
        ax.set_facecolor(COLOR_PANEL_BG)
        
        # Sample data
        categories = ['Project A', 'Project B', 'Project C', 'Project D']
        values = [30, 45, 25, 60]
        colors = [COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_INFO]
        
        bars = ax.bar(categories, values, color=colors)
        ax.set_title(title, color=COLOR_TEXT_LIGHT, fontsize=14, fontweight='bold')
        ax.set_xlabel('Projects', color=COLOR_TEXT_LIGHT)
        ax.set_ylabel('Progress (%)', color=COLOR_TEXT_LIGHT)
        
        # Style the chart
        ax.tick_params(colors=COLOR_TEXT_LIGHT)
        ax.spines['bottom'].set_color(COLOR_TEXT_MUTED_DARK_BG)
        ax.spines['top'].set_color(COLOR_TEXT_MUTED_DARK_BG)
        ax.spines['left'].set_color(COLOR_TEXT_MUTED_DARK_BG)
        ax.spines['right'].set_color(COLOR_TEXT_MUTED_DARK_BG)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{value}%', ha='center', va='bottom', color=COLOR_TEXT_LIGHT)
        
        plt.tight_layout()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
    
    # Create charts
    create_sample_chart(left_chart_panel, "Project Progress")
    create_sample_chart(right_chart_panel, "Task Distribution")
    
    def refresh_dashboard():
        """Refresh dashboard data"""
        # Update status boxes with real data
        total_projects = len(agent_data.get("data", []))
        active_jobs = sum(1 for project in agent_data.get("data", []) 
                         for job in project.get("jobs", []) 
                         if job.get("status") == "In Progress")
        completed_jobs = sum(1 for project in agent_data.get("data", []) 
                           for job in project.get("jobs", []) 
                           if job.get("status") == "Completed")
        failed_jobs = sum(1 for project in agent_data.get("data", []) 
                         for job in project.get("jobs", []) 
                         if job.get("status") == "Failed")
        
        # Update status box values
        status_boxes[0]["value"].config(text=str(total_projects))
        status_boxes[1]["value"].config(text=str(active_jobs))
        status_boxes[2]["value"].config(text=str(completed_jobs))
        status_boxes[3]["value"].config(text=str(failed_jobs))
        
        # Update tree page if it exists
        if "Tree" in pages:
            update_tree_page(agent_data)
    
    def update_status_boxes(new_agent_data):
        """Update status boxes with new data"""
        total_projects = len(new_agent_data.get("data", []))
        active_jobs = sum(1 for project in new_agent_data.get("data", []) 
                         for job in project.get("jobs", []) 
                         if job.get("status") == "In Progress")
        completed_jobs = sum(1 for project in new_agent_data.get("data", []) 
                           for job in project.get("jobs", []) 
                           if job.get("status") == "Completed")
        failed_jobs = sum(1 for project in new_agent_data.get("data", []) 
                         for job in project.get("jobs", []) 
                         if job.get("status") == "Failed")
        
        status_boxes[0]["value"].config(text=str(total_projects))
        status_boxes[1]["value"].config(text=str(active_jobs))
        status_boxes[2]["value"].config(text=str(completed_jobs))
        status_boxes[3]["value"].config(text=str(failed_jobs))
    
    def update_project_page(new_agent_data):
        """Update project page with new data"""
        if "Project" in pages:
            pages["Project"].load_project_data(new_agent_data)
    
    def update_job_page(new_agent_data):
        """Update job page with new data"""
        if "Job" in pages:
            pages["Job"].load_jobs_from_agent_data(new_agent_data)
    
    def update_charts(new_agent_data):
        # Redraw the main dashboard chart with new data
        # This assumes you have a reference to the chart widget/figure
        pass
    
    def update_tree_page(new_agent_data):
        """Update tree page with new data"""
        if "Tree" in pages:
            pages["Tree"].update_agent_data(new_agent_data)
    
    def update_test_cases_page_token(new_token):
        """Update test cases page with new token"""
        if "TestCases" in pages:
            pages["TestCases"].update_token(new_token)
    
    # Project page
    project_page = ProjectPage(content_frame, switch_page, 
                             {"title": ("Arial", 16, "bold"), "subtitle": ("Arial", 12)},
                             agent_data.get("data", []), token=agent_data.get("token"), base_url=base_url)
    project_page.grid(row=0, column=0, sticky="nsew")
    pages["Project"] = project_page
    
    # Job page
    job_page = JobPage(content_frame, switch_page)
    job_page.grid(row=0, column=0, sticky="nsew")
    pages["Job"] = job_page
    
    # Report page
    report_page = ReportPage(content_frame, switch_page, 
                           {"title": ("Arial", 16, "bold"), "subtitle": ("Arial", 12)},
                           agent_data.get("data", []), base_url, agent_data.get("agent_id"), token=agent_data.get("token"))
    report_page.grid(row=0, column=0, sticky="nsew")
    pages["Report"] = report_page
    
    # Tree page
    tree_page = TreePage(content_frame, switch_page, agent_data, base_url, agent_data.get("token"))
    tree_page.grid(row=0, column=0, sticky="nsew")
    pages["Tree"] = tree_page
    
    # Test cases page
    test_cases_page = TestCasesPage(content_frame, switch_page, base_url, pages, token=agent_data.get("token"))
    test_cases_page.grid(row=0, column=0, sticky="nsew")
    pages["TestCases"] = test_cases_page
    
    # Test case options page
    test_case_options_page = TestCaseOptionsPage(content_frame, switch_page, pages, base_url)
    test_case_options_page.grid(row=0, column=0, sticky="nsew")
    pages["TestCaseOptions"] = test_case_options_page
    
    # Download page
    download_page = DownloadPage(content_frame, base_url, switch_page, token=agent_data.get("token"))
    download_page.grid(row=0, column=0, sticky="nsew")
    pages["Download"] = download_page
    
    # Initially show dashboard
    switch_page("Dashboard")
    
    # Load initial data
    job_page.load_jobs_from_agent_data(agent_data)
    
    # Start animations
    start_animations()
    
    # Start the main loop
    root.mainloop()

# Rest of the classes and functions would go here...
# (This is a simplified version to fix the indentation issue)

if __name__ == "__main__":
    # Sample data for testing
    sample_data = {
        "data": [],
        "token": "sample_token",
        "agent_id": "sample_agent_id"
    }
    start_dashboard(sample_data, "http://localhost:8000") 