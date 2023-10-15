import os
import requests
import zipfile
import shutil
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from pytube import YouTube
import pyautogui

# Define the URL of your GitHub repository
GITHUB_REPO_URL = "https://github.com/your_username/your_repository"

# Create the main application window
app = tk.Tk()
app.title("YouTube Video Downloader")

# Function to download a YouTube video
def download_video():
    try:
        url = url_entry.get()
        save_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")])
        if url and save_path:
            yt = YouTube(url)
            stream = yt.streams.get_highest_resolution()
            stream.download(output_path=save_path)
            status_label.config(text="Download completed.")
    except Exception as e:
        status_label.config(text=f"Error: {str(e)}")

# Function to check for updates and install them
def check_and_install_update():
    try:
        # Define the GitHub release URL
        github_release_url = f"{GITHUB_REPO_URL}/releases/latest"
        
        # Get the latest release information
        response = requests.get(github_release_url)
        release_data = response.json()
        tag_name = release_data["tag_name"]
        
        # Define the download URL for the update package
        update_package_url = f"{GITHUB_REPO_URL}/releases/download/{tag_name}/update.zip"
        
        # Download the update package
        update_package_path = "update.zip"
        response = requests.get(update_package_url)
        with open(update_package_path, "wb") as f:
            f.write(response.content)
        
        # Extract the update package
        with zipfile.ZipFile(update_package_path, "r") as zip_ref:
            zip_ref.extractall("temp_update")
        
        # Replace the old application EXE with the updated one
        old_exe = "your_app.exe"  # Replace with your old EXE filename
        new_exe = "temp_update/your_app.exe"  # Replace with your new EXE filename
        shutil.move(new_exe, old_exe)
        
        # Clean up temporary files and directories
        os.remove(update_package_path)
        shutil.rmtree("temp_update")
        
        # Restart the updated application
        pyautogui.hotkey("ctrl", "c")  # Copy the script
        pyautogui.hotkey("ctrl", "v")  # Paste and run the updated script
        
    except Exception as e:
        status_label.config(text=f"Error: {str(e)}")

# Create and configure UI elements
url_label = ttk.Label(app, text="Enter YouTube URL:")
url_label.pack(pady=10)
url_entry = ttk.Entry(app, width=50)
url_entry.pack()
download_button = ttk.Button(app, text="Download", command=download_video)
download_button.pack(pady=10)
status_label = ttk.Label(app, text="")
status_label.pack()
update_button = ttk.Button(app, text="Check for Updates", command=check_and_install_update)
update_button.pack(pady=10)

# Start the application
app.mainloop()
