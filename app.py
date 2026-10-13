# app.py
# berkas utama aplikasi 2EZ4U
# jalankan: python app.py atau py app.py

import os
import sys
import tkinter as tk

# pastikan folder root masuk ke path import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from frontend.ui import AppUI


def main():
    root = tk.Tk()
    app = AppUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
