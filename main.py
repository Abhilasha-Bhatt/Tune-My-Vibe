import pygame
import os
import random
import threading
from tkinter import *
from tkinter import ttk
from googleapiclient.discovery import build
import yt_dlp
import shutil
import ctypes
import vlc
import sys

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)

youtube_api_key = "AIzaSyDRhk3DYTDWtjIDjmKkIrNo1HGvgQTsF7I"

vlc_path = shutil.which("vlc") or r"C:\\Program Files\\VideoLAN\\VLC"
os.environ["PATH"] += os.pathsep + vlc_path
try:
    ctypes.CDLL(os.path.join(vlc_path, "libvlc.dll"))
except OSError:
    print("Warning: VLC library not found! Check installation.")

instance = vlc.Instance()
player = instance.media_player_new()

song_list = []
current_index = 0
current_button = None

mood_colors = {
    "Happy": "#FFD700",
    "Sad": "#4682B4",
    "Relaxed": "#98FB98",
    "Energetic": "#FF4500",
    "Angry": "#DC143C"
}

BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
icon_path = os.path.join(BASE_DIR, "icon.ico")

window = Tk()
window.title("TuneMyVibe: Mood, Music & Motivation")
window.geometry("600x600")
window.config(bg="#2C2F33")
window.iconbitmap(icon_path)

def update_background():
    chosen_mood = selected_mood.get()
    if chosen_mood in mood_colors:
        window.config(bg=mood_colors[chosen_mood])

def fetch_songs():
    update_background()
    global song_list, current_index
    chosen_mood = selected_mood.get()
    if not chosen_mood:
        return
    
    def api_request():
        try:
            youtube = build("youtube", "v3", developerKey=youtube_api_key)
            request = youtube.search().list(q=f"{chosen_mood} mood songs", part="snippet", type="video", maxResults=5)
            response = request.execute()
            
            song_list.clear()
            for item in response.get("items", []):
                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"]
                song_list.append((video_id, title))
            
            random.shuffle(song_list)
            update_ui()
        except Exception as e:
            print(f"Error fetching songs: {e}")
    
    threading.Thread(target=api_request, daemon=True).start()

def update_ui():
    for widget in song_frame.winfo_children():
        widget.destroy()
    
    for i, (video_id, title) in enumerate(song_list):
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        song_button = Button(song_frame, text=title, bg="lightblue", fg="black", font=("Arial", 10),
                             wraplength=300, command=lambda url=video_url, idx=i: play_song(url, idx))
        song_button.pack(pady=2)

def play_song(video_url, index):
    global current_index, current_button
    current_index = index
    
    def stream():
        try:
            ydl_opts = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                audio_url = info['url']
            
            player.stop()
            media = instance.media_new(audio_url)
            player.set_media(media)
            player.play()
            update_progress()
        except Exception as e:
            print(f"Error streaming audio: {e}")
    
    threading.Thread(target=stream, daemon=True).start()
    
    if current_button:
        current_button.config(bg="lightblue")
    current_button = song_frame.winfo_children()[index]
    current_button.config(bg="yellow")

def stop_music():
    player.stop()

def toggle_pause():
    if player.is_playing():
        player.pause()
    else:
        player.play()

def set_volume(val):
    player.audio_set_volume(int(val))

def update_progress():
    if player.is_playing():
        elapsed_time = player.get_time() // 1000
        total_time = player.get_length() // 1000 if player.get_length() > 0 else 0
        progress_label.config(text=f"{elapsed_time}/{total_time} sec")
        window.after(1000, update_progress)

def next_song():
    global current_index
    if current_index < len(song_list) - 1:
        current_index += 1
        play_song(f"https://www.youtube.com/watch?v={song_list[current_index][0]}", current_index)

def previous_song():
    global current_index
    if current_index > 0:
        current_index -= 1
        play_song(f"https://www.youtube.com/watch?v={song_list[current_index][0]}", current_index)

header_label = Label(window, text="🎵 TuneMyVibe 🎨", font=("Arial", 20, "bold"), bg="#2C2F33", fg="#FEE12B")
header_label.pack(pady=20)

mood_label = Label(window, text="Select Your Mood:", font=("Arial", 14), bg="#2C2F33", fg="white")
mood_label.pack()

moods = ["Happy", "Sad", "Relaxed", "Energetic", "Angry"]
selected_mood = StringVar()
mood_dropdown = ttk.Combobox(window, values=moods, textvariable=selected_mood, font=("Arial", 12))
mood_dropdown.pack(pady=10)
mood_dropdown.set("Choose a mood")

apply_button = Button(window, text="Apply Mood 🎶", font=("Arial", 12, "bold"), bg="#FEE12B", fg="black", padx=10, pady=5,
                      command=fetch_songs)
apply_button.pack(pady=10)

song_frame = Frame(window, bg="#2C2F33")
song_frame.pack(pady=10)

progress_label = Label(window, text="", font=("Arial", 12), bg="#2C2F33", fg="white")
progress_label.pack_forget()

volume_slider = Scale(window, from_=0, to=100, orient=HORIZONTAL, label="Volume", command=set_volume)
volume_slider.pack()
volume_slider.set(50)

button_frame = Frame(window, bg="#2C2F33")
button_frame.pack(pady=10)

Button(button_frame, text="⏮ Previous", font=("Arial", 12), command=previous_song).pack(side=LEFT, padx=5)
Button(button_frame, text="⏸ Pause/Resume", font=("Arial", 12), command=toggle_pause).pack(side=LEFT, padx=5)
Button(button_frame, text="⏹ Stop", font=("Arial", 12), bg="red", fg="white", command=stop_music).pack(side=LEFT, padx=5)

window.mainloop()
