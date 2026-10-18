"""Hızlı kontrol: python test_app.py"""
from app import build_opts, clean_settings, human_speed, to_target

assert to_target("tarkan şımarık") == "ytsearch1:tarkan şımarık"
assert to_target("https://youtu.be/abc") == "https://youtu.be/abc"
assert to_target("youtu.be/abc") == "https://youtu.be/abc"
assert to_target("www.youtube.com/watch?v=x") == "https://www.youtube.com/watch?v=x"

mp3 = build_opts("MP3", "192 kbps", "out", print)
assert mp3["postprocessors"][0]["preferredquality"] == "192"
mp4 = build_opts("MP4", "720p", "out", print)
assert mp4["format_sort"][0] == "res:720" and mp4["merge_output_format"] == "mp4"
assert build_opts("MP4", "Max", "out", print)["format_sort"][0] == "res"

assert human_speed(None) == "…" and human_speed(2 * 1024 * 1024) == "2.0 MB/s"
assert clean_settings(5) == {} and clean_settings({"lang": "de", "format": "WAV", "theme": "x", "folder": 3}) == {}
assert clean_settings({"lang": "en", "format": "MP4"}) == {"lang": "en", "format": "MP4"}
print("ok")
