#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

import os
import requests
from github import Github, GithubException

# --- KONFIGURASI ---
# Ganti dengan informasi Anda
GITHUB_TOKEN = os.getenv('GITHUB_PAT')  # Ambil token dari environment variable, JANGAN HARDCODE DI SINI
SOURCE_URL = "https://raw.githubusercontent.com/maywho5454/mastermaywo/main/mastermaywho"
DEST_REPO = "Novantama/IPTV"  # Format: "username/repository"
DEST_FILE_PATH = "Playlist/AllWorld.m3u"
COMMIT_MESSAGE = "Auto update: Sync playlist from source"
GIT_BRANCH = "Main" # Sesuaikan dengan nama branch Anda (misal: "main" atau "master")

def get_source_content():
    """Mengambil konten teks dari URL sumber."""
    try:
        print(f"Mengambil konten dari: {SOURCE_URL}...")
        response = requests.get(SOURCE_URL)
        response.raise_for_status()  # Cek jika ada error HTTP (spt 404)
        print("Konten berhasil diambil.")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error saat mengambil konten sumber: {e}")
        return None

def update_github_file():
    """Memperbarui file di repositori GitHub tujuan."""
    if not GITHUB_TOKEN:
        print("Error: GITHUB_PAT environment variable belum diatur. Script tidak bisa berjalan.")
        return

    # 1. Ambil konten baru dari sumber
    new_content = get_source_content()
    if new_content is None:
        return

    try:
        # 2. Autentikasi ke GitHub
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(DEST_REPO)
        print(f"Berhasil terhubung ke repositori: {DEST_REPO}")

        # 3. Dapatkan file yang ada untuk mendapatkan SHA-nya
        try:
            contents = repo.get_contents(DEST_FILE_PATH, ref=GIT_BRANCH)
            sha = contents.sha
            # Cek apakah kontennya sama untuk menghindari commit yang tidak perlu
            if contents.decoded_content.decode('utf-8') == new_content:
                print("Konten sudah yang terbaru. Tidak ada pembaruan yang diperlukan.")
                return
        except GithubException as e:
            # Jika file tidak ditemukan, kita akan membuatnya (SHA tidak diperlukan)
            if e.status == 404:
                print(f"File '{DEST_FILE_PATH}' tidak ditemukan. Akan membuat file baru.")
                repo.create_file(DEST_FILE_PATH,
                                COMMIT_MESSAGE,
                                new_content,
                                branch=GIT_BRANCH)
                print("File baru berhasil dibuat di GitHub.")
                return
            else:
                raise # Lemparkan error lain

        # 4. Update file yang sudah ada
        print(f"Mencoba memperbarui file '{DEST_FILE_PATH}'...")
        repo.update_file(contents.path,
                        COMMIT_MESSAGE,
                        new_content,
                        sha,
                        branch=GIT_BRANCH)

        print("Pembaruan file berhasil di-commit ke GitHub!")

    except GithubException as e:
        print(f"Error pada API GitHub: {e}")
    except Exception as e:
        print(f"Terjadi error yang tidak terduga: {e}")

if __name__ == "__main__":
    update_github_file()