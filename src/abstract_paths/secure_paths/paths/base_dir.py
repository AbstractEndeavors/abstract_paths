import os
WWW_DIR = '/var/www'
MEDIA_DIR = f"{WWW_DIR}/media"
ABS_UPLOAD_DIR = f"{MEDIA_DIR}/users"
def get_base_path(path):
    base_dir = os.path.join(MEDIA_DIR, path)
    return base_dir
