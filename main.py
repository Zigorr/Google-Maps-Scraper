#!/usr/bin/env python3
"""
Google Maps Lead Scraper - GUI Application
User-friendly interface for non-technical users to find business leads.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import time
import csv
import os
from datetime import datetime
from lead_scraper import LeadScraper


class GoogleMapsLeadScraperGUI:
    """
    User-friendly GUI application for Google Maps lead generation.
    Designed for non-technical users.
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Google Maps Lead Scraper")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Initialize variables
        self.scraper = None
        self.current_results = None
        self.is_searching = False
        
        # Create the GUI
        self.create_widgets()
        
        # Center the window
        self.center_window()
    
    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Create all GUI widgets."""
        
        # Title
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            title_frame, 
            text="🎯 Google Maps Lead Scraper", 
            font=("Arial", 16, "bold")
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Find businesses without websites for your outreach campaigns",
            font=("Arial", 10)
        )
        subtitle_label.pack()
        
        # Main input frame
        input_frame = ttk.LabelFrame(self.root, text="Search Settings", padding="15")
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Keyword input
        ttk.Label(input_frame, text="Business Type:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.keyword_var = tk.StringVar()
        self.keyword_entry = ttk.Entry(input_frame, textvariable=self.keyword_var, width=40)
        self.keyword_entry.grid(row=0, column=1, padx=(10, 0), pady=5, sticky=tk.W)
        ttk.Label(input_frame, text="(e.g., nail salons, barbershops, massage therapy)", 
                 font=("Arial", 8), foreground="gray").grid(row=0, column=2, padx=10, sticky=tk.W)
        
        # City input
        ttk.Label(input_frame, text="City:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.city_var = tk.StringVar()
        self.city_entry = ttk.Entry(input_frame, textvariable=self.city_var, width=40)
        self.city_entry.grid(row=1, column=1, padx=(10, 0), pady=5, sticky=tk.W)
        ttk.Label(input_frame, text="(e.g., Nashville, Miami, Los Angeles)", 
                 font=("Arial", 8), foreground="gray").grid(row=1, column=2, padx=10, sticky=tk.W)
        
        # Max businesses
        ttk.Label(input_frame, text="Max Businesses:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.max_businesses_var = tk.StringVar(value="50")
        max_spinbox = ttk.Spinbox(input_frame, from_=5, to=100, textvariable=self.max_businesses_var, width=10)
        max_spinbox.grid(row=2, column=1, padx=(10, 0), pady=5, sticky=tk.W)
        ttk.Label(input_frame, text="(Higher numbers take longer but find more leads)", 
                 font=("Arial", 8), foreground="gray").grid(row=2, column=2, padx=10, sticky=tk.W)
        
        # Action buttons frame
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=tk.X)
        
        # Find Leads button
        self.search_button = ttk.Button(
            button_frame, 
            text="🔍 Find Leads", 
            command=self.start_search,
            style="Accent.TButton"
        )
        self.search_button.pack(side=tk.LEFT, padx=5)
        
        # Stop button (initially disabled)
        self.stop_button = ttk.Button(
            button_frame,
            text="⏹️ Stop Search",
            command=self.stop_search,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Export button (initially disabled)
        self.export_button = ttk.Button(
            button_frame,
            text="💾 Save to CSV",
            command=self.export_results,
            state=tk.DISABLED
        )
        self.export_button.pack(side=tk.RIGHT, padx=5)
        
        # Clear results button
        self.clear_button = ttk.Button(
            button_frame,
            text="🗑️ Clear Results",
            command=self.clear_results,
            state=tk.DISABLED
        )
        self.clear_button.pack(side=tk.RIGHT, padx=5)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(self.root, text="Progress", padding="10")
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Progress bar (determinate mode for better tracking)
        self.progress = ttk.Progressbar(progress_frame, mode='determinate', maximum=100)
        self.progress.pack(fill=tk.X, pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to search")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.pack()
        
        # Results frame
        results_frame = ttk.LabelFrame(self.root, text="Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Results text area
        self.results_text = scrolledtext.ScrolledText(
            results_frame, 
            wrap=tk.WORD, 
            height=15,
            font=("Consolas", 9)
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        self.show_instructions()
    
    def show_instructions(self):
        """Show initial instructions in the results area."""
        instructions = """📋 Welcome to Google Maps Lead Scraper!

🎯 This tool helps you find businesses that don't have established websites - perfect for outreach!

📝 How to use:
1. Enter the type of business you want to find (e.g., "nail salons", "barbershops")
2. Enter the city you want to search in
3. Click "Find Leads" and wait for results
4. Click "Save to CSV" to export your leads

✅ What makes a good lead:
• Businesses with no website (just phone/address)
• Businesses using only Instagram for their online presence
• Businesses using booking platforms like Squarespace or Booksy instead of real websites

❌ What gets filtered out:
• Businesses with established websites (like business-name.com)
• Large chains with corporate websites

🚀 Ready to find some leads? Fill in the search fields above and click "Find Leads"!
"""
        self.results_text.insert(tk.END, instructions)
    
    def validate_inputs(self):
        """Validate user inputs before starting search."""
        keyword = self.keyword_var.get().strip()
        city = self.city_var.get().strip()
        
        if not keyword:
            messagebox.showerror("Error", "Please enter a business type (e.g., 'nail salons')")
            return False
        
        if not city:
            messagebox.showerror("Error", "Please enter a city name")
            return False
        
        try:
            max_businesses = int(self.max_businesses_var.get())
            if max_businesses < 1 or max_businesses > 100:
                messagebox.showerror("Error", "Max businesses must be between 1 and 100")
                return False
        except ValueError:
            messagebox.showerror("Error", "Max businesses must be a number")
            return False
        
        return True
    
    def update_progress(self, current, total, status):
        """Update progress bar and status with ETA calculation."""
        if total > 0:
            progress = (current / total) * 100
            self.progress['value'] = progress
            
            # Calculate ETA if we have started processing
            if hasattr(self, 'start_time') and current > 0:
                elapsed = time.time() - self.start_time
                rate = current / elapsed  # businesses per second
                remaining = total - current
                eta_seconds = remaining / rate if rate > 0 else 0
                
                # Format ETA
                if eta_seconds > 60:
                    eta_str = f"{int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
                else:
                    eta_str = f"{int(eta_seconds)}s"
                
                # Update status with ETA
                self.status_var.set(f"{status} ({current}/{total}) - ETA: {eta_str}")
            else:
                self.status_var.set(status)
        
        self.root.update_idletasks()

    def start_search(self):
        """Start the lead search process."""
        if not self.validate_inputs():
            return
        
        if self.is_searching:
            messagebox.showwarning("Warning", "Search is already in progress")
            return
        
        # Clear previous results
        self.clear_results()
        
        # Update UI state
        self.is_searching = True
        self.search_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.export_button.config(state=tk.DISABLED)
        self.clear_button.config(state=tk.DISABLED)
        
        # Initialize progress tracking
        self.progress['value'] = 0
        self.status_var.set("Initializing search...")
        self.start_time = time.time()
        
        # Start search in separate thread
        search_thread = threading.Thread(target=self.run_search, daemon=True)
        search_thread.start()
    
    def run_search(self):
        """Run the search in a separate thread."""
        try:
            keyword = self.keyword_var.get().strip()
            city = self.city_var.get().strip()
            max_businesses = int(self.max_businesses_var.get())
            
            # Update status with more detailed progress
            self.root.after(0, lambda: self.status_var.set(f"Preparing to search for {keyword} in {city}..."))
            time.sleep(0.5)  # Brief pause for UI update
            
            # Initialize scraper with progress feedback
            self.root.after(0, lambda: self.status_var.set("Starting browser (this may take 30-60 seconds)..."))
            self.root.after(0, lambda: self.progress.config(mode='indeterminate'))
            self.root.after(0, lambda: self.progress.start(10))
            
            # Progress callback for browser initialization
            def browser_progress(message):
                self.root.after(0, lambda: self.status_var.set(message))
            
            # Initialize scraper with progress callback and error handling
            try:
                self.scraper = LeadScraper(headless=True, progress_callback=browser_progress)
            except Exception as e:
                # Handle browser startup failure
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.progress.config(mode='determinate'))
                self.root.after(0, lambda: self.progress.config(value=0))
                
                error_msg = str(e)
                if "timed out" in error_msg.lower():
                    error_msg = "Browser startup timed out. Please close any Chrome windows and try again."
                elif "chrome" in error_msg.lower():
                    error_msg = "Chrome browser failed to start. Please ensure Chrome is installed and try again."
                
                self.root.after(0, lambda: messagebox.showerror("Browser Error", error_msg))
                self.root.after(0, lambda: self.status_var.set("Browser failed to start"))
                return
            
            # Stop indeterminate progress and switch to determinate
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.progress.config(mode='determinate'))
            self.root.after(0, lambda: self.progress.config(value=0))
            
            # Run the search with enhanced progress monitoring
            self.root.after(0, lambda: self.status_var.set("Browser ready - starting search..."))
            
            # Enhanced output capture with real-time updates
            import io
            import sys
            
            # Create a custom output handler for real-time updates
            class ProgressCapture(io.StringIO):
                def __init__(self, gui_instance):
                    super().__init__()
                    self.gui = gui_instance
                    self.buffer = ""
                
                def write(self, text):
                    super().write(text)
                    self.buffer += text
                    
                    # Update GUI with key progress indicators
                    if "🔍 Searching for:" in text:
                        self.gui.root.after(0, lambda: self.gui.status_var.set("Searching Google Maps..."))
                    elif "📍 Processing" in text and "businesses..." in text:
                        self.gui.root.after(0, lambda: self.gui.status_var.set("Found businesses - starting data extraction..."))
                    elif "📊 Processing" in text and "/" in text:
                        # Extract progress from "📊 Processing 5/20 - 25.0%"
                        try:
                            parts = text.split("Processing ")[1].split(" - ")[0]
                            current, total = parts.split("/")
                            progress = (int(current) / int(total)) * 100
                            self.gui.root.after(0, lambda p=progress: self.gui.progress.config(value=p))
                            self.gui.root.after(0, lambda: self.gui.status_var.set(f"Extracting business data... ({current}/{total})"))
                        except:
                            pass
                    elif "✅ Scraping completed!" in text:
                        self.gui.root.after(0, lambda: self.gui.status_var.set("Scraping completed - analyzing results..."))
                    elif "🔄 Attempting to restart browser session" in text:
                        self.gui.root.after(0, lambda: self.gui.status_var.set("Browser session lost - attempting recovery..."))
                    elif "✅ Browser session recovered" in text:
                        self.gui.root.after(0, lambda: self.gui.status_var.set("Browser session recovered - continuing..."))
                    elif "❌ Browser disconnected" in text:
                        self.gui.root.after(0, lambda: self.gui.status_var.set("Browser connection issue - attempting recovery..."))
                    
                    return len(text)
            
            # Capture output with real-time updates
            old_stdout = sys.stdout
            captured_output = ProgressCapture(self)
            sys.stdout = captured_output
            
            try:
                results = self.scraper.find_leads(keyword, city, max_businesses)
                self.current_results = results
                
                # Restore stdout
                sys.stdout = old_stdout
                output = captured_output.getvalue()
                
                # Update UI with results
                self.root.after(0, lambda: self.display_results(results, output))
                
            finally:
                sys.stdout = old_stdout
                
        except Exception as e:
            # Handle errors with more detailed information
            error_details = str(e)
            if "Browser" in error_details or "WebDriver" in error_details:
                error_type = "Browser Error"
                user_message = f"Browser-related error occurred:\n{error_details}\n\nTry:\n• Closing all Chrome windows\n• Restarting the application\n• Checking your internet connection"
            elif "timeout" in error_details.lower():
                error_type = "Timeout Error"
                user_message = f"Operation timed out:\n{error_details}\n\nTry:\n• Using a different search term\n• Reducing max businesses\n• Checking your internet connection"
            else:
                error_type = "Search Error"
                user_message = f"An error occurred:\n{error_details}\n\nTry:\n• Different search terms\n• Checking your internet connection\n• Restarting the application"
            
            self.root.after(0, lambda: self.handle_search_error(user_message))
        finally:
            # Enhanced cleanup
            if self.scraper:
                try:
                    self.scraper.close()
                except:
                    pass
            self.root.after(0, self.search_completed)
    
    def display_results(self, results, output):
        """Display search results in the text area."""
        self.results_text.delete(1.0, tk.END)
        
        # Add summary
        summary = f"""🎯 SEARCH COMPLETE - {results['keyword']} in {results['city']}
⏰ Completed: {results['timestamp']}
📊 Total Businesses Found: {results['total_scraped']}
✅ Qualified Leads: {results['total_qualified']}
📈 Success Rate: {results['qualification_rate']:.1f}%

"""
        self.results_text.insert(tk.END, summary)
        
        if results['qualified_leads']:
            self.results_text.insert(tk.END, "🎯 QUALIFIED LEADS:\n" + "="*60 + "\n\n")
            
            for i, lead in enumerate(results['qualified_leads'], 1):
                lead_info = f"""Lead {i}: {lead['business_name']}
📞 Phone: {lead['phone']}
📍 Address: {lead['address']}
🏷️ Why qualified: {lead['qualification_reason']}
"""
                # Show what was found
                found_items = []
                if lead.get('instagram_found'):
                    found_items.append(f"Instagram (@{lead.get('instagram_handle', 'found')})")
                if lead.get('squarespace_found'):
                    found_items.append("Squarespace booking")
                if lead.get('booksy_found'):
                    found_items.append("Booksy booking")
                
                if found_items:
                    lead_info += f"🔗 Found: {', '.join(found_items)}\n"
                
                # Show notes if available
                if lead.get('notes'):
                    lead_info += f"📝 Notes: {lead['notes']}\n"
                
                lead_info += "\n"
                self.results_text.insert(tk.END, lead_info)
                
        else:
            self.results_text.insert(tk.END, """😔 No qualified leads found in this search.

💡 Try searching for:
• Different business types (hair salons, massage therapy, auto repair)
• Smaller cities or neighborhoods
• Service-based businesses rather than retail stores

""")
        
        # Add detailed output at the end
        self.results_text.insert(tk.END, "\n" + "="*60 + "\n")
        self.results_text.insert(tk.END, "📊 DETAILED SEARCH LOG:\n")
        self.results_text.insert(tk.END, "="*60 + "\n")
        self.results_text.insert(tk.END, output)
        
        # Scroll to top
        self.results_text.see(1.0)
        
        # Enable export button if we have results
        if results['qualified_leads']:
            self.export_button.config(state=tk.NORMAL)
            self.status_var.set(f"Found {results['total_qualified']} qualified leads! Click 'Save to CSV' to export.")
        else:
            self.status_var.set("Search complete - no qualified leads found.")
    
    def handle_search_error(self, error_message):
        """Handle search errors."""
        self.results_text.delete(1.0, tk.END)
        error_text = f"""❌ Search Error

An error occurred during the search:
{error_message}

💡 Common solutions:
• Make sure you have an internet connection
• Try a different search (simpler business type or different city)
• Check that Chrome browser is installed
• Close other browser windows that might interfere

Contact support if the problem persists.
"""
        self.results_text.insert(tk.END, error_text)
        self.status_var.set("Search failed - see error message above")
        messagebox.showerror("Search Error", f"Search failed: {error_message}")
    
    def stop_search(self):
        """Stop the current search."""
        if self.scraper:
            self.scraper.close()
        self.is_searching = False
        self.search_completed()
        self.status_var.set("Search stopped by user")
    
    def search_completed(self):
        """Reset UI after search completion."""
        self.is_searching = False
        self.progress.stop()
        self.search_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.clear_button.config(state=tk.NORMAL)
    
    def clear_results(self):
        """Clear the results area."""
        self.results_text.delete(1.0, tk.END)
        self.current_results = None
        self.export_button.config(state=tk.DISABLED)
        self.clear_button.config(state=tk.DISABLED)
        self.status_var.set("Results cleared - ready for new search")
        self.show_instructions()
    
    def export_results(self):
        """Export results to CSV file."""
        if not self.current_results or not self.current_results['qualified_leads']:
            messagebox.showwarning("Warning", "No qualified leads to export")
            return
        
        # Ask user where to save the file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"leads_{self.current_results['keyword'].replace(' ', '_')}_{self.current_results['city']}_{timestamp}.csv"
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=default_filename,
            title="Save leads to CSV file"
        )
        
        if not filename:
            return
        
        try:
            self.save_to_csv(filename)
            messagebox.showinfo("Success", f"Leads exported successfully to:\n{filename}")
            self.status_var.set(f"Exported {len(self.current_results['qualified_leads'])} leads to CSV")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export leads:\n{str(e)}")
    
    def save_to_csv(self, filename):
        """Save the qualified leads to a CSV file matching client requirements."""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Business Name',
                'Phone',
                'Address', 
                'IG found?',
                'Squarespace link found?',
                'Booksy link found?',
                'Qualification Reason',
                'Notes'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for lead in self.current_results['qualified_leads']:
                writer.writerow({
                    'Business Name': lead['business_name'],
                    'Phone': lead['phone'],
                    'Address': lead['address'],
                    'IG found?': 'Yes' if lead.get('instagram_found', False) else 'No',
                    'Squarespace link found?': 'Yes' if lead.get('squarespace_found', False) else 'No',
                    'Booksy link found?': 'Yes' if lead.get('booksy_found', False) else 'No',
                    'Qualification Reason': lead['qualification_reason'],
                    'Notes': lead.get('notes', '')
                })
    
    def on_closing(self):
        """Handle application closing."""
        if self.is_searching:
            if messagebox.askokcancel("Quit", "Search is in progress. Do you want to quit?"):
                if self.scraper:
                    self.scraper.close()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """Main function to run the GUI application."""
    root = tk.Tk()
    
    # Set the application icon (if available)
    try:
        root.iconbitmap('icon.ico')
    except:
        pass
    
    app = GoogleMapsLeadScraperGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    main() 