import os

def get_all_files(folder_path):
    if not os.path.isdir(folder_path):
        return []
    files = [
        os.path.join(folder_path, file) for file in os.listdir(folder_path) 
        if file.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'mp4')) 
        and not file.startswith('.') 
        and not file.startswith('~')
    ]
    return files
