import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
from datetime import datetime
from docx import Document

# Base directories
BASE_DIR = Path(__file__).parent
SESSIONS_DIR = BASE_DIR / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

MODEL = "llama3.2:1b-instruct-q4_K_M"
PROMPT = "Summarize this into detailed notes"

# Global state
show_output = True  # True = show summary.docx, False = show raw_notes.txt
current_notes = ""  # Stores in-progress notes

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
    global current_notes
    current_notes = text_box.get("1.0", tk.END).strip()
    if not current_notes:
        messagebox.showerror("Error", "No text entered!")
        return

    folder = get_next_session_folder()
    raw_file = folder / "raw_notes.txt"
    summary_file = folder / "summary.docx"

    raw_file.write_text(current_notes)
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
    """Load either raw or summary notes depending on toggle"""
    selected = tree.focus()
    if not selected:
        return

    temp_text = ""
    if show_output:
        summary_file = Path(selected) / "summary.docx"
        if summary_file.exists():
            doc = Document(summary_file)
            temp_text = "\n".join([p.text for p in doc.paragraphs])
    else:
        raw_file = Path(selected) / "raw_notes.txt"
        if raw_file.exists():
            temp_text = raw_file.read_text()
    
    # Temporarily overwrite editor for preview
    text_box.delete("1.0", tk.END)
    text_box.insert(tk.END, temp_text)

def toggle_view():
    """Switch between input and output view"""
    global show_output
    show_output = not show_output
    if show_output:
        toggle_btn.config(text="Viewing: Output (summary.docx)")
    else:
        toggle_btn.config(text="Viewing: Input (raw_notes.txt)")
    load_notes(None)  # Refresh the current session display

def back_to_current_notes():
    """Restore in-progress notes"""
    text_box.delete("1.0", tk.END)
    text_box.insert(tk.END, current_notes)

# --- GUI ---
window = tk.Tk()
window.title("Study Note Summarizer")
window.geometry("1000x600")

# Paned window to split left/right
paned = tk.PanedWindow(window, orient=tk.HORIZONTAL)
paned.pack(fill=tk.BOTH, expand=True)

# --- Left pane: sessions list ---
left_frame = tk.Frame(paned)
toggle_btn = tk.Button(left_frame, text="Viewing: Output (summary.docx)", command=toggle_view)
toggle_btn.pack(pady=5, padx=5, fill=tk.X)

tree = ttk.Treeview(left_frame)
tree.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
tree.bind("<<TreeviewSelect>>", load_notes)
paned.add(left_frame, width=250)

# --- Right pane: text editor and buttons ---
right_frame = tk.Frame(paned)
text_box = tk.Text(right_frame, wrap="word", font=("Arial", 12))
text_box.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

btn_frame = tk.Frame(right_frame)
btn_frame.pack(pady=5)

summarize_btn = tk.Button(btn_frame, text="Summarize Notes", font=("Arial", 14), command=summarize)
summarize_btn.pack(side=tk.LEFT, padx=5)

back_btn = tk.Button(btn_frame, text="Back to Current Notes", font=("Arial", 14), command=back_to_current_notes)
back_btn.pack(side=tk.LEFT, padx=5)

paned.add(right_frame, width=750)

# Load sessions initially
load_sessions()

window.mainloop()
