import tkinter as tk
from tkinter import filedialog, messagebox
import yt_dlp as youtube_dl
import os

def download_by_name(name, path):
    search_query = f"ytsearch:{name}"
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
        'quiet': True,
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([search_query])
    messagebox.showinfo("Success", f"Downloaded and converted: {name}")

def download_by_link(link, path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
        'quiet': True,
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([link])
    messagebox.showinfo("Success", f"Downloaded and converted: {link}")

def browse_folder():
    folder_path = filedialog.askdirectory()
    folder_entry.delete(0, tk.END)
    folder_entry.insert(0, folder_path)

def process_input():
    folder_path = folder_entry.get()
    input_data = input_text.get("1.0", tk.END).strip()
    if not folder_path or not input_data:
        messagebox.showerror("Error", "Please provide both folder path and input.")
        return

    inputs = input_data.split('\n')
    for item in inputs:
        if option.get() == 1:
            download_by_name(item, folder_path)
        elif option.get() == 2:
            download_by_link(item, folder_path)

app = tk.Tk()
app.title("YouTube MP3 Downloader")

tk.Label(app, text="Folder Path:").grid(row=0, column=0, padx=10, pady=10)
folder_entry = tk.Entry(app, width=50)
folder_entry.grid(row=0, column=1, padx=10, pady=10)
tk.Button(app, text="Browse", command=browse_folder).grid(row=0, column=2, padx=10, pady=10)

tk.Label(app, text="Input (Name/Link):").grid(row=1, column=0, padx=10, pady=10)
input_text = tk.Text(app, height=10, width=50)
input_text.grid(row=1, column=1, padx=10, pady=10, columnspan=2)

option = tk.IntVar()
tk.Radiobutton(app, text="Download by Name", variable=option, value=1).grid(row=2, column=1, pady=10)
tk.Radiobutton(app, text="Download by Link", variable=option, value=2).grid(row=2, column=2, pady=10)

tk.Button(app, text="Download", command=process_input).grid(row=3, column=1, columnspan=2, pady=10)

app.mainloop()
