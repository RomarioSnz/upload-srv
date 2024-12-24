import os
import uuid
import hashlib
import time

def create_unique_folder(base_path):
    unique_id = str(uuid.uuid4())
    folder_path = os.path.join(base_path, unique_id)
    os.makedirs(folder_path, exist_ok=True)
    return unique_id, folder_path

def generate_unique_filename(filename):
    ext = os.path.splitext(filename)[1]
    unique_name = hashlib.md5(f"{filename}{time.time()}".encode()).hexdigest()
    return f"{unique_name}{ext}"
