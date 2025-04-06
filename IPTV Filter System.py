import os
import shutil
import requests
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import re
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog

# ======================= KONFIGURASI =======================
CHECK_FFPROBE = True
CHECK_FFMPEG = True

def find_executable(name, hints=[]):
    path = shutil.which(name)
    if path:
        return path
    for hint in hints:
        full = os.path.join(hint, name)
        if os.path.isfile(full):
            return full
    return None

FFPROBE_PATH = find_executable("ffprobe.exe", [
    r"C:\ffmpeg\bin",
    r"C:\Program Files\ffmpeg\bin",
    r"C:\Users\%USERNAME%\Documents\ffmpeg\bin"
])
FFMPEG_PATH = find_executable("ffmpeg.exe", [
    r"C:\ffmpeg\bin",
    r"C:\Program Files\ffmpeg\bin",
    r"C:\Users\%USERNAME%\Documents\ffmpeg\bin"
])

if not FFPROBE_PATH or not FFMPEG_PATH:
    raise FileNotFoundError("ffprobe.exe atau ffmpeg.exe tidak ditemukan. Pastikan sudah ter-install dan PATH sudah diatur.")

# ======================= PARAMETER =======================
HTTP_TIMEOUT = 7
FF_TIMEOUT = 12
MAX_WORKERS = 100
FFMPEG_DURATION = 4
DRM_PATTERN = re.compile(r'drm|license_|clearkey', re.IGNORECASE)

# ======================= DIALOG FILE =======================
def get_file_via_dialog(title, filetypes, save=False, defaultextension=None):
    root = tk.Tk()
    root.withdraw()
    if save:
        return filedialog.asksaveasfilename(
            title=title,
            filetypes=filetypes,
            defaultextension=defaultextension
        )
    else:
        return filedialog.askopenfilename(title=title, filetypes=filetypes)

# ======================= PARSING M3U =======================
def parse_m3u(file_path):
    channels = []
    current_meta = []
    current_url = None
    current_group = "Unknown Group"

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                if current_url and current_meta:
                    channels.append(create_channel(current_meta, current_url, current_group))
                    current_meta, current_url = [], None
                continue
            if line.startswith("http"):
                current_url = line
                if current_meta:
                    channels.append(create_channel(current_meta, current_url, current_group))
                    current_meta, current_url = [], None
            elif line.startswith("#"):
                current_meta.append(line)
                if line.startswith("#EXTINF"):
                    current_group = extract_group(line)
    if current_url and current_meta:
        channels.append(create_channel(current_meta, current_url, current_group))
    return [ch for ch in channels if ch["metadata"]]

def create_channel(meta, url, group):
    return {"metadata": meta, "url": url, "group": group}

def extract_group(line):
    match = re.search(r'group-title="([^"]+)"', line)
    return match.group(1) if match else "Unknown Group"

# ======================= VALIDASI =======================
def validate_channel(channel):
    url = channel["url"]
    meta = channel["metadata"]

    if has_drm(meta):
        return True, channel, None

    error_msg = None
    http_code = None

    try:
        response = requests.head(url, timeout=HTTP_TIMEOUT, allow_redirects=True)
        if response.status_code == 200:
            return True, channel, None
        else:
            http_code = f"HTTP {response.status_code}"
    except requests.exceptions.RequestException as e:
        error_msg = f"HTTP Error: {type(e).__name__}"

    if CHECK_FFPROBE and run_ffprobe(url):
        return True, channel, None
    elif CHECK_FFMPEG and run_ffmpeg(url):
        return True, channel, None

    return False, channel, error_msg or http_code or "All checks failed"

def has_drm(metadata):
    return any(DRM_PATTERN.search(line) for line in metadata)

def run_ffprobe(url):
    try:
        cmd = [FFPROBE_PATH, '-v', 'error', '-show_entries', 'format=duration', url]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               timeout=FF_TIMEOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        return bool(result.stdout.decode().strip())
    except:
        return False

def run_ffmpeg(url):
    try:
        cmd = [FFMPEG_PATH, '-v', 'error', '-t', str(FFMPEG_DURATION), '-i', url, '-f', 'null', '-']
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=FF_TIMEOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        return "Invalid data found" not in result.stderr.decode()
    except:
        return False

# ======================= OUTPUT =======================
def write_m3u_output(valid_channels, http_errors, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n\n")
        if http_errors:
            f.write("# STATISTIK ERROR:\n")
            for code, count in http_errors.items():
                f.write(f"# {code}: {count}\n")
            f.write("\n")
        for group in sorted(valid_channels.keys(), key=str.casefold):
            f.write(f"# GROUP: {group}\n")
            for ch in valid_channels[group]:
                write_channel(f, ch)

def write_channel(file_obj, channel):
    extinf = [line for line in channel["metadata"] if line.startswith("#EXTINF")]
    other_meta = [line for line in channel["metadata"] if not line.startswith("#EXTINF")]
    for line in extinf + other_meta:
        file_obj.write(f"{line.strip()}\n")
    file_obj.write(f"{channel['url'].strip()}\n\n")

def write_error_log(error_log, error_log_path):
    with open(error_log_path, "w", encoding="utf-8") as f:
        f.write("==== LOG ERROR DETAIL ====\n\n")
        for error_type, urls in error_log.items():
            f.write(f"ERROR TYPE: {error_type}\n")
            f.write(f"TOTAL: {len(urls)}\n")
            f.write("URL TERKAIT:\n")
            for url in urls:
                f.write(f"- {url}\n")
            f.write("\n" + "="*50 + "\n")
    print(f"\nFile error log disimpan di: {os.path.abspath(error_log_path)}")

def print_report(total, removed, http_errors):
    print(f"\n{'='*40}")
    print(f"Total Channel: {total}")
    print(f"Tersaring    : {total - removed}")
    print(f"DiHapus      : {removed}")
    if http_errors:
        print("\nStatistik Error HTTP:")
        for code, count in http_errors.items():
            print(f"- {code}: {count}x")

# ======================= MAIN =======================
def main():
    print("== M3U Channel Filter ==")

    print("Silakan pilih file M3U input...")
    input_path = get_file_via_dialog("Pilih file M3U", [("M3U Files", "*.m3u")])
    if not input_path:
        print("Batal. Tidak ada file dipilih.")
        return

    print("Pilih lokasi untuk menyimpan file hasil filter (.m3u)...")
    output_path = get_file_via_dialog("Simpan file output", [("M3U Files", "*.m3u")], save=True, defaultextension=".m3u")
    if not output_path:
        print("Batal. Tidak ada file output dipilih.")
        return

    print("Pilih lokasi untuk menyimpan file log error (.txt)...")
    log_path = get_file_via_dialog("Simpan log error", [("Text Files", "*.txt")], save=True, defaultextension=".txt")
    if not log_path:
        print("Batal. Tidak ada file log dipilih.")
        return

    if not os.path.exists(input_path):
        print(f"[ERROR] File input tidak ditemukan: {input_path}")
        return

    channels = parse_m3u(input_path)
    total = len(channels)
    print(f"Memulai validasi {total} channel...")

    valid_channels = defaultdict(list)
    error_log = defaultdict(list)
    http_errors = defaultdict(int)
    removed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(validate_channel, ch): ch for ch in channels}
        for future in tqdm(as_completed(futures), total=total, desc="Memfilter", unit="ch", dynamic_ncols=True):
            ch = futures[future]
            is_valid, _, error = future.result()
            if is_valid:
                valid_channels[ch["group"]].append(ch)
            else:
                removed += 1
                if error:
                    error_type = error.split(":")[0] if ":" in error else error
                    error_log[error_type].append(ch["url"])
                    if "HTTP" in error_type:
                        http_errors[error_type.split()[-1]] += 1

    write_m3u_output(valid_channels, http_errors, output_path)
    write_error_log(error_log, log_path)
    print_report(total, removed, http_errors)

if __name__ == "__main__":
    main()
