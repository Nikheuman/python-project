# قسمت۱---------------------------------------------------------------------------

import os
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

# -----------------------------
# تنظیم مسیرها
# -----------------------------
BASE_DIR = r"F:\exe"
WORK_DIR = os.path.join(BASE_DIR, "work")
DIST_DIR = os.path.join(BASE_DIR, "dist")

selected_file = ""


# -----------------------------
# ایجاد پوشه‌ها
# -----------------------------
def create_folders():
    os.makedirs(WORK_DIR, exist_ok=True)
    os.makedirs(DIST_DIR, exist_ok=True)


# -----------------------------
# پاکسازی پوشه work
# -----------------------------
def clean_work():
    if os.path.exists(WORK_DIR):
        shutil.rmtree(WORK_DIR)

    os.makedirs(WORK_DIR)


# -----------------------------
# انتخاب فایل Python
# -----------------------------
def browse_file():
    global selected_file

    filename = filedialog.askopenfilename(
        title="Select Python File",
        filetypes=[("Python Files", "*.py")]
    )

    if filename:
        selected_file = filename
        txt_file.delete(0, tk.END)
        txt_file.insert(0, filename)
        lbl_status.config(text="Ready")


# -----------------------------
# باز کردن پوشه dist
# -----------------------------
def open_dist():

    if not os.path.exists(DIST_DIR):
        os.makedirs(DIST_DIR)

    os.startfile(DIST_DIR)


# -----------------------------
# ساخت EXE
# -----------------------------
def build_exe():

    global selected_file

    if selected_file == "":
        messagebox.showwarning(
            "Warning",
            "Please select a Python file."
        )
        return

    lbl_status.config(text="Building...")
    root.update()

    create_folders()
    clean_work()

    filename = os.path.basename(selected_file)

    work_file = os.path.join(
        WORK_DIR,
        filename
    )

    shutil.copy2(
        selected_file,
        work_file
    )

    old = os.getcwd()
    os.chdir(WORK_DIR)
    
    # قسمت 2---------------------------------------------------------------------------
    try:

        result = subprocess.run(
            [
                "pyinstaller",
                "--onefile",
                filename
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:

            os.chdir(old)

            messagebox.showerror(
                "Build Error",
                result.stderr
            )

            lbl_status.config(text="Error")
            return

        exe_name = os.path.splitext(filename)[0] + ".exe"

        src_exe = os.path.join(
            WORK_DIR,
            "dist",
            exe_name
        )

        dst_exe = os.path.join(
            DIST_DIR,
            exe_name
        )

        if os.path.exists(dst_exe):
            os.remove(dst_exe)

        shutil.move(
            src_exe,
            dst_exe
        )

    finally:

        os.chdir(old)

        spec = os.path.join(
            WORK_DIR,
            os.path.splitext(filename)[0] + ".spec"
        )

        if os.path.exists(spec):
            os.remove(spec)

        build = os.path.join(
            WORK_DIR,
            "build"
        )

        if os.path.exists(build):
            shutil.rmtree(build)

        dist = os.path.join(
            WORK_DIR,
            "dist"
        )

        if os.path.exists(dist):
            shutil.rmtree(dist)

        pycache = os.path.join(
            WORK_DIR,
            "__pycache__"
        )

        if os.path.exists(pycache):
            shutil.rmtree(pycache)

        if os.path.exists(work_file):
            os.remove(work_file)

    lbl_status.config(text="Done")

    messagebox.showinfo(
        "Finished",
        "EXE created successfully."
    )    
    
    # قسمت 3---------------------------------------------------------------------------

# -----------------------------
# رابط گرافیکی
# -----------------------------
root = tk.Tk()
root.title("Python EXE Builder v1.0")
root.geometry("600x220")
root.resizable(False, False)

lbl1 = tk.Label(
    root,
    text="Python File"
)
lbl1.pack(pady=(10, 2))

txt_file = tk.Entry(
    root,
    width=70
)
txt_file.pack(padx=10)

btn_browse = tk.Button(
    root,
    text="Browse...",
    width=15,
    command=browse_file
)
btn_browse.pack(pady=8)

lbl2 = tk.Label(
    root,
    text="Output Folder"
)
lbl2.pack()

lbl_output = tk.Label(
    root,
    text=DIST_DIR,
    fg="blue"
)
lbl_output.pack()

lbl_status = tk.Label(
    root,
    text="Ready",
    fg="green"
)
lbl_status.pack(pady=10)

frame = tk.Frame(root)
frame.pack(pady=10)

btn_build = tk.Button(
    frame,
    text="Build EXE",
    width=15,
    command=build_exe
)
btn_build.grid(row=0, column=0, padx=5)

btn_open = tk.Button(
    frame,
    text="Open dist",
    width=15,
    command=open_dist
)
btn_open.grid(row=0, column=1, padx=5)

btn_exit = tk.Button(
    frame,
    text="Exit",
    width=15,
    command=root.destroy
)
btn_exit.grid(row=0, column=2, padx=5)

create_folders()

root.mainloop()

