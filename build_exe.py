#!/usr/bin/env python3
"""
Build script to create a standalone executable for Google Maps Lead Scraper.
This creates a single .exe file that can be run on any Windows machine.
"""

import subprocess
import sys
import os
import shutil

def build_executable():
    """Build the standalone executable using PyInstaller."""
    
    print("🚀 Building Google Maps Lead Scraper Executable...")
    print("=" * 60)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✅ PyInstaller found")
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller installed")
    
    # Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
        print("🗑️ Cleaned previous build")
    
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",  # Create a single executable file
        "--windowed",  # No console window (GUI only)
        "--name", "GoogleMapsLeadScraper",
        "--icon=icon.ico" if os.path.exists("icon.ico") else "",
        "--add-data", "requirements.txt;.",
        "--hidden-import", "selenium",
        "--hidden-import", "webdriver_manager",
        "--hidden-import", "pandas",
        "main.py"
    ]
    
    # Remove empty icon parameter if no icon file
    cmd = [arg for arg in cmd if arg]
    
    print(f"🔧 Running: {' '.join(cmd)}")
    
    try:
        # Run PyInstaller for main app
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Main app build completed successfully!")
        
        # Build launcher executable
        print("\n🔨 Building professional launcher...")
        launcher_cmd = [
            "pyinstaller",
            "--onefile",
            "--windowed",
            "--name", "GoogleMapsLeadScraper_Launcher",
            "--icon=icon.ico" if os.path.exists("icon.ico") else "",
            "--hidden-import", "tkinter",
            "launcher.py"
        ]
        
        # Remove empty icon parameter if no icon file
        launcher_cmd = [arg for arg in launcher_cmd if arg]
        
        launcher_result = subprocess.run(launcher_cmd, check=True, capture_output=True, text=True)
        print("✅ Launcher build completed successfully!")
        
        # Check if executables were created
        exe_path = os.path.join("dist", "GoogleMapsLeadScraper.exe")
        launcher_path = os.path.join("dist", "GoogleMapsLeadScraper_Launcher.exe")
        
        if os.path.exists(exe_path) and os.path.exists(launcher_path):
            main_size = os.path.getsize(exe_path) / (1024 * 1024)  # Size in MB
            launcher_size = os.path.getsize(launcher_path) / (1024 * 1024)  # Size in MB
            
            print(f"\n📦 Main executable: {exe_path}")
            print(f"📏 File size: {main_size:.1f} MB")
            print(f"\n📦 Launcher executable: {launcher_path}")
            print(f"📏 File size: {launcher_size:.1f} MB")
            
            print("\n🎉 SUCCESS! Both executables are ready for distribution.")
            print("\n📋 Instructions for non-technical users:")
            print("1. Copy both .exe files to any Windows computer")
            print("2. Double-click 'GoogleMapsLeadScraper_Launcher.exe' for professional startup")
            print("3. Or double-click 'GoogleMapsLeadScraper.exe' for direct launch")
            print("4. No Python installation required!")
            print("\n⚠️ Note: The first run may take longer as Chrome driver downloads.")
        else:
            print("❌ Executable not found in dist folder")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print("\nError output:")
        print(e.stderr)
        return False
    
    return True

def create_distribution_package():
    """Create a complete distribution package."""
    
    if not os.path.exists("dist/GoogleMapsLeadScraper.exe"):
        print("❌ Executable not found. Run build first.")
        return
    
    # Create distribution folder
    dist_folder = "GoogleMapsLeadScraper_Distribution"
    if os.path.exists(dist_folder):
        shutil.rmtree(dist_folder)
    
    os.makedirs(dist_folder)
    
    # Copy executable
    shutil.copy2("dist/GoogleMapsLeadScraper.exe", dist_folder)
    
    # Create instruction file
    instructions = """
Google Maps Lead Scraper - User Instructions
==========================================

📋 What this tool does:
This application helps you find businesses that don't have established websites - perfect for outreach campaigns!

🚀 How to run:
1. Double-click "GoogleMapsLeadScraper.exe"
2. Wait for the application to load (first run may take a minute)
3. Fill in the search fields:
   - Business Type: e.g., "nail salons", "barbershops", "massage therapy"
   - City: e.g., "Nashville", "Miami", "Los Angeles"
   - Max Businesses: How many to search (25 is a good starting point)
4. Click "Find Leads" and wait for results
5. Click "Save to CSV" to export your leads

✅ What makes a good lead:
• Businesses with no website (just phone/address)
• Businesses using only Instagram
• Businesses using booking platforms like Squarespace or Booksy

❌ What gets filtered out:
• Businesses with established websites
• Large chains with corporate sites

💡 Tips for better results:
• Try different business types (service businesses work best)
• Search smaller cities for higher success rates
• Look for businesses that rely on word-of-mouth

🔧 System Requirements:
• Windows 10 or newer
• Internet connection
• Chrome browser (will be installed automatically if needed)

📞 Need help?
Contact the person who provided this tool for support.

==========================================
Built with ❤️ for lead generation success!
"""
    
    with open(os.path.join(dist_folder, "README.txt"), "w") as f:
        f.write(instructions)
    
    print(f"📦 Distribution package created: {dist_folder}/")
    print("🎁 Ready to share with non-technical users!")

if __name__ == "__main__":
    print("Google Maps Lead Scraper - Build Tool")
    print("=" * 40)
    
    choice = input("Choose option:\n1. Build executable\n2. Create distribution package\n3. Both\nChoice (1-3): ")
    
    if choice in ["1", "3"]:
        success = build_executable()
        if not success:
            sys.exit(1)
    
    if choice in ["2", "3"]:
        create_distribution_package()
    
    print("\n✅ All tasks completed!") 