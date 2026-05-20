"""
save_attachment.py
==================

This module provides utilities to download, detect, and manage file attachments
(such as PDFs, ZIPs, HTML, XML, or TXT files) from the **National Stock Exchange (NSE)**
or other data endpoints.

It includes functionality to:
- Download files while maintaining valid NSE session cookies.
- Automatically determine the file type based on its binary signature.
- Rename the file with the correct extension.
- Extract ZIP archives automatically and remove the original compressed file.

Functions
----------
get_file_signature(file_path, num_bytes=10)
    Reads the first few bytes of a file to determine its signature.

determine_file_extension(file_signature)
    Determines the likely file extension based on the file's signature bytes.

download_file(url, local_folder)
    Downloads a file from a given URL, detects its type, renames it, and extracts it if needed.
"""

import os
import requests
import zipfile
import shutil

def get_file_signature(file_path, num_bytes=10):
    """Reads the first few bytes of a file to determine its signature."""
    with open(file_path, 'rb') as file:
        return file.read(num_bytes)

def determine_file_extension(file_signature):
    """Determines the file extension based on its signature."""
    if file_signature.startswith(b'%PDF-'):
        return 'pdf'
    elif file_signature.startswith(b'PK\x03\x04'):
        return 'zip'
    elif file_signature.startswith((b'<!DOCTYPE html>', b'<html>')):
        return 'html'
    elif file_signature.startswith(b'<?xml'):
        return 'xml'
    elif file_signature.startswith((b'\xEF\xBB\xBF', b'\xFF\xFE', b'\xFE\xFF')):
        return 'txt'
    else:
        return None

def download_file(url, local_folder):
    """
    Downloads a file (PDF, ZIP, XML, HTML, TXT) from NSE or another endpoint.
    Detects file type by signature and extracts if ZIP.
    """

    # --- Headers (same as working NSE fetcher) ---
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/123.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/",
        "Connection": "keep-alive",
    }

    os.makedirs(local_folder, exist_ok=True)

    # Extract filename safely
    filename = os.path.basename(url.split("?")[0])
    base_filename, _ = os.path.splitext(filename)
    temp_path = os.path.join(local_folder, f"{base_filename}.tmp")

    # Use session to maintain cookies
    session = requests.Session()
    try:
        # Warm-up requests to NSE to get cookies (some downloads require it)
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        session.get("https://www.nseindia.com/option-chain", headers=headers, timeout=10)

        # Actual download request
        response = session.get(url, headers=headers, stream=True, timeout=20)
        response.raise_for_status()

        # Save raw content to a temp file
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Detect file type and rename
        file_signature = get_file_signature(temp_path)
        file_extension = determine_file_extension(file_signature)

        if not file_extension:
            return temp_path

        final_path = os.path.join(local_folder, f"{base_filename}.{file_extension}")
        shutil.move(temp_path, final_path)

        # Extract ZIP files automatically
        if file_extension == 'zip':
            try:
                with zipfile.ZipFile(final_path, 'r') as zip_ref:
                    zip_ref.extractall(local_folder)

                os.remove(final_path)
            except zipfile.BadZipFile:
                pass

        return final_path

    except requests.exceptions.RequestException as e:
        return None

    finally:
        session.close()
