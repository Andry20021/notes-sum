import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
from pathlib import Path
from datetime import datetime

# Base directories
BASE_DIR = Path(__file__).parent
SESSIONS_DIR = BASE_DIR / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

MODEL = "llama3.2:1b-instruct-q4_K_M"
PROMPT = "Summarize this into detailed notes"

# --- Functions ---

def get_next_session_folder():
    """Create a new session folder with timestamp"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    existing = sorted([p for p in SESSIONS_DIR.iterdir() if p.is_dir() and p.name.startswith(f"session_{date_str}")])
    session_num = len(existing) + 1
    folder = SESSIONS_DIR / f"session_{date_str}_{session_num}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def summarize():
    text = text_box.get("1.0", tk.END).strip()
    if not text:
        messagebox.showerror("Error", "No text entered!")
        return

    folder = get_next_session_folder()
    raw_file = folder / "raw_notes.txt"
    summary_file = folder / "summary.docx"

    raw_file.write_text(text)
    command = f'ollama run {MODEL} "{PROMPT}" < "{raw_file}" | pandoc -o "{summary_file}"'
    try:
        subprocess.run(command, shell=True, check=True)
        messagebox.showinfo("Success", f"Summary saved to:\n{summary_file}")
        load_sessions()  # Refresh the left pane
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Command failed:\n{e}")

def load_sessions():
    """Load session folders into the Treeview"""
    for i in tree.get_children():
        tree.delete(i)
    for folder in sorted(SESSIONS_DIR.iterdir()):
        if folder.is_dir():
            tree.insert("", "end", iid=str(folder), text=folder.name)

def load_notes(event):
    """Load raw_notes.txt into text box when session selected"""
    selected = tree.focus()
    if not selected:
        return
    raw_file = Path(selected) / "raw_notes.txt"
    if raw_file.exists():
        text_box.delete("1.0", tk.END)
        text_box.insert(tk.END, raw_file.read_text())

# --- GUI ---
window = tk.Tk()
window.title("Study Note Summarizer with Sidebar")
window.geometry("1000x600")

# Paned window to split left/right
paned = tk.PanedWindow(window, orient=tk.HORIZONTAL)
paned.pack(fill=tk.BOTH, expand=True)

# --- Left pane: sessions list ---
left_frame = tk.Frame(paned)
tree = ttk.Treeview(left_frame)
tree.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
tree.bind("<<TreeviewSelect>>", load_notes)
paned.add(left_frame, width=250)

# --- Right pane: text editor and button ---
right_frame = tk.Frame(paned)
text_box = tk.Text(right_frame, wrap="word", font=("Arial", 12))
text_box.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

btn = tk.Button(right_frame, text="Summarize Notes", font=("Arial", 14), command=summarize)
btn.pack(pady=5)

paned.add(right_frame, width=750)

# Load sessions initially
load_sessions()

window.mainloop()
