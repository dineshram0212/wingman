import os
import psutil
import subprocess
import platform
from wingman.plugins.tool_decorator import tool


@tool
def write_file(filename: str, content: str):
    """
    Writes content to a file if it exists; otherwise creates a new file and writes the content to it.

    :param filename: The name (with path) of the file to write.
    :param content: The content to write into the file.
    """
    if not os.path.exists(filename):
        try:
            with open(filename, 'a+') as f:
                f.write(content)
                print({})
        except Exception as e:
            print(f"Error creating file {filename}: {e}")
    try:
        with open(filename, 'w') as f:
            f.write(content)
    except Exception as e:
        print(f"Error Writing to file {filename}: {e}")


@tool
def read_file(filename: str):
    """
    Reads content from a file.

    :param filename: The name (with path) of the file to read.
    """
    try:
        with open(filename, 'r') as f:
            content = f.read()
            print(f"Content inside {filename}:\n\n{content}")
            return content
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        return ""

@tool
def open_file(filename: str):
    """
    Opens a file.

    :param filename: The name (with path) of the file to open.
    """
    try:
        if platform.system() == "Windows":
            os.startfile(filename)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", filename])
        else:  # Linux
            subprocess.run(["xdg-open", filename])

        return f"Opened file: {filename}"
    except Exception as e:
        return f"Failed to open file: {str(e)}"



def get_usable_drives():
    drives = []
    for p in psutil.disk_partitions(all=False):
        if os.name == "nt":
            if 'cdrom' in p.opts or p.fstype == '':
                continue
        drives.append(p.mountpoint)
    drives.remove('C:\\')
    home_dir = os.path.expanduser("~")
    base_dirs = [
        os.path.join(home_dir, "Documents"),
        os.path.join(home_dir, "Desktop"),
        os.path.join(home_dir, "Downloads"),
    ]
    base_dirs+= drives
    return base_dirs


@tool
def find_all_user_files(filename: str, target_directory: str = None):
    """
    Used to find all the possible filepaths for a given filename.
    Searches for all matching filenames in user folders and mounted local drives.
    Returns a list of file paths where matches were found.

    :param filename: The name of the file or the keyword to search for.
    :param target_directory: Optional directory to prioritize during the search.
    """
    search_dirs = get_usable_drives()

    # Optionally prioritize a given directory
    if target_directory:
        home = os.path.expanduser("~")
        prioritized = os.path.join(home, target_directory)
        if os.path.exists(prioritized):
            search_dirs.insert(0, prioritized)

    matches = []

    skip_dirs = {
        "windows", "program files", "program files (x86)", "system volume information",
        "$recycle.bin", "node_modules", "venv", "env",
        "dist", "build", "out", "tmp", "temp", "log", "logs"
    }


    for directory in search_dirs:
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d.lower() not in skip_dirs and not d.startswith((".", "_", "$"))]

            for f in files:
                if filename.lower() in f.lower():
                    matches.append(os.path.join(root, f))


    return matches