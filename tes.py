import tkinter
from tkinter import filedialog
import customtkinter
from PIL import Image, ImageTk  # Import Pillow modules
from pytube import YouTube 
from pytube.exceptions import RegexMatchError
import os 
import re

import requests
import threading


# Global variables to control download status
previous_video=None
video=None
is_cancelled = False
thumbnail_image = None  # Store the thumbnail image
# Define a threading event for pausing the download
pause_event = threading.Event()
video_info_thread = None


def sanitize_filename(title):
    # Allow letters, digits, and a few special characters
    # Replace characters that are not allowed in filenames with an underscore
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', title)

def start_download():
    global video
    try:
        title_text = sanitize_filename(video.title)

        save_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")],initialfile=title_text)
        if not save_path:
            return
        title.configure(text=video.title,text_color="white")
        threading.Thread(target=download_video, args=(save_path,), daemon=True).start()
    except:
        title.configure(text="Invalid Youtube Link", text_color="red")


def download_video(save_path):
    global is_cancelled,video
    link.configure(state="disabled")
    download_button.grid_remove()
    download_info_frame.grid(row=4, column=0,padx=10, pady=10)
    try:
        finishLabel.configure(text="Connecting...",text_color="white")
        file_extension=format_combobox.get()
        desired_resolution=quality_combobox.get().split(",")[0]
        desired_resolution = desired_resolution.split(":")[1] if "BestOption" in desired_resolution else desired_resolution
        #iF file is sound
        if "kbps" in desired_resolution:
            video.register_on_progress_callback(on_hmada)  
            save_path, file_name = os.path.split(save_path)
            desired_stream = video.streams.filter(abr=desired_resolution, file_extension=file_extension).first().download(filename=file_name,output_path=save_path)
            # save the file as mp3
            base, ext = os.path.splitext(desired_stream) 
            new_file = base + '.mp3'
            os.rename(desired_stream, new_file) 
        #if file is video
        else:
            buttons_frame.grid(row=3, column=0,columnspan=2, padx=5, pady=5)
            desired_stream = video.streams.filter(res=desired_resolution, file_extension=file_extension).first()
            print(file_extension,desired_resolution)
            filesize = desired_stream.filesize_mb  # get the video size
            with open(save_path, 'wb') as f:
                is_cancelled = False
                downloaded = 0
                response = requests.get(desired_stream.url, stream=True)
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if is_cancelled:
                        finishLabel.configure(text='Download cancelled',text_color="white")
                        break
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        megabytes_downloaded = downloaded / (1024 * 1024)
                        on_progress(filesize, megabytes_downloaded)
                    # Check the pause_event and pause download if set
                    if pause_event.is_set():
                        while pause_event.is_set():
                            # Sleep to avoid freezing the app
                            app.update()
    except Exception as e:
        finishLabel.configure(text=f"Error: {str(e)}", text_color="red")        
    finally:
        # Reset the download status when the download is complete
        link.configure(state="normal")
        download_button.grid()
        buttons_frame.grid_remove()
        finishLabel.configure(text='Download completed',text_color="green")



        
def on_hmada(stream, chunk, bytes_remaining):
    total_size = stream.filesize_mb
    bytes_downloaded = total_size - (bytes_remaining/(1024*1024))
    percentage_of_completion = bytes_downloaded / total_size * 100
    per = str(int(percentage_of_completion))
    pPercentage.configure(text=per + '%')
    finishLabel.configure(text=f'Downloaded {bytes_downloaded:.2f} MB / {total_size} MB', text_color="white")
    # Update progress bar
    progressBar.set(float(percentage_of_completion) / 100)



# Function to stop the download (called when the "Stop" button is pressed)
def toggle_download():
    # Toggle the pause_event to pause or resume the download
    if pause_event.is_set():
        pause_event.clear()
        pause_button.configure(text='Pause')
    else:
        pause_event.set()
        pause_button.configure(text='Resume')

def cancel_download():
    global is_cancelled
    pause_event.clear()
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
    global video_info_thread,video,previous_video
    # This function will be called whenever the value of url_var changes
    try:
        new_url = url_var.get()
        video=YouTube(new_url)
        title.configure(text=video.title,text_color="white")
        download_button.configure(state= "normal") 
        load_and_display_thumbnail(video.thumbnail_url)
        # Access available video streams
        if previous_video == None or previous_video.video_id !=video.video_id:
            video_info_thread = threading.Thread(target=get_video_info, args=(),daemon=True).start()
            #get_video_info()
            previous_video =video
    except RegexMatchError:
        title.configure(text="Invalid Youtube Link", text_color="red")
        download_button.configure(state= "disabled") 
        thumbnail_label.grid_remove()
        download_info_frame.grid_remove()



#https://www.youtube.com/watch?v=ML743nrkMHw&t=9s

def get_video_info():
    global video
    streams=video.streams
    # Print available formats and resolutions
    setting_formats(streams,"video")
    setting_quality(format_combobox.get())

def get_audio_info():
    global video
    # To get audio-only streams (without video):
    audio_streams = video.streams.filter(only_audio=True)
    setting_formats(audio_streams,"audio")
    setting_quality(format_combobox.get())
   

def setting_quality(format):
    print("iam here")
    global video
    qualitys=[]
    streams=video.streams
    stream_type=radio_var.get()
    if stream_type=="Video":
        specific_streams=streams.filter(file_extension=format,type="video", progressive=True)
        if format=="mp4":
            highest_resolution_mp4_stream = streams.filter(file_extension="mp4").get_highest_resolution()
            qualitys.append(f"BestOption:{highest_resolution_mp4_stream.resolution},FileSize={highest_resolution_mp4_stream.filesize/ (1024 * 1024):.2f} MB")
        for stream in specific_streams:
            print(stream)
            qualitys.append(f"{stream.resolution},FileSize={stream.filesize/ (1024 * 1024):.2f} MB")
    elif stream_type=="Audio":
        specific_streams=streams.filter(only_audio=True,file_extension=format)
        print(specific_streams)
        for stream in specific_streams:
            qualitys.append(f"{stream.abr},FileSize={stream.filesize/ (1024 * 1024):.2f} MB")
    quality_combobox.configure(values=qualitys)
    quality_combobox.set(qualitys[0])



def setting_formats(streams,type):
    formats=["mp4"]
    for stream in streams:
        if not (stream.resolution if type=="video" else stream.abr):
            continue
        file_extension = stream.mime_type.split("/")[-1]
        if file_extension not in formats:
            formats.append(file_extension)
    format_combobox.configure(values=formats)
    format_combobox.set(formats[0])





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
    thumbnail_label.grid(row=2,column=0, padx=10, pady=10,columnspan=2)

def toggle_advanced_options():
    if advanced_options_frame.winfo_ismapped():
        advanced_options_frame.grid_remove()
    else:
        advanced_options_frame.grid(column=0,row=1,padx=5, pady=5)





# System Settings
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("green")


# Our app frame
app= customtkinter.CTk()
app.geometry("720x480")
app.title("Youtube Donwloader")

left_frame = customtkinter.CTkFrame(app,border_width=0,fg_color='transparent')
left_frame.columnconfigure(0, weight=1)
left_frame.pack(side="left", fill="y")

# Create a button to toggle advanced options
advanced_button =customtkinter.CTkButton(left_frame, text="Advanced Options", command=toggle_advanced_options).grid(column=0,row=0,padx=5, pady=5)

# Create a frame to hold the advanced options (initially hidden)
advanced_options_frame = customtkinter.CTkFrame(left_frame,border_width=0,fg_color='transparent')


# Create a frame for the center content
center_frame =customtkinter.CTkFrame(app,border_width=0,fg_color='transparent')
center_frame.pack(side="left",fill="both",expand=True)



#Adding UI Elements
title=customtkinter.CTkLabel(center_frame,text="Insert a youtube link")
title.grid(row=0,column=0,columnspan=2,padx=10,pady=10)

#Link input
url_var=customtkinter.StringVar()
url_var.trace_add("write", on_url_var_change)
link=customtkinter.CTkEntry(center_frame,width=350,height=40,textvariable=url_var)
link.grid(row=1,column=0,columnspan=2, padx=10,pady=10)

#Thumbnail Label
thumbnail_label =tkinter.Label(center_frame,borderwidth=0,highlightthickness=0)

#Download Button
download_button=customtkinter.CTkButton(center_frame,text="Download",command=start_download,state="disabled")
download_button.grid(row=3, column=0,columnspan=2, padx=5, pady=5)

# Create "Pause" and "Stop" button
buttons_frame =customtkinter.CTkFrame(center_frame,border_width=0,fg_color='transparent')
stop_button = customtkinter.CTkButton(buttons_frame, text="Stop", command=cancel_download,fg_color="red")
pause_button = customtkinter.CTkButton(buttons_frame, text="Pause", command=toggle_download,fg_color="blue")
pause_button.grid(row=0, column=0,padx=5,pady=10)
stop_button.grid(row=0, column=1,padx=5,pady=10)






format_label = customtkinter.CTkLabel(advanced_options_frame, text="Select Format:")
format_label.grid(row=2, column=0, padx=5, pady=5)
format_combobox = customtkinter.CTkComboBox(advanced_options_frame,corner_radius=6,values="",command=setting_quality)
format_combobox.grid(row=2, column=1, padx=5, pady=5)
  # Set default format
format_combobox.set("")  # Set default format


quality_label = customtkinter.CTkLabel(advanced_options_frame, text="Select Quality:")
quality_label.grid(row=3, column=0, padx=5, pady=5)
quality_combobox = customtkinter.CTkComboBox(advanced_options_frame,corner_radius=6,values="")
quality_combobox.grid(row=3, column=1, padx=5, pady=5)
quality_combobox.set("")  # Set default format

# Create Combobox for selecting video format within the advanced options
def radiobutton_event():
    print("radiobutton toggled, current value:", radio_var.get())

radio_label = customtkinter.CTkLabel(advanced_options_frame, text="Select Format:")
radio_label.grid(row=0, column=0, padx=5, pady=5)
radio_var = customtkinter.StringVar()
radiobutton_1 = customtkinter.CTkRadioButton(advanced_options_frame, text="Video",
                                             command=get_video_info, variable= radio_var, value="Video",radiobutton_width=20,radiobutton_height=20)
radiobutton_2 = customtkinter.CTkRadioButton(advanced_options_frame, text="Audio",
                                             command=get_audio_info, variable= radio_var, value="Audio",radiobutton_width=20,radiobutton_height=20)

radiobutton_1.grid(row=1, column=0,columnspan=2, padx=10, pady=5,sticky=customtkinter.W)
radiobutton_2.grid(row=1, column=1,padx=5, pady=5,sticky=customtkinter.E)
radiobutton_1.select()



# Create a frame to hold the download progress options (initially hidden)
download_info_frame = customtkinter.CTkFrame(center_frame,border_width=0,fg_color='transparent')

#Finished Donwloading
finishLabel=customtkinter.CTkLabel(download_info_frame,text="")
finishLabel.pack()


#Progress percentage
pPercentage=customtkinter.CTkLabel(download_info_frame,text="0%")
pPercentage.pack()

#Progress Bar
progressBar=customtkinter.CTkProgressBar(download_info_frame,width=350)
progressBar.set(0)
progressBar.pack()





#Run app
app.mainloop()