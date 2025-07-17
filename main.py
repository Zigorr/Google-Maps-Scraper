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
        
        # Progress bar
        self.progress = ttk.Progressbar(progress_frame, mode='indeterminate')
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
        
        # Start progress animation
        self.progress.start()
        self.status_var.set("Initializing search...")
        
        # Start search in separate thread
        search_thread = threading.Thread(target=self.run_search, daemon=True)
        search_thread.start()
    
    def run_search(self):
        """Run the search in a separate thread."""
        try:
            keyword = self.keyword_var.get().strip()
            city = self.city_var.get().strip()
            max_businesses = int(self.max_businesses_var.get())
            
            # Update status
            self.root.after(0, lambda: self.status_var.set(f"Searching for {keyword} in {city}..."))
            
            # Initialize scraper
            self.scraper = LeadScraper(headless=True)  # Use headless mode for GUI
            
            # Run the search with custom progress updates
            self.root.after(0, lambda: self.status_var.set("Opening browser..."))
            
            # Redirect output to capture progress
            import io
            import sys
            
            # Capture output
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
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
            # Handle errors
            self.root.after(0, lambda: self.handle_search_error(str(e)))
        finally:
            # Clean up
            if self.scraper:
                self.scraper.close()
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
📝 Notes: {lead['notes']}

"""
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
        """Save the qualified leads to a CSV file."""
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
                    'IG found?': 'Yes' if lead['instagram_found'] else 'No',
                    'Squarespace link found?': 'Yes' if lead['squarespace_found'] else 'No', 
                    'Booksy link found?': 'Yes' if lead['booksy_found'] else 'No',
                    'Qualification Reason': lead['qualification_reason'],
                    'Notes': lead['notes']
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