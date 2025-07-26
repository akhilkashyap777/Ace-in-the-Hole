# simple_search_hide.py - Clean search hiding for Windows
import os
import platform

def hide_from_search(folder_path):
    """Simple function to hide folder from Windows Search"""
    if platform.system() != "Windows":
        return False
    
    try:
        import ctypes
        
        # Set FILE_ATTRIBUTE_NOT_CONTENT_INDEXED (0x2000) + HIDDEN (0x2)
        result = ctypes.windll.kernel32.SetFileAttributesW(folder_path, 0x2002)
        
        if result:
            # Also set on all files inside
            for root, dirs, files in os.walk(folder_path):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    ctypes.windll.kernel32.SetFileAttributesW(file_path, 0x2002)
            
            return True
        
        return False
    
    except:
        return False

def hide_vault_folders(base_dir):
    """Hide all vault folders from search"""
    if not os.path.exists(base_dir):
        return False
    
    try:
        # Hide base directory
        hide_from_search(base_dir)
        
        # Hide all subdirectories
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path):
                hide_from_search(item_path)
        
        return True
    
    except:
        return False