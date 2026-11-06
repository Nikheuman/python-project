from __future__ import annotations

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


def choose_file() -> None:
    global selected_file

    chosen = filedialog.askopenfilename(
        title="Select Python file",
        filetypes=[("Python files", "*.py")],
    )
    if chosen:
        selected_file = Path(chosen)
        file_var.set(str(selected_file))
        status_var.set("Ready")


def choose_output() -> None:
    chosen = filedialog.askdirectory(
        title="Choose output folder",
        initialdir=output_var.get(),
    )
    if chosen:
        output_var.set(chosen)


def set_controls_enabled(enabled: bool) -> None:
    state = "normal" if enabled else "disabled"
    browse_button.configure(state=state)
    output_button.configure(state=state)
    build_button.configure(state=state)


def build_exe(source: Path, output_dir: Path) -> None:
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        name = source.stem

        with tempfile.TemporaryDirectory(prefix="py_exe_builder_") as temp:
            temp_dir = Path(temp)
            dist_dir = temp_dir / "dist"
            work_dir = temp_dir / "build"
            spec_dir = temp_dir / "spec"

            command = [
                sys.executable, "-m", "PyInstaller",
                "--noconfirm", "--clean", "--onefile",
                "--name", name,
                "--distpath", str(dist_dir),
                "--workpath", str(work_dir),
                "--specpath", str(spec_dir),
                str(source),
            ]

            events.put(("status", "Building EXE..."))
            result = subprocess.run(
                command,
                cwd=source.parent,
                capture_output=True,
                text=True,
                errors="replace",
                check=False,
            )

            if result.returncode != 0:
                details = (result.stderr or result.stdout or "Unknown build error").strip()
                events.put(("error", details[-10000:]))
                return

            built_file = dist_dir / f"{name}.exe"
            output_file = output_dir / f"{name}.exe"

            if not built_file.is_file():
                events.put(("error", "The build finished, but the EXE file was not found."))
                return

            # Replace the old output only after the new EXE has been built successfully.
            shutil.move(str(built_file), str(output_file))
            events.put(("success", str(output_file)))

    except FileNotFoundError as exc:
        events.put((
            "error",
            "PyInstaller could not be started. Install it with:\n"
            f'"{sys.executable}" -m pip install pyinstaller\n\n{exc}',
        ))
    except Exception as exc:
        events.put(("error", f"{type(exc).__name__}: {exc}"))


def start_build() -> None:
    global is_building

    if is_building:
        return

    if selected_file is None or not selected_file.is_file():
        messagebox.showwarning("Select a file", "Choose a valid Python file first.")
        return

    output_text = output_var.get().strip()
    if not output_text:
        messagebox.showwarning("Output folder", "Choose an output folder first.")
        return

    output_dir = Path(output_text).expanduser()
    output_file = output_dir / f"{selected_file.stem}.exe"

    if output_file.exists():
        if not messagebox.askyesno(
            "Replace existing file?",
            f"{output_file} already exists.\nDo you want to replace it?",
        ):
            return

    is_building = True
    set_controls_enabled(False)
    progress.start(12)
    status_var.set("Preparing...")

    threading.Thread(
        target=build_exe,
        args=(selected_file, output_dir),
        daemon=True,
    ).start()
    root.after(150, check_events)


def check_events() -> None:
    global is_building

    try:
        while True:
            kind, message = events.get_nowait()

            if kind == "status":
                status_var.set(message)
            elif kind == "error":
                finish_build("Build failed")
                messagebox.showerror("Build failed", message)
                return
            elif kind == "success":
                finish_build("Build completed")
                messagebox.showinfo("Finished", f"EXE created:\n{message}")
                return
    except queue.Empty:
        pass

    if is_building:
        root.after(150, check_events)


def finish_build(status: str) -> None:
    global is_building
    progress.stop()
    is_building = False
    set_controls_enabled(True)
    status_var.set(status)


root = tk.Tk()
root.title(APP_TITLE)
root.geometry("620x220")
root.minsize(520, 200)

file_var = tk.StringVar()
output_var = tk.StringVar(value=str(DEFAULT_OUTPUT))
status_var = tk.StringVar(value="Ready")

main = ttk.Frame(root, padding=16)
main.pack(fill="both", expand=True)
main.columnconfigure(0, weight=1)

ttk.Label(main, text="Python file").grid(row=0, column=0, sticky="w")
file_row = ttk.Frame(main)
file_row.grid(row=1, column=0, sticky="ew", pady=(4, 12))
file_row.columnconfigure(0, weight=1)
ttk.Entry(file_row, textvariable=file_var).grid(row=0, column=0, sticky="ew")
browse_button = ttk.Button(file_row, text="Browse...", command=choose_file)
browse_button.grid(row=0, column=1, padx=(8, 0))

ttk.Label(main, text="Output folder").grid(row=2, column=0, sticky="w")
output_row = ttk.Frame(main)
output_row.grid(row=3, column=0, sticky="ew", pady=(4, 12))
output_row.columnconfigure(0, weight=1)
ttk.Entry(output_row, textvariable=output_var).grid(row=0, column=0, sticky="ew")
output_button = ttk.Button(output_row, text="Choose...", command=choose_output)
output_button.grid(row=0, column=1, padx=(8, 0))

progress = ttk.Progressbar(main, mode="indeterminate")
progress.grid(row=4, column=0, sticky="ew", pady=(0, 8))
ttk.Label(main, textvariable=status_var).grid(row=5, column=0, sticky="w")
build_button = ttk.Button(main, text="Build EXE", command=start_build)
build_button.grid(row=6, column=0, sticky="e", pady=(12, 0))

root.mainloop()
