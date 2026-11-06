# Python EXE Builder v2.0

A small Windows-friendly Tkinter utility that packages a Python script with PyInstaller.

## Requirements

- Python 3.10 or newer
- PyInstaller

Install the dependency:

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python exe_v2.py
```

## Features

- Browse for a Python `.py` file.
- Choose the output directory.
- Build as a single executable (`--onefile`) or as a folder (`--onedir`).
- Optional windowed mode (`--windowed`) for GUI programs.
- Run PyInstaller in a background thread so the Tkinter interface stays responsive.
- Use the active Python interpreter to launch PyInstaller.
- Build artifacts are isolated in a temporary directory and cleaned up automatically.
- Existing output is replaced only after confirmation.

## Notes and limitations

- This tool packages the selected entry-point script. Projects with extra data files, dynamic imports, plugins, or non-standard resources may need additional PyInstaller options such as `--add-data` or `--hidden-import`.
- A successful build does not guarantee that the executable works on every Windows version or computer. Test the result on a clean target machine.
- Build output is currently captured and shown when an error occurs; live percentage progress is not available because PyInstaller does not provide a reliable percentage for this workflow.

## Learning goals

This exercise demonstrates Tkinter widgets, pathlib, subprocess, temporary directories, threads, queues, exception handling, and safe file replacement.
