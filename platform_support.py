"""Small native OS integrations; imported without platform-specific dependencies."""
import os
import subprocess
import sys


def lock_instance(stream):
    stream.seek(0)
    if sys.platform == 'win32':
        import msvcrt
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def open_folder(path):
    if sys.platform == 'win32':
        os.startfile(path)
    else:
        subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', str(path)])


def choose_folder():
    if sys.platform == 'darwin':
        # AppleScript uses a static command; output paths are never interpolated into code.
        result = subprocess.run(['osascript', '-e', 'POSIX path of (choose folder with prompt "Output folder / 저장 폴더")'], capture_output=True, text=True)
        if result.returncode:
            if '(-128)' in result.stderr:return ''
            raise RuntimeError(result.stderr.strip() or 'Folder picker failed')
        return result.stdout.strip()
    import tkinter as tk
    from tkinter import filedialog
    window = tk.Tk(); window.withdraw(); window.attributes('-topmost', True)
    try:return filedialog.askdirectory(title='Output folder / 저장 폴더', parent=window)
    finally:window.destroy()
