import tkinter
from tkinter import filedialog
import customtkinter
from PIL import Image, ImageTk  # Import Pillow modules
from pytube import YouTube 
import requests
import threading
import string


# Global variables to control download status
is_paused = is_cancelled = False
thumbnail_image = None  # Store the thumbnail image


def start_download():
    url=link.get()
    try:
        video=YouTube(url)
        title_text = video.title
        valid_characters = "-_.() %s%s" % (string.ascii_letters, string.digits)
        title_text = ''.join(char if char in valid_characters else '_' for char in title_text)

        save_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")],initialfile=title_text)
        if not save_path:
            return
        title.configure(text=video.title,text_color="white")
        threading.Thread(target=download_video, args=(video,save_path), daemon=True).start()
    except:
        title.configure(text="Invalid Youtube Link", text_color="red")

def download_video(video,save_path):
    global is_paused, is_cancelled
    link.configure(state="disabled")
    download_button.configure(state= "disabled") 
    pause_button.pack(pady=10)
    stop_button.pack()
    try:
        finishLabel.configure(text="Connecting...",text_color="white")
        stream = video.streams.get_highest_resolution()
        filesize = stream.filesize_mb  # get the video size
        with open(save_path, 'wb') as f:
            is_paused = is_cancelled = False
            downloaded = 0
            response = requests.get(stream.url, stream=True)
            for chunk in response.iter_content(chunk_size=1024*1024):
                if is_cancelled:
                    finishLabel.configure(text='Download cancelled',text_color="white")
                    break
                if is_paused:
                    continue
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    megabytes_downloaded = downloaded / (1024 * 1024)
                    on_progress(filesize, megabytes_downloaded)
                else:
                    # no more data
                    finishLabel.configure(text='Download completed',text_color="green")
                    break
    except Exception as e:
        finishLabel.configure(text=f"Error: {str(e)}", text_color="red")        
    finally:
        # Reset the download status when the download is complete
        link.configure(state="normal")
        download_button.configure(state= "normal") 
        pause_button.pack_forget()
        stop_button.pack_forget()
        
  
# Function to stop the download (called when the "Stop" button is pressed)
def toggle_download():
    global is_paused
    is_paused = not is_paused
    pause_button.configure(text= 'Resume' if is_paused else 'Pause')

def cancel_download():
    global is_cancelled
    is_cancelled = True
    progressBar.set(0)
    pPercentage.configure(text='0'+'%')

def on_progress(filesize,megabytes_downloaded):
    percentage_completed = (megabytes_downloaded / filesize) * 100
    per=str(int(round(percentage_completed)))
    finishLabel.configure(text=f'Downloaded {megabytes_downloaded:.2f} MB / {filesize} MB', text_color="white")
    pPercentage.configure(text=per+'%')
    #Update progress bar
    progressBar.set(float(percentage_completed) / 100)


def on_url_var_change(*args):
    # This function will be called whenever the value of url_var changes
    try:
        new_url = url_var.get()
        video=YouTube(new_url)
        title.configure(text=video.title,text_color="white")
        download_button.configure(state= "normal") 
        load_and_display_thumbnail(video.thumbnail_url)

    except:
        title.configure(text="Invalid Youtube Link", text_color="red")
        download_button.configure(state= "disabled") 
        thumbnail_label.grid_forget()


# Function to load and display the video thumbnail
def load_and_display_thumbnail(thumbnail_url):
    global thumbnail_image
    response = requests.get(thumbnail_url, stream=True)
    thumbnail_image = Image.open(response.raw).resize((300, 150), Image.LANCZOS )  # Resize the thumbnail

    # Create a PhotoImage from the Pillow image
    thumbnail_photo = ImageTk.PhotoImage(thumbnail_image)
    # Display the thumbnail image in a Label widget
    thumbnail_label.configure(image=thumbnail_photo)
    thumbnail_label.image = thumbnail_photo  # Keep a reference
    thumbnail_label.grid(row=1,column=1)

def toggle_advanced_options():
    if advanced_options_frame.winfo_ismapped():
        advanced_options_frame.grid_forget()
    else:
        advanced_options_frame.grid(row=1, column=0, padx=10, pady=10)



# System Settings
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("green")


# Our app frame
app= customtkinter.CTk()
app.geometry("720x480")
app.title("Youtube Donwloader")

#Adding UI Elements
title=customtkinter.CTkLabel(app,text="Insert a youtube link")
title.pack(padx=10,pady=10)


#Link input
url_var=tkinter.StringVar()
url_var.trace_add("write", on_url_var_change)
link=customtkinter.CTkEntry(app,width=350,height=40,textvariable=url_var)
link.pack()

#Thumbnail frame
frame = customtkinter.CTkFrame(app,border_width=0,fg_color='transparent')
frame.pack(side=customtkinter.TOP)
# Thumbnail Label
thumbnail_label =tkinter.Label(frame,borderwidth=0,highlightthickness=0)
thumbnail_label.grid(row=0,column=0,pady=10)

# Create a button to toggle advanced options
advanced_button =customtkinter.CTkButton(frame, text="Advanced Options", command=toggle_advanced_options)
advanced_button.grid(row=0, column=0, padx=10, pady=10)

# Create a frame to hold the advanced options (initially hidden)
advanced_options_frame = customtkinter.CTkFrame(frame)
#advanced_options_frame.grid(row=1, column=0, padx=10, pady=10, sticky="w")


# Create Combobox for selecting video format within the advanced options
format_label = customtkinter.CTkLabel(advanced_options_frame, text="Select Format:")
format_label.grid(row=0, column=0, padx=5, pady=5)
formats = ["MP4", "AVI", "MKV", "FLV"]
format_combobox = customtkinter.CTkComboBox(advanced_options_frame, values=formats)
format_combobox.grid(row=0, column=1, padx=5, pady=5)
format_combobox.set(formats[0])  # Set default format



#Finished Donwloading
finishLabel=customtkinter.CTkLabel(app,text="")
finishLabel.pack()


#Progress percentage
pPercentage=customtkinter.CTkLabel(app,text="0%")
pPercentage.pack()

#Progress Bar
progressBar=customtkinter.CTkProgressBar(app,width=400)
progressBar.set(0)
progressBar.pack(padx=10,pady=10)

#Download Button
download_button=customtkinter.CTkButton(app,text="Download",command=start_download)
download_button.pack()

# Create a "Stop" button
stop_button = customtkinter.CTkButton(app, text="Stop", command=cancel_download,fg_color="red")
pause_button = customtkinter.CTkButton(app, text="Pause", command=toggle_download,fg_color="blue")




#Run app
app.mainloop()


#Command used for releasing .exe file
# pyinstaller --name YTDownloader --onefile --windowed tes.py