# app.py - aplikasi utama 2EZ4U
# jalanin: python app.py

import sys, os, time, threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

sys.path.insert(0, os.path.dirname(__file__))

from backend.m1_pesanan import Pesanan, Array, LinkList, load_pesanan
from backend.m2_antrean import CircularQueue, Stack, UndoManager
from backend.m3_sorting import (bubble_sort, merge_sort, quick_sort,
                                 by_harga, by_prioritas, by_oid, by_waktu_masuk,
                                 sort_dan_ukur)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("2EZ4U - Sistem Pesanan Kampus")
        self.root.geometry("1100x680")
        self.root.configure(bg="#f5f5f5")

        # data utama
        self.daftar_pesanan = Array()   # nyimpen semua pesanan
        self.queue = CircularQueue()
        self.undo_mgr = UndoManager()
        self.data_mentah = []           # list python biasa buat sorting
        self.data_terurut = None        # hasil sorting terakhir

        self._build_ui()

    def _build_ui(self):
        # === TOP BAR ===
        top = tk.Frame(self.root, bg="#2c3e50", height=50)
        top.pack(fill="x")
        tk.Label(top, text="2EZ4U", font=("Segoe UI", 16, "bold"),
                 bg="#2c3e50", fg="white").pack(side="left", padx=15, pady=8)

        btn_load = tk.Button(top, text="Load CSV", command=self._load_csv,
                             bg="#27ae60", fg="white", font=("Segoe UI", 10),
                             relief="flat", padx=12, pady=4)
        btn_load.pack(side="left", padx=5, pady=8)

        self.lbl_status = tk.Label(top, text="Belum ada data",
                                   bg="#2c3e50", fg="#ecf0f1",
                                   font=("Segoe UI", 9))
        self.lbl_status.pack(side="right", padx=15)

        # === MAIN CONTENT ===
        main = tk.Frame(self.root, bg="#f5f5f5")
        main.pack(fill="both", expand=True, padx=10, pady=5)

        # panel kiri - kontrol
        panel_kiri = tk.Frame(main, bg="#f5f5f5", width=280)
        panel_kiri.pack(side="left", fill="y", padx=(0, 5))
        panel_kiri.pack_propagate(False)

        self._build_panel_pesanan(panel_kiri)
        self._build_panel_sorting(panel_kiri)
        self._build_panel_antrean(panel_kiri)

        # panel kanan - tabel data
        panel_kanan = tk.Frame(main, bg="white", relief="groove", bd=1)
        panel_kanan.pack(side="left", fill="both", expand=True)

        self._build_tabel(panel_kanan)

    def _build_panel_pesanan(self, parent):
        frame = tk.LabelFrame(parent, text="Tambah Pesanan", font=("Segoe UI", 9, "bold"),
                              bg="#f5f5f5", padx=8, pady=5)
        frame.pack(fill="x", pady=(0, 5))

        # input fields
        fields = [("Pelanggan:", "entry_plg"), ("Resto:", "entry_resto"),
                  ("Menu:", "entry_menu"), ("Harga:", "entry_harga")]
        for label_text, attr in fields:
            row = tk.Frame(frame, bg="#f5f5f5")
            row.pack(fill="x", pady=1)
            tk.Label(row, text=label_text, width=10, anchor="w",
                     bg="#f5f5f5", font=("Segoe UI", 8)).pack(side="left")
            e = tk.Entry(row, font=("Segoe UI", 8))
            e.pack(side="left", fill="x", expand=True)
            setattr(self, attr, e)

        # tombol tambah
        btn_row = tk.Frame(frame, bg="#f5f5f5")
        btn_row.pack(fill="x", pady=(5, 0))
        for text, cmd, color in [
            ("Reguler", self._tambah_reguler, "#3498db"),
            ("Prioritas", self._tambah_prioritas, "#f39c12"),
            ("VIP", self._tambah_vip, "#e74c3c"),
        ]:
            tk.Button(btn_row, text=text, command=cmd, bg=color, fg="white",
                      font=("Segoe UI", 8), relief="flat", padx=6).pack(side="left", padx=2)

        # undo
        tk.Button(btn_row, text="Undo", command=self._undo, bg="#95a5a6",
                  fg="white", font=("Segoe UI", 8), relief="flat", padx=6).pack(side="right")

    def _build_panel_sorting(self, parent):
        frame = tk.LabelFrame(parent, text="Sorting (M3)", font=("Segoe UI", 9, "bold"),
                              bg="#f5f5f5", padx=8, pady=5)
        frame.pack(fill="x", pady=(0, 5))

        # pilih algoritma
        tk.Label(frame, text="Algoritma:", bg="#f5f5f5", font=("Segoe UI", 8)).pack(anchor="w")
        self.var_algo = tk.StringVar(value="quick")
        for val, txt in [("bubble", "Bubble Sort"), ("merge", "Merge Sort"), ("quick", "Quick Sort")]:
            tk.Radiobutton(frame, text=txt, variable=self.var_algo, value=val,
                           bg="#f5f5f5", font=("Segoe UI", 8)).pack(anchor="w")

        # pilih kolom
        tk.Label(frame, text="Urutkan by:", bg="#f5f5f5", font=("Segoe UI", 8)).pack(anchor="w", pady=(5, 0))
        self.var_key = tk.StringVar(value="harga")
        key_frame = tk.Frame(frame, bg="#f5f5f5")
        key_frame.pack(fill="x")
        for val, txt in [("harga", "Harga"), ("prioritas", "Prioritas"),
                         ("oid", "Order ID"), ("t_masuk", "Waktu Masuk")]:
            tk.Radiobutton(key_frame, text=txt, variable=self.var_key, value=val,
                           bg="#f5f5f5", font=("Segoe UI", 8)).pack(anchor="w")

        # asc/desc
        self.var_asc = tk.BooleanVar(value=True)
        tk.Checkbutton(frame, text="Ascending", variable=self.var_asc,
                       bg="#f5f5f5", font=("Segoe UI", 8)).pack(anchor="w")

        # jumlah data
        lim_row = tk.Frame(frame, bg="#f5f5f5")
        lim_row.pack(fill="x", pady=(3, 0))
        tk.Label(lim_row, text="Jumlah data:", bg="#f5f5f5", font=("Segoe UI", 8)).pack(side="left")
        self.entry_limit = tk.Entry(lim_row, width=8, font=("Segoe UI", 8))
        self.entry_limit.pack(side="left", padx=3)
        self.entry_limit.insert(0, "1000")

        # tombol sort
        btn_row = tk.Frame(frame, bg="#f5f5f5")
        btn_row.pack(fill="x", pady=(5, 0))
        tk.Button(btn_row, text="Sort!", command=self._do_sort, bg="#8e44ad",
                  fg="white", font=("Segoe UI", 9, "bold"), relief="flat",
                  padx=15).pack(side="left")
        self.lbl_waktu = tk.Label(btn_row, text="", bg="#f5f5f5",
                                  font=("Segoe UI", 8), fg="#7f8c8d")
        self.lbl_waktu.pack(side="left", padx=8)

    def _build_panel_antrean(self, parent):
        frame = tk.LabelFrame(parent, text="Antrean (M2)", font=("Segoe UI", 9, "bold"),
                              bg="#f5f5f5", padx=8, pady=5)
        frame.pack(fill="x", pady=(0, 5))

        self.lbl_queue = tk.Label(frame, text="Queue: 0 item",
                                  bg="#f5f5f5", font=("Segoe UI", 8))
        self.lbl_queue.pack(anchor="w")

        btn_r = tk.Frame(frame, bg="#f5f5f5")
        btn_r.pack(fill="x", pady=3)
        tk.Button(btn_r, text="Enqueue Semua", command=self._enqueue_all,
                  bg="#16a085", fg="white", font=("Segoe UI", 8),
                  relief="flat", padx=6).pack(side="left", padx=2)
        tk.Button(btn_r, text="Proses (Dequeue)", command=self._dequeue,
                  bg="#d35400", fg="white", font=("Segoe UI", 8),
                  relief="flat", padx=6).pack(side="left", padx=2)

    def _build_tabel(self, parent):
        cols = ("no", "oid", "pelanggan", "resto", "menu", "harga", "prioritas", "status")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=25)

        widths = {"no": 45, "oid": 80, "pelanggan": 170, "resto": 110,
                  "menu": 110, "harga": 75, "prioritas": 65, "status": 70}
        for c in cols:
            self.tree.heading(c, text=c.upper())
            self.tree.column(c, width=widths.get(c, 80), anchor="center")

        scroll_y = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        scroll_y.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

    # ==================== AKSI ====================

    def _load_csv(self):
        path = filedialog.askopenfilename(
            title="Pilih file pesanan.csv",
            initialdir=os.path.join(os.path.dirname(__file__), "data"),
            filetypes=[("CSV Files", "*.csv")]
        )
        if not path:
            return

        self.lbl_status.config(text="Loading...")
        self.root.update()

        try:
            raw = load_pesanan(path)
            self.data_mentah = raw

            # masukin ke Array
            self.daftar_pesanan = Array(len(raw) + 10)
            for p in raw:
                self.daftar_pesanan.append(p)

            self.lbl_status.config(text=f"Loaded {len(raw)} pesanan")
            self._tampilkan_data(raw[:500])  # tampilkan 500 pertama biar ga lag
            messagebox.showinfo("Sukses", f"Berhasil load {len(raw)} pesanan!")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal load: {e}")

    def _tampilkan_data(self, data, mulai=1):
        # hapus data lama di tabel
        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, p in enumerate(data):
            no = mulai + idx
            self.tree.insert("", "end", values=(
                no, p.oid, p.pelanggan, p.resto, p.menu,
                f"Rp{p.harga:,}".replace(",", "."), p.prioritas, p.status
            ))

    def _baca_input_pesanan(self):
        plg = self.entry_plg.get().strip()
        resto = self.entry_resto.get().strip()
        menu = self.entry_menu.get().strip()
        harga = self.entry_harga.get().strip()

        if not all([plg, resto, menu, harga]):
            messagebox.showwarning("Input", "Semua field harus diisi!")
            return None

        try:
            harga_int = int(harga)
        except ValueError:
            messagebox.showwarning("Input", "Harga harus angka!")
            return None

        # bikin oid baru
        oid = f"O-{self.daftar_pesanan.size + 1:06d}"
        p = Pesanan(oid, plg, resto, menu, harga_int, 3,
                    int(time.time()), 0, "WAITING")
        return p

    def _tambah_reguler(self):
        p = self._baca_input_pesanan()
        if p is None:
            return
        p.prioritas = 3
        self.daftar_pesanan.tambah_reguler(p)
        self.data_mentah.append(p)
        self.undo_mgr.catat("tambah_reguler", (self.daftar_pesanan.size - 1, p))
        self._refresh_tabel()
        self._clear_input()

    def _tambah_prioritas(self):
        p = self._baca_input_pesanan()
        if p is None:
            return
        p.prioritas = 2
        idx = self.daftar_pesanan.size // 2
        self.daftar_pesanan.tambah_prioritas(p)
        self.data_mentah.append(p)
        self.undo_mgr.catat("tambah_prioritas", (idx, p))
        self._refresh_tabel()
        self._clear_input()

    def _tambah_vip(self):
        p = self._baca_input_pesanan()
        if p is None:
            return
        p.prioritas = 1
        self.daftar_pesanan.tambah_vip(p)
        self.data_mentah.append(p)
        self.undo_mgr.catat("tambah_vip", (0, p))
        self._refresh_tabel()
        self._clear_input()

    def _undo(self):
        result = self.undo_mgr.undo()
        if result is None:
            messagebox.showinfo("Undo", "Ga ada yang bisa di-undo")
            return
        aksi, data = result
        if aksi in ("tambah_reguler", "tambah_prioritas", "tambah_vip"):
            idx, pesanan = data
            try:
                self.daftar_pesanan.hapus_pesanan(idx)
            except IndexError:
                pass
        elif aksi == "dequeue":
            pesanan = data
            self.queue.enqueue(pesanan)

        self._refresh_tabel()
        messagebox.showinfo("Undo", f"Berhasil undo: {aksi}")

    def _do_sort(self):
        if not self.data_mentah:
            messagebox.showwarning("Sort", "Load data dulu!")
            return

        algo = self.var_algo.get()
        key_name = self.var_key.get()
        asc = self.var_asc.get()

        key_map = {
            "harga": by_harga,
            "prioritas": by_prioritas,
            "oid": by_oid,
            "t_masuk": by_waktu_masuk,
        }
        key_func = key_map[key_name]

        # ambil sebagian data sesuai limit
        try:
            limit = int(self.entry_limit.get())
        except ValueError:
            limit = 1000
        data_slice = self.data_mentah[:limit]

        # bubble sort bisa lama banget kalo datanya banyak
        if algo == "bubble" and limit > 5000:
            ok = messagebox.askyesno(
                "Peringatan",
                f"Bubble sort {limit} data bisa lama banget. Lanjut?")
            if not ok:
                return

        self.lbl_waktu.config(text="Sorting...")
        self.root.update()

        hasil, waktu = sort_dan_ukur(data_slice, algo, key_func, asc)

        self.data_terurut = hasil
        self.lbl_waktu.config(text=f"{waktu:.2f} ms")
        self._tampilkan_data(hasil[:500])

    def _enqueue_all(self):
        if not self.data_mentah:
            messagebox.showwarning("Queue", "Load data dulu!")
            return
        self.queue = CircularQueue(len(self.data_mentah) + 10)
        for p in self.data_mentah:
            if p.status == "WAITING" or p.status == "QUEUE":
                self.queue.enqueue(p)
        self.lbl_queue.config(text=f"Queue: {len(self.queue)} item")
        messagebox.showinfo("Queue", f"{len(self.queue)} pesanan masuk antrean")

    def _dequeue(self):
        if self.queue.is_empty():
            messagebox.showinfo("Queue", "Antrean kosong!")
            return
        p = self.queue.dequeue()
        p.status = "DONE"
        self.undo_mgr.catat("dequeue", p)
        self.lbl_queue.config(text=f"Queue: {len(self.queue)} item")
        messagebox.showinfo("Proses", f"Pesanan {p.oid} ({p.pelanggan}) selesai diproses!")

    def _refresh_tabel(self):
        tampil = []
        for i in range(min(self.daftar_pesanan.size, 500)):
            tampil.append(self.daftar_pesanan.get(i))
        self._tampilkan_data(tampil)

    def _clear_input(self):
        self.entry_plg.delete(0, "end")
        self.entry_resto.delete(0, "end")
        self.entry_menu.delete(0, "end")
        self.entry_harga.delete(0, "end")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
