
# IPTV Filter System

A Python script to filter IPTV channels from `.m3u` playlists based on URL validity and DRM presence. This tool helps users clean up broken or DRM-restricted streams before importing them into IPTV players.

## 🎯 Features

- 🧹 Filters IPTV channels (`.m3u` files) based on:
  - HTTP response status
  - Validation using `ffprobe` and `ffmpeg`
  - Detection of DRM-related keywords
- 📂 Graphical file dialogs for input/output/log paths
- 📝 Generates separate output files:
  - Valid channels (`.m3u`)
  - Error log (`.txt`)
  - Summary of HTTP errors
- ⚡ High-performance filtering with `ThreadPoolExecutor`
- 🧠 Automatic channel grouping based on metadata

## 🔧 Installation

1. **Clone this repository**:
   ```bash
   git clone https://github.com/yourusername/IPTV-Filter-System.git
   cd IPTV-Filter-System
   ```

2. **Install Python dependencies**:

   Ensure you are using Python 3.7 or later.

   ```bash
   pip install -r requirements.txt
   ```

   If `requirements.txt` is not available, manually install:
   ```bash
   pip install requests tqdm
   ```

3. **Install `ffmpeg` and `ffprobe`**:

   - Download from: https://ffmpeg.org/download.html
   - Make sure `ffmpeg.exe` and `ffprobe.exe` are placed in:
     - `C:\ffmpeg\bin`, or
     - Added to your system `PATH`

## ▶️ How to Use

1. Run the script:
   ```bash
   python "IPTV Filter System.py"
   ```

2. Follow the prompts:
   - Select the input `.m3u` playlist
   - Choose a location to save the filtered output
   - Choose a location to save the error log

3. Once finished, you'll find:
   - A filtered `.m3u` file with only valid channels
   - A `.txt` error log listing failed URLs and reasons

## 🧩 Dependencies / Plugins

- `requests` — for HTTP validation
- `tqdm` — for displaying progress bars
- `tkinter` — for GUI-based file dialogs
- `concurrent.futures` — for multithreading
- `ffmpeg` / `ffprobe` — for stream validation
- Built-in modules: `re`, `os`, `shutil`, `subprocess`, `collections`

## 🛡️ Validation Logic

A channel is considered **valid** if:
- It responds with HTTP status code 200, or
- It can be parsed by `ffprobe` or `ffmpeg`, or
- It contains DRM-related metadata (for reference)

Channels that fail all checks will be excluded and logged.

## 📁 Output Structure

- **Filtered Playlist**: A `.m3u` file with only valid channels
- **Error Log**: A `.txt` file with grouped error types and affected URLs
- **Summary**: Error statistics printed in console and header of output file

## ⚠️ Notes

- Designed for **Windows OS** (due to `.exe` usage)
- Requires an active internet connection for URL checks
- Filtering time depends on playlist size and network speed

## 📜 License

This project is licensed under the MIT License. Feel free to use and modify it as needed.
