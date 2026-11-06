from __future__ import annotations

import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


APP_TITLE = "Python EXE Builder v2.0"
DEFAULT_OUTPUT = Path.home() / "Documents" / "EXE_Output"

events: queue.Queue[tuple[str, str]] = queue.Queue()
selected_file: Path | None = None
is_building = False


def choose_python_file() -> None:
    global selected_file

    chosen = filedialog.askopenfilename(
        title="Select Python file",
        filetypes=[("Python files", "*.py"), ("All files", "*.*")],
    )
    if chosen:
        selected_file = Path(chosen)
        file_var.set(str(selected_file))
        status_var.set("Ready")


def choose_output_folder() -> None:
    chosen = filedialog.askdirectory(
        title="Choose output folder",
        initialdir=output_var.get() or str(DEFAULT_OUTPUT),
        mustexist=False,
    )
    if chosen:
        output_var.set(chosen)


def set_build_controls(enabled: bool) -> None:
    state = "normal" if enabled else "disabled"
    browse_button.configure(state=state)
    output_button.configure(state=state)
    build_button.configure(state=state)
    mode_onefile.configure(state=state)
    mode_onedir.configure(state=state)
    windowed_check.configure(state=state)


def build_in_background(source: Path, output_dir: Path, mode: str, windowed: bool) -> None:
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        name = source.stem

        with tempfile.TemporaryDirectory(prefix="py_exe_builder_") as temp_name:
            temp_dir = Path(temp_name)
            dist_dir = temp_dir / "dist"
            work_dir = temp_dir / "build"
            spec_dir = temp_dir / "spec"
            dist_dir.mkdir()
            work_dir.mkdir()
            spec_dir.mkdir()

            command = [
                sys.executable,
                "-m",
                "PyInstaller",
                "--noconfirm",
                "--clean",
                "--name",
                name,
                "--distpath",
                str(dist_dir),
                "--workpath",
                str(work_dir),
                "--specpath",
                str(spec_dir),
            ]

            if mode == "onefile":
                command.append("--onefile")
            else:
                command.append("--onedir")

            if windowed:
                command.append("--windowed")

            command.append(str(source))

            events.put(("status", "Building... PyInstaller is running."))
            result = subprocess.run(
                command,
                cwd=str(source.parent),
                capture_output=True,
                text=True,
                errors="replace",
                check=False,
            )

            if result.returncode != 0:
                details = (result.stderr or result.stdout or "Unknown PyInstaller error").strip()
                events.put(("error", details[-12000:]))
                return

            if mode == "onefile":
                built_item = dist_dir / f"{name}.exe"
                final_item = output_dir / f"{name}.exe"
            else:
                built_item = dist_dir / name
                final_item = output_dir / name

            if not built_item.exists():
                events.put(("error", "PyInstaller finished, but the expected output was not found."))
                return

            if final_item.exists():
                if final_item.is_dir():
                    shutil.rmtree(final_item)
                else:
                    final_item.unlink()

            shutil.move(str(built_item), str(final_item))
            events.put(("success", str(final_item)))

    except FileNotFoundError as exc:
        events.put((
            "error",
            "Python or PyInstaller could not be started.\n"
            "Install PyInstaller with:\n"
            f'  "{sys.executable}" -m pip install pyinstaller\n\n{exc}',
        ))
    except Exception as exc:
        events.put(("error", f"{type(exc).__name__}: {exc}"))


def start_build() -> None:
    global is_building

    if is_building:
        return

    if selected_file is None or not selected_file.is_file():
        messagebox.showwarning("Select a file", "Please select an existing Python (.py) file.")
        return

    if selected_file.suffix.lower() != ".py":
        messagebox.showwarning("Invalid file", "The selected file must have a .py extension.")
        return

    output_dir = Path(output_var.get()).expanduser()
    if not output_var.get().strip():
        messagebox.showwarning("Output folder", "Please choose an output folder.")
        return

    mode = mode_var.get()
    target = output_dir / (f"{selected_file.stem}.exe" if mode == "onefile" else selected_file.stem)

    if target.exists():
        answer = messagebox.askyesno(
            "Replace existing output?",
            f"The following output already exists:\n{target}\n\nReplace it?",
        )
        if not answer:
            return

    is_building = True
    set_build_controls(False)
    progress.start(12)
    status_var.set("Preparing build...")

    worker = threading.Thread(
        target=build_in_background,
        args=(selected_file, output_dir, mode, windowed_var.get()),
        daemon=True,
    )
    worker.start()
    root.after(150, check_build_events)


def check_build_events() -> None:
    global is_building

    try:
        while True:
            kind, message = events.get_nowait()

            if kind == "status":
                status_var.set(message)
            elif kind == "error":
                progress.stop()
                is_building = False
                set_build_controls(True)
                status_var.set("Build failed")
                messagebox.showerror("Build failed", message)
                return
            elif kind == "success":
                progress.stop()
                is_building = False
                set_build_controls(True)
                status_var.set("Build completed successfully")
                messagebox.showinfo("Finished", f"Output created:\n{message}")
                return
    except queue.Empty:
        pass

    if is_building:
        root.after(150, check_build_events)


def open_output_folder() -> None:
    folder = Path(output_var.get()).expanduser()
    folder.mkdir(parents=True, exist_ok=True)

    try:
        if os.name == "nt":
            os.startfile(str(folder))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])
    except Exception as exc:
        messagebox.showerror("Cannot open folder", str(exc))


root = tk.Tk()
root.title(APP_TITLE)
root.geometry("690x330")
root.minsize(620, 300)

file_var = tk.StringVar()
output_var = tk.StringVar(value=str(DEFAULT_OUTPUT))
status_var = tk.StringVar(value="Ready")
mode_var = tk.StringVar(value="onefile")
windowed_var = tk.BooleanVar(value=False)

main = ttk.Frame(root, padding=16)
main.pack(fill="both", expand=True)
main.columnconfigure(0, weight=1)

ttk.Label(main, text="Python source file").grid(row=0, column=0, sticky="w")
file_row = ttk.Frame(main)
file_row.grid(row=1, column=0, sticky="ew", pady=(5, 14))
file_row.columnconfigure(0, weight=1)
ttk.Entry(file_row, textvariable=file_var).grid(row=0, column=0, sticky="ew")
browse_button = ttk.Button(file_row, text="Browse...", command=choose_python_file)
browse_button.grid(row=0, column=1, padx=(8, 0))

ttk.Label(main, text="Output folder").grid(row=2, column=0, sticky="w")
out_row = ttk.Frame(main)
out_row.grid(row=3, column=0, sticky="ew", pady=(5, 14))
out_row.columnconfigure(0, weight=1)
ttk.Entry(out_row, textvariable=output_var).grid(row=0, column=0, sticky="ew")
output_button = ttk.Button(out_row, text="Choose...", command=choose_output_folder)
output_button.grid(row=0, column=1, padx=(8, 0))

ttk.Label(main, text="Build mode").grid(row=4, column=0, sticky="w")
mode_row = ttk.Frame(main)
mode_row.grid(row=5, column=0, sticky="w", pady=(5, 10))
mode_onefile = ttk.Radiobutton(mode_row, text="One file (.exe)", variable=mode_var, value="onefile")
mode_onefile.grid(row=0, column=0, padx=(0, 18))
mode_onedir = ttk.Radiobutton(mode_row, text="One folder", variable=mode_var, value="onedir")
mode_onedir.grid(row=0, column=1)
windowed_check = ttk.Checkbutton(
    main,
    text="Windowed mode (hide console window)",
    variable=windowed_var,
)
windowed_check.grid(row=6, column=0, sticky="w", pady=(0, 12))

progress = ttk.Progressbar(main, mode="indeterminate")
progress.grid(row=7, column=0, sticky="ew", pady=(0, 8))
ttk.Label(main, textvariable=status_var).grid(row=8, column=0, sticky="w")

buttons = ttk.Frame(main)
buttons.grid(row=9, column=0, sticky="e", pady=(14, 0))
build_button = ttk.Button(buttons, text="Build EXE", command=start_build)
build_button.grid(row=0, column=0, padx=(0, 8))
ttk.Button(buttons, text="Open output", command=open_output_folder).grid(row=0, column=1)
ttk.Button(buttons, text="Exit", command=root.destroy).grid(row=0, column=2, padx=(8, 0))

root.mainloop()
