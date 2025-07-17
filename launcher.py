#!/usr/bin/env python3
"""
Professional Launcher for Google Maps Lead Scraper
Launches the GUI application without showing terminal window
"""

import sys
import os
import subprocess
import tkinter as tk
from tkinter import messagebox
import threading
import time

class LauncherGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Google Maps Lead Scraper - Starting...")
        self.root.geometry("400x200")
        self.root.resizable(False, False)
        
        # Center the window
        self.root.eval('tk::PlaceWindow . center')
        
        # Configure style
        self.root.configure(bg='#f0f0f0')
        
        # Create loading interface
        self.create_loading_interface()
        
        # Start the main application in a separate thread
        self.launch_thread = threading.Thread(target=self.launch_main_app, daemon=True)
        self.launch_thread.start()
    
    def create_loading_interface(self):
        """Create a professional loading interface."""
        # Title
        title_label = tk.Label(
            self.root,
            text="🗺️ Google Maps Lead Scraper",
            font=("Arial", 16, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        title_label.pack(pady=20)
        
        # Status
        self.status_label = tk.Label(
            self.root,
            text="Starting application...",
            font=("Arial", 10),
            bg='#f0f0f0',
            fg='#7f8c8d'
        )
        self.status_label.pack(pady=10)
        
        # Progress bar (simple animated dots)
        self.progress_label = tk.Label(
            self.root,
            text="●○○",
            font=("Arial", 12),
            bg='#f0f0f0',
            fg='#3498db'
        )
        self.progress_label.pack(pady=10)
        
        # Start progress animation
        self.animate_progress()
    
    def animate_progress(self):
        """Animate the progress indicator."""
        patterns = ["●○○", "○●○", "○○●", "○●○"]
        current = getattr(self, 'progress_index', 0)
        
        self.progress_label.config(text=patterns[current])
        self.progress_index = (current + 1) % len(patterns)
        
        # Continue animation if window still exists
        if self.root.winfo_exists():
            self.root.after(500, self.animate_progress)
    
    def launch_main_app(self):
        """Launch the main application."""
        try:
            # Update status
            self.root.after(0, lambda: self.status_label.config(text="Initializing components..."))
            time.sleep(1)
            
            # Check if main.py exists
            if not os.path.exists("main.py"):
                self.root.after(0, self.show_error, "main.py not found in current directory")
                return
            
            self.root.after(0, lambda: self.status_label.config(text="Loading scraper engine..."))
            time.sleep(1)
            
            # Import and run the main application
            try:
                import main
                self.root.after(0, self.close_launcher)
                main.main()  # This will start the GUI
            except ImportError as e:
                self.root.after(0, self.show_error, f"Failed to import main application: {e}")
            except Exception as e:
                self.root.after(0, self.show_error, f"Failed to start application: {e}")
                
        except Exception as e:
            self.root.after(0, self.show_error, f"Unexpected error: {e}")
    
    def close_launcher(self):
        """Close the launcher window."""
        try:
            self.root.destroy()
        except:
            pass
    
    def show_error(self, message):
        """Show error message and close."""
        messagebox.showerror("Launch Error", message)
        self.root.destroy()
    
    def run(self):
        """Start the launcher."""
        self.root.mainloop()

def main():
    """Main function to run the launcher."""
    try:
        launcher = LauncherGUI()
        launcher.run()
    except Exception as e:
        # Fallback error handling
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        messagebox.showerror("Critical Error", f"Failed to start launcher: {e}")
        root.destroy()

if __name__ == "__main__":
    main() 