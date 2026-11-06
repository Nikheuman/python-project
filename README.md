# Python EXE Builder v2.0

A simple Tkinter tool for converting one Python script into a single Windows EXE using PyInstaller.

## Requirements

- Python 3.10+
- PyInstaller

Install:

```bash
python -m pip install -r requirements.txt
```

Run:

```bash
python exe_v2.py
```

## How to use

1. Select a `.py` file.
2. Choose the output folder.
3. Click **Build EXE**.

The program runs PyInstaller in a background thread so the window stays responsive. Temporary build files are kept separate and cleaned up automatically. If an EXE with the same name already exists, you are asked before it is replaced.

## Note

This version packages a single entry-point script. Projects that need extra data files or hidden imports may require additional PyInstaller settings.
