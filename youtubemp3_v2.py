import customtkinter as ctk
from tkinter import filedialog, messagebox
import yt_dlp as youtube_dl
import os


def download_by_name(name, path, format_choice):
    search_query = f"ytsearch:{name}"
    ydl_opts = {
        'format': 'bestaudio/best' if format_choice == 'Müzik' else 'bestvideo[ext=mp4]+bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if format_choice == 'Müzik' else [],
        'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
        'quiet': True,
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([search_query])


def download_by_link(link, path, format_choice):
    ydl_opts = {
        'format': 'bestaudio/best' if format_choice == 'Müzik' else 'bestvideo[ext=mp4]+bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if format_choice == 'Müzik' else [],
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
        messagebox.showerror("Hata", "Lütfen klasör yolunu, girişi ve formatı sağlayın.")
        return

    inputs = input_data.split('\n')
    for item in inputs:
        if option.get() == 1:
            download_by_name(item, folder_path, format_choice)
        elif option.get() == 2:
            download_by_link(item, folder_path, format_choice)

    messagebox.showinfo("Başarılı", "İndirme tamamlandı.")


app = ctk.CTk()
app.title("YouTube MP3/Video İndirici")
app.geometry("700x550")

ctk.CTkLabel(app, text="Klasör Yolu:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
folder_entry = ctk.CTkEntry(app, width=400)
folder_entry.grid(row=0, column=1, padx=10, pady=10)
ctk.CTkButton(app, text="Gözat", command=browse_folder, width=100).grid(row=0, column=2, padx=10, pady=10)

ctk.CTkLabel(app, text="Giriş (İsim/Link):").grid(row=1, column=0, padx=10, pady=10, sticky="nw")
input_text = ctk.CTkTextbox(app, height=200, width=400)
input_text.grid(row=1, column=1, padx=10, pady=10, columnspan=2)

option = ctk.IntVar()
ctk.CTkRadioButton(app, text="İsme Göre İndir", variable=option, value=1).grid(row=2, column=1, pady=10, sticky="w")
ctk.CTkRadioButton(app, text="Linke Göre İndir", variable=option, value=2).grid(row=2, column=2, pady=10, sticky="w")

ctk.CTkLabel(app, text="Format Seçimi:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
format_var = ctk.StringVar(value="Müzik")
ctk.CTkRadioButton(app, text="Müzik (MP3)", variable=format_var, value="Müzik").grid(row=3, column=1, pady=10,
                                                                                     sticky="w")
ctk.CTkRadioButton(app, text="Video (MP4)", variable=format_var, value="Video").grid(row=3, column=2, pady=10,
                                                                                     sticky="w")

ctk.CTkButton(app, text="İndir", command=process_input, width=200).grid(row=5, column=1, columnspan=2, pady=20)

app.mainloop()
