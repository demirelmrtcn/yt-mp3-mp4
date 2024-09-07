import customtkinter as ctk
from tkinter import filedialog, messagebox
import yt_dlp as youtube_dl
import os
from PIL import Image

# Define the text labels and messages for both languages
LANGUAGES = {
    "tr": {
        "title": "YouTube MP3/Video İndirici",
        "folder_label": "Klasör Yolu:",
        "browse_button": "Gözat",
        "input_label": "Giriş (İsim/Link):",
        "download_by_name": "İsme Göre İndir",
        "download_by_link": "Linke Göre İndir",
        "format_label": "Format Seçimi:",
        "format_music": "Müzik (MP3)",
        "format_video": "Video (MP4)",
        "download_button": "İndir",
        "error_message": "Lütfen klasör yolunu, girişi ve formatı sağlayın.",
        "success_message": "İndirme tamamlandı."
    },
    "en": {
        "title": "YouTube MP3/Video Downloader",
        "folder_label": "Folder Path:",
        "browse_button": "Browse",
        "input_label": "Input (Name/Link):",
        "download_by_name": "Download by Name",
        "download_by_link": "Download by Link",
        "format_label": "Format Choice:",
        "format_music": "Music (MP3)",
        "format_video": "Video (MP4)",
        "download_button": "Download",
        "error_message": "Please provide the folder path, input, and format.",
        "success_message": "Download complete."
    }
}

current_lang = LANGUAGES["tr"]  # Default to Turkish

def change_language(lang_code):
    global current_lang
    current_lang = LANGUAGES[lang_code]
    update_ui_language()

def update_ui_language():
    app.title(current_lang["title"])
    folder_label.configure(text=current_lang["folder_label"])
    browse_button.configure(text=current_lang["browse_button"])
    input_label.configure(text=current_lang["input_label"])
    download_by_name_rb.configure(text=current_lang["download_by_name"])
    download_by_link_rb.configure(text=current_lang["download_by_link"])
    format_label.configure(text=current_lang["format_label"])
    format_music_rb.configure(text=current_lang["format_music"])
    format_video_rb.configure(text=current_lang["format_video"])
    download_button.configure(text=current_lang["download_button"])


def download_by_name(name, path, format_choice):
    search_query = f"ytsearch:{name}"

    # Müzik ve video için ayarları ayırıyoruz
    if format_choice == 'Müzik':
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
    else:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio/best',
            'merge_output_format': 'mp4',  # Videoların mp4 formatında kaydedilmesi
            'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
            'quiet': True,
        }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([search_query])


def download_by_link(link, path, format_choice):
    # Müzik ve video için ayarları ayırıyoruz
    if format_choice == 'Müzik':
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
    else:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio/best',
            'merge_output_format': 'mp4',  # Videoların mp4 formatında kaydedilmesi
            'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
            'quiet': True,
        }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([link])

def browse_folder():
    folder_path = filedialog.askdirectory()
    folder_entry.delete(0, ctk.END)
    folder_entry.insert(0, folder_path)

def process_input():
    folder_path = folder_entry.get()
    input_data = input_text.get("1.0", ctk.END).strip()
    format_choice = format_var.get()

    if not folder_path or not input_data or not format_choice:
        messagebox.showerror("Error", current_lang["error_message"])
        return

    inputs = input_data.split('\n')
    for item in inputs:
        if option.get() == 1:
            download_by_name(item, folder_path, format_choice)
        elif option.get() == 2:
            download_by_link(item, folder_path, format_choice)

    messagebox.showinfo("Success", current_lang["success_message"])

def load_flag_image(path):
    return ctk.CTkImage(light_image=Image.open(path), dark_image=Image.open(path), size=(20, 15))

# Application UI
app = ctk.CTk()
app.title(current_lang["title"])
app.geometry("700x500")

folder_label = ctk.CTkLabel(app, text=current_lang["folder_label"])
folder_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
folder_entry = ctk.CTkEntry(app, width=400)
folder_entry.grid(row=0, column=1, padx=10, pady=10)
browse_button = ctk.CTkButton(app, text=current_lang["browse_button"], command=browse_folder, width=100)
browse_button.grid(row=0, column=2, padx=10, pady=10)

input_label = ctk.CTkLabel(app, text=current_lang["input_label"])
input_label.grid(row=1, column=0, padx=10, pady=10, sticky="nw")
input_text = ctk.CTkTextbox(app, height=200, width=400)
input_text.grid(row=1, column=1, padx=10, pady=10, columnspan=2)

option = ctk.IntVar()
download_by_name_rb = ctk.CTkRadioButton(app, text=current_lang["download_by_name"], variable=option, value=1)
download_by_name_rb.grid(row=2, column=1, pady=10, sticky="w")
download_by_link_rb = ctk.CTkRadioButton(app, text=current_lang["download_by_link"], variable=option, value=2)
download_by_link_rb.grid(row=2, column=2, pady=10, sticky="w")

format_label = ctk.CTkLabel(app, text=current_lang["format_label"])
format_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
format_var = ctk.StringVar(value="Müzik")
format_music_rb = ctk.CTkRadioButton(app, text=current_lang["format_music"], variable=format_var, value="Müzik")
format_music_rb.grid(row=3, column=1, pady=10, sticky="w")
format_video_rb = ctk.CTkRadioButton(app, text=current_lang["format_video"], variable=format_var, value="Video")
format_video_rb.grid(row=3, column=2, pady=10, sticky="w")

download_button = ctk.CTkButton(app, text=current_lang["download_button"], command=process_input, width=200)
download_button.grid(row=5, column=1, columnspan=2, pady=20)

turkish_flag = load_flag_image("C:/PY/youtubemp3/turkish.png")
english_flag = load_flag_image("C:/PY/youtubemp3/english.png")

language_frame = ctk.CTkFrame(app)
language_frame.grid(row=6, column=2, padx=10, pady=10, sticky="se")

ctk.CTkButton(language_frame, image=turkish_flag, text="", command=lambda: change_language("tr")).grid(row=0, column=0, padx=5)
ctk.CTkButton(language_frame, image=english_flag, text="", command=lambda: change_language("en")).grid(row=0, column=1, padx=5)

app.mainloop()
