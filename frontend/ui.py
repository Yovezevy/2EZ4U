# ui.py
# tampilan antarmuka tkinter untuk proyek 2EZ4U
# terdiri dari:
# 1. daftar menu navigasi di kiri (M1, M2, M3)
# 2. form parameter & area hasil di kanan
# 3. panel COMMAND di bawah (mencatat riwayat eksekusi modul & waktu)

import os
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from backend.m1_pesanan import Pesanan, Array, LinkList, load_pesanan
from backend.m2_antrean import (
    Stack,
    ke_postfix,
    hitung_postfix,
    AntreanNaif,
    AntreanMelingkar,
    UndoRedo
)
from backend.m3_laporan import (
    insertion_sort,
    merge_sort,
    linear_search,
    binary_search,
    by_oid,
    by_harga,
    by_selesai
)


class AppUI:
    def __init__(self, root):
        self.root = root
        self.root.title("2EZ4U Food Delivery - Algoritma & Struktur Data")
        self.root.geometry("1180x760")
        self.root.minsize(980, 640)
        self.root.configure(bg="#eef2f5")

        # penyimpanan data backend
        self.data_mentah = []            # list data pesanan dari csv
        self.array_pesanan = Array(4)    # M1: Array
        self.linklist_pesanan = LinkList() # M1: LinkList

        self.queue_naif = AntreanNaif()  # M2: Antrean naif
        self.queue_circ = AntreanMelingkar() # M2: Antrean circular
        self.undo_redo = UndoRedo()       # M2: Stack undo/redo

        self.oid_sorted_cache = None     # M3: cache daftar terurut by oid buat binary search
        self.oid_sorted_time_ms = 0.0

        self.active_menu = "M1_ARRAY_TAMBAH_REGULER"

        self._buat_layout_utama()
        self._pilih_menu("M1_ARRAY_TAMBAH_REGULER")

    def _buat_layout_utama(self):
        # 1. Header atas
        header = tk.Frame(self.root, bg="#1a252f", height=48)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        lbl_logo = tk.Label(header, text="2EZ4U Food Delivery",
                            font=("Segoe UI", 14, "bold"),
                            bg="#1a252f", fg="#ffffff")
        lbl_logo.pack(side="left", padx=15, pady=8)

        self.lbl_info_data = tk.Label(header, text="Data: belum dimuat (0 baris)",
                                      font=("Segoe UI", 9),
                                      bg="#1a252f", fg="#bdc3c7")
        self.lbl_info_data.pack(side="right", padx=15)

        # 2. Panel COMMAND di bawah
        panel_cmd = tk.Frame(self.root, bg="#111827", height=160)
        panel_cmd.pack(fill="x", side="bottom")
        panel_cmd.pack_propagate(False)

        lbl_cmd_title = tk.Label(panel_cmd, text="COMMAND",
                                 font=("Consolas", 10, "bold"),
                                 bg="#111827", fg="#10b981", anchor="w")
        lbl_cmd_title.pack(fill="x", padx=10, pady=(4, 0))

        cmd_content = tk.Frame(panel_cmd, bg="#111827")
        cmd_content.pack(fill="both", expand=True, padx=10, pady=(2, 6))

        scroll_cmd = tk.Scrollbar(cmd_content)
        scroll_cmd.pack(side="right", fill="y")

        self.txt_cmd = tk.Text(cmd_content, font=("Consolas", 9),
                               bg="#0b0f19", fg="#e5e7eb",
                               insertbackground="#ffffff",
                               yscrollcommand=scroll_cmd.set,
                               relief="flat", height=7)
        self.txt_cmd.pack(side="left", fill="both", expand=True)
        scroll_cmd.config(command=self.txt_cmd.yview)

        # tag warna di command log
        self.txt_cmd.tag_config("prompt", foreground="#38bdf8")
        self.txt_cmd.tag_config("module", foreground="#fbbf24")
        self.txt_cmd.tag_config("waktu", foreground="#34d399")
        self.txt_cmd.tag_config("error", foreground="#f87171")

        # 3. Area Tengah (kiri menu, kanan form & hasil)
        tengah = tk.Frame(self.root, bg="#eef2f5")
        tengah.pack(fill="both", expand=True)

        # 3a. Panel Kiri (Menu Navigasi)
        self.panel_menu = tk.Frame(tengah, bg="#ffffff", width=275,
                                   highlightbackground="#d1d5db", highlightthickness=1)
        self.panel_menu.pack(side="left", fill="y", padx=(0, 1))
        self.panel_menu.pack_propagate(False)

        self._bangun_menu_kiri()

        # 3b. Panel Kanan (Form & Hasil)
        self.panel_kanan = tk.Frame(tengah, bg="#f9fafb")
        self.panel_kanan.pack(side="left", fill="both", expand=True)

        # Header menu aktif
        self.banner_frame = tk.Frame(self.panel_kanan, bg="#ffffff", height=42,
                                     highlightbackground="#e5e7eb", highlightthickness=1)
        self.banner_frame.pack(fill="x", side="top")
        self.banner_frame.pack_propagate(False)

        self.lbl_judul_menu = tk.Label(self.banner_frame, text="",
                                       font=("Segoe UI", 11, "bold"),
                                       bg="#ffffff", fg="#1f2937")
        self.lbl_judul_menu.pack(side="left", padx=15, pady=8)

        # Frame tempat form dinamis
        self.form_container = tk.Frame(self.panel_kanan, bg="#f9fafb", padx=15, pady=10)
        self.form_container.pack(fill="x", side="top")

        # Frame hasil
        self.hasil_container = tk.Frame(self.panel_kanan, bg="#ffffff",
                                        highlightbackground="#e5e7eb", highlightthickness=1)
        self.hasil_container.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self._bangun_area_hasil()

    def _catat_command(self, perintah, detail, modul, durasi_ms):
        # mencatat baris perintah ke panel COMMAND persis seperti contoh PDF
        teks_baris = f"> {perintah:<22} {detail:<45} [{modul}] {durasi_ms:8.2f} ms\n"
        self.txt_cmd.insert("end", "> ", "prompt")
        self.txt_cmd.insert("end", f"{perintah:<22} {detail:<45} ")
        self.txt_cmd.insert("end", f"[{modul}] ", "module")
        self.txt_cmd.insert("end", f"{durasi_ms:8.2f} ms\n", "waktu")
        self.txt_cmd.see("end")

    def _bangun_menu_kiri(self):
        # scrollbar di kanan dan canvas di kiri
        scroll = tk.Scrollbar(self.panel_menu, orient="vertical")
        scroll.pack(side="right", fill="y")

        canvas = tk.Canvas(self.panel_menu, bg="#ffffff", highlightthickness=0,
                           yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.config(command=canvas.yview)

        isi_menu = tk.Frame(canvas, bg="#ffffff")
        window_id = canvas.create_window((0, 0), window=isi_menu, anchor="nw", width=255)

        def _on_cfg(e):
            canvas.configure(scrollregion=canvas.bbox("all"))

        isi_menu.bind("<Configure>", _on_cfg)

        def _on_wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_wheel)

        # Seksi DATA
        self._tambah_label_grup(isi_menu, "DATA")
        btn_load = tk.Button(isi_menu, text="Load pesanan.csv",
                             command=self._aksi_load_csv,
                             bg="#2563eb", fg="#ffffff", font=("Segoe UI", 9, "bold"),
                             relief="flat", anchor="w", padx=10, pady=5)
        btn_load.pack(fill="x", padx=10, pady=(2, 8))

        # Seksi M1: DATA PESANAN
        self._tambah_label_grup(isi_menu, "M1 - DATA PESANAN")
        m1_items = [
            ("ARRAY - LIHAT PESANAN", "M1_ARRAY_LIHAT"),
            ("ARRAY - TAMBAH PESANAN REGULER", "M1_ARRAY_TAMBAH_REGULER"),
            ("ARRAY - TAMBAH PESANAN PRIORITAS", "M1_ARRAY_TAMBAH_PRIORITAS"),
            ("ARRAY - TAMBAH PESANAN VIP", "M1_ARRAY_TAMBAH_VIP"),
            ("ARRAY - HAPUS PESANAN", "M1_ARRAY_HAPUS"),
            ("LINKEDLIST - LIHAT PESANAN", "M1_LL_LIHAT"),
            ("LINKEDLIST - TAMBAH PESANAN REGULER", "M1_LL_TAMBAH_REGULER"),
            ("LINKEDLIST - TAMBAH PESANAN PRIORITAS", "M1_LL_TAMBAH_PRIORITAS"),
            ("LINKEDLIST - TAMBAH PESANAN VIP", "M1_LL_TAMBAH_VIP"),
            ("LINKEDLIST - HAPUS PESANAN", "M1_LL_HAPUS"),
        ]
        for teks, kode in m1_items:
            self._tambah_tombol_nav(isi_menu, teks, kode)

        # Seksi M2: ANTREAN DAN UNDO
        self._tambah_label_grup(isi_menu, "M2 - ANTREAN DAN UNDO")
        m2_items = [
            ("STACK - POSTFIX (MESIN KASIR)", "M2_STACK_POSTFIX"),
            ("QUEUE - ENQUEUE", "M2_QUEUE_ENQUEUE"),
            ("QUEUE - DEQUEUE NAIF", "M2_QUEUE_DEQUEUE_NAIF"),
            ("QUEUE - DEQUEUE CIRCULAR", "M2_QUEUE_DEQUEUE_CIRC"),
            ("STACK - UNDO", "M2_STACK_UNDO"),
            ("STACK - REDO", "M2_STACK_REDO"),
        ]
        for teks, kode in m2_items:
            self._tambah_tombol_nav(isi_menu, teks, kode)

        # Seksi M3: LAPORAN DAN PENCARIAN
        self._tambah_label_grup(isi_menu, "M3 - LAPORAN DAN PENCARIAN")
        m3_items = [
            ("SORT - INSERTION SORT", "M3_SORT_INSERTION"),
            ("SORT - MERGE SORT", "M3_SORT_MERGE"),
            ("SEARCH - LINEAR SEARCH", "M3_SEARCH_LINEAR"),
            ("SEARCH - BINARY SEARCH", "M3_SEARCH_BINARY"),
        ]
        for teks, kode in m3_items:
            self._tambah_tombol_nav(isi_menu, teks, kode)

    def _tambah_label_grup(self, parent, judul):
        lbl = tk.Label(parent, text=judul, font=("Segoe UI", 8, "bold"),
                       bg="#ffffff", fg="#6b7280", anchor="w")
        lbl.pack(fill="x", padx=10, pady=(6, 1))

    def _tambah_tombol_nav(self, parent, teks, kode):
        btn = tk.Button(parent, text=teks,
                        command=lambda k=kode: self._pilih_menu(k),
                        font=("Segoe UI", 8), bg="#ffffff", fg="#374151",
                        activebackground="#e0f2fe", activeforeground="#0369a1",
                        relief="flat", anchor="w", padx=10, pady=2)
        btn.pack(fill="x", padx=6, pady=1)

    def _bangun_area_hasil(self):
        # Tabel Treeview untuk menampilkan daftar pesanan
        self.tree_frame = tk.Frame(self.hasil_container, bg="#ffffff")
        self.tree_frame.pack(fill="both", expand=True)

        cols = ("no", "oid", "pelanggan", "resto", "menu", "harga", "prioritas", "status")
        self.tree = ttk.Treeview(self.tree_frame, columns=cols, show="headings", height=14)

        lebarkolom = [
            ("no", 45), ("oid", 90), ("pelanggan", 180), ("resto", 130),
            ("menu", 130), ("harga", 85), ("prioritas", 70), ("status", 80)
        ]
        for col_name, w in lebarkolom:
            self.tree.heading(col_name, text=col_name.upper())
            self.tree.column(col_name, width=w, anchor="center")

        scroll_tree_y = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_tree_y.set)
        scroll_tree_y.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        # Text area alternatif untuk laporan / detail pencarian / langkah postfix
        self.txt_hasil = tk.Text(self.hasil_container, font=("Consolas", 10),
                                 bg="#ffffff", fg="#1f2937", relief="flat",
                                 padx=10, pady=10)

    def _tampilkan_mode_tabel(self):
        self.txt_hasil.pack_forget()
        self.tree_frame.pack(fill="both", expand=True)

    def _tampilkan_mode_teks(self):
        self.tree_frame.pack_forget()
        self.txt_hasil.pack(fill="both", expand=True)

    def _pilih_menu(self, kode):
        self.active_menu = kode

        # bersihkan form container
        for widget in self.form_container.winfo_children():
            widget.destroy()

        # buat form sesuai menu yang dipilih
        if kode == "M1_ARRAY_TAMBAH_REGULER":
            self.lbl_judul_menu.config(text="Array: Pesanan REGULER (masuk paling belakang)")
            self._buat_form_tambah_pesanan("array", 3)
        elif kode == "M1_ARRAY_TAMBAH_PRIORITAS":
            self.lbl_judul_menu.config(text="Array: Pesanan PRIORITAS (menyerobot ke tengah)")
            self._buat_form_tambah_pesanan("array", 2)
        elif kode == "M1_ARRAY_TAMBAH_VIP":
            self.lbl_judul_menu.config(text="Array: Pesanan VIP (langsung paling depan)")
            self._buat_form_tambah_pesanan("array", 1)
        elif kode == "M1_ARRAY_LIHAT":
            self.lbl_judul_menu.config(text="Array: Lihat Pesanan ke-i (O(1))")
            self._buat_form_lihat_hapus("array", "lihat")
        elif kode == "M1_ARRAY_HAPUS":
            self.lbl_judul_menu.config(text="Array: Hapus Pesanan ke-i (O(n))")
            self._buat_form_lihat_hapus("array", "hapus")

        elif kode == "M1_LL_TAMBAH_REGULER":
            self.lbl_judul_menu.config(text="Linked List: Pesanan REGULER (ujung belakang O(1))")
            self._buat_form_tambah_pesanan("ll", 3)
        elif kode == "M1_LL_TAMBAH_PRIORITAS":
            self.lbl_judul_menu.config(text="Linked List: Pesanan PRIORITAS (tengah O(n))")
            self._buat_form_tambah_pesanan("ll", 2)
        elif kode == "M1_LL_TAMBAH_VIP":
            self.lbl_judul_menu.config(text="Linked List: Pesanan VIP (paling depan O(1))")
            self._buat_form_tambah_pesanan("ll", 1)
        elif kode == "M1_LL_LIHAT":
            self.lbl_judul_menu.config(text="Linked List: Lihat Pesanan ke-i (O(n) telusur)")
            self._buat_form_lihat_hapus("ll", "lihat")
        elif kode == "M1_LL_HAPUS":
            self.lbl_judul_menu.config(text="Linked List: Hapus Pesanan ke-i (O(n) telusur)")
            self._buat_form_lihat_hapus("ll", "hapus")

        elif kode == "M2_STACK_POSTFIX":
            self.lbl_judul_menu.config(text="Stack: Mesin Kasir (Konversi Infix ke Postfix & Hitung Total)")
            self._buat_form_postfix()
        elif kode == "M2_QUEUE_ENQUEUE":
            self.lbl_judul_menu.config(text="Queue: Tambah Pesanan ke Belakang Antrean (Naif & Circular)")
            self._buat_form_enqueue()
        elif kode == "M2_QUEUE_DEQUEUE_NAIF":
            self.lbl_judul_menu.config(text="Queue Naif: Layani Pesanan Depan (Geser Elemen O(n))")
            self._buat_form_dequeue("naif")
        elif kode == "M2_QUEUE_DEQUEUE_CIRC":
            self.lbl_judul_menu.config(text="Queue Circular: Layani Pesanan Depan (Pointer Maju O(1))")
            self._buat_form_dequeue("circ")
        elif kode == "M2_STACK_UNDO":
            self.lbl_judul_menu.config(text="Stack: Undo Aksi Terakhir")
            self._buat_form_undo_redo("undo")
        elif kode == "M2_STACK_REDO":
            self.lbl_judul_menu.config(text="Stack: Redo Aksi Terakhir")
            self._buat_form_undo_redo("redo")

        elif kode == "M3_SORT_INSERTION":
            self.lbl_judul_menu.config(text="Sort: Insertion Sort (Stabil, In-Place, O(n^2), Batas 20.000)")
            self._buat_form_sort("insertion")
        elif kode == "M3_SORT_MERGE":
            self.lbl_judul_menu.config(text="Sort: Merge Sort (Stabil, O(n log n), Skala Penuh 200.000)")
            self._buat_form_sort("merge")
        elif kode == "M3_SEARCH_LINEAR":
            self.lbl_judul_menu.config(text="Search: Linear Search (O(n) telusur dari depan)")
            self._buat_form_search("linear")
        elif kode == "M3_SEARCH_BINARY":
            self.lbl_judul_menu.config(text="Search: Binary Search (O(log n) pada daftar terurut oid)")
            self._buat_form_search("binary")

    # ================= FORM BUILDERS =================

    def _buat_form_tambah_pesanan(self, tipe_struktur, prioritas):
        self._tampilkan_mode_tabel()
        row = tk.Frame(self.form_container, bg="#f9fafb")
        row.pack(fill="x", pady=2)

        lbl_nama = tk.Label(row, text="Nama Pelanggan:", font=("Segoe UI", 9), bg="#f9fafb")
        lbl_nama.pack(side="left", padx=(0, 4))
        ent_nama = tk.Entry(row, width=18, font=("Segoe UI", 9))
        ent_nama.pack(side="left", padx=(0, 10))
        ent_nama.insert(0, "Pelanggan Baru")

        lbl_resto = tk.Label(row, text="Resto:", font=("Segoe UI", 9), bg="#f9fafb")
        lbl_resto.pack(side="left", padx=(0, 4))
        ent_resto = tk.Entry(row, width=14, font=("Segoe UI", 9))
        ent_resto.pack(side="left", padx=(0, 10))
        ent_resto.insert(0, "kantin-pusat")

        lbl_menu = tk.Label(row, text="Menu:", font=("Segoe UI", 9), bg="#f9fafb")
        lbl_menu.pack(side="left", padx=(0, 4))
        ent_menu = tk.Entry(row, width=14, font=("Segoe UI", 9))
        ent_menu.pack(side="left", padx=(0, 10))
        ent_menu.insert(0, "paket-siang")

        lbl_harga = tk.Label(row, text="Harga:", font=("Segoe UI", 9), bg="#f9fafb")
        lbl_harga.pack(side="left", padx=(0, 4))
        ent_harga = tk.Entry(row, width=10, font=("Segoe UI", 9))
        ent_harga.pack(side="left", padx=(0, 10))
        ent_harga.insert(0, "15000")

        def _aksi():
            nama = ent_nama.get().strip()
            resto = ent_resto.get().strip()
            menu = ent_menu.get().strip()
            try:
                harga = int(ent_harga.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Harga harus berupa angka bulat")
                return

            oid_baru = f"O-{len(self.data_mentah) + 1:06d}"
            p = Pesanan(oid_baru, nama, resto, menu, harga, prioritas, int(time.time()), 0, "ANTRE")

            t0 = time.perf_counter()
            if tipe_struktur == "array":
                if prioritas == 3:
                    self.array_pesanan.tambah_reguler(p)
                    cmd = "array_tambah_reguler"
                elif prioritas == 2:
                    self.array_pesanan.tambah_prioritas(p)
                    cmd = "array_tambah_prioritas"
                else:
                    self.array_pesanan.tambah_vip(p)
                    cmd = "array_tambah_vip"
                modul = "M1 - array"
            else:
                if prioritas == 3:
                    self.linklist_pesanan.tambah_reguler(p)
                    cmd = "ll_tambah_reguler"
                elif prioritas == 2:
                    self.linklist_pesanan.tambah_prioritas(p)
                    cmd = "ll_tambah_prioritas"
                else:
                    self.linklist_pesanan.tambah_vip(p)
                    cmd = "ll_tambah_vip"
                modul = "M1 - linkedlist"
            dt = (time.perf_counter() - t0) * 1000

            self.data_mentah.append(p)
            self._catat_command(cmd, f"{p.oid} masuk (P{prioritas})", modul, dt)
            self._tampilkan_daftar([p], append_only=True)

        btn = tk.Button(row, text="TAMBAH", command=_aksi,
                        bg="#10b981", fg="#ffffff", font=("Segoe UI", 9, "bold"),
                        relief="flat", padx=12, pady=2)
        btn.pack(side="left", padx=5)

    def _buat_form_lihat_hapus(self, tipe_struktur, aksi_mode):
        self._tampilkan_mode_tabel()
        row = tk.Frame(self.form_container, bg="#f9fafb")
        row.pack(fill="x", pady=2)

        lbl = tk.Label(row, text="Indeks ke-i:", font=("Segoe UI", 9), bg="#f9fafb")
        lbl.pack(side="left", padx=(0, 5))

        ent_idx = tk.Entry(row, width=10, font=("Segoe UI", 9))
        ent_idx.pack(side="left", padx=(0, 10))
        ent_idx.insert(0, "0")

        def _aksi():
            try:
                i = int(ent_idx.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Indeks harus bilangan bulat")
                return

            t0 = time.perf_counter()
            try:
                if tipe_struktur == "array":
                    if aksi_mode == "lihat":
                        hasil = self.array_pesanan.lihat_pesanan(i)
                        cmd = "array_lihat_pesanan"
                    else:
                        hasil = self.array_pesanan.hapus_pesanan(i)
                        cmd = "array_hapus_pesanan"
                    modul = "M1 - array"
                else:
                    if aksi_mode == "lihat":
                        hasil = self.linklist_pesanan.lihat_pesanan(i)
                        cmd = "ll_lihat_pesanan"
                    else:
                        hasil = self.linklist_pesanan.hapus_pesanan(i)
                        cmd = "ll_hapus_pesanan"
                    modul = "M1 - linkedlist"
                dt = (time.perf_counter() - t0) * 1000

                detail = f"idx {i}: {hasil.oid} ({hasil.pelanggan})"
                self._catat_command(cmd, detail, modul, dt)
                self._tampilkan_daftar([hasil])
            except IndexError:
                messagebox.showerror("Error", f"Indeks {i} di luar jangkauan")

        btn_teks = "LIHAT" if aksi_mode == "lihat" else "HAPUS"
        btn_bg = "#3b82f6" if aksi_mode == "lihat" else "#ef4444"
        btn = tk.Button(row, text=btn_teks, command=_aksi,
                        bg=btn_bg, fg="#ffffff", font=("Segoe UI", 9, "bold"),
                        relief="flat", padx=12, pady=2)
        btn.pack(side="left", padx=5)

    def _buat_form_postfix(self):
        self._tampilkan_mode_teks()
        row = tk.Frame(self.form_container, bg="#f9fafb")
        row.pack(fill="x", pady=2)

        lbl = tk.Label(row, text="Ekspresi Struk:", font=("Segoe UI", 9), bg="#f9fafb")
        lbl.pack(side="left", padx=(0, 5))

        ent_expr = tk.Entry(row, width=42, font=("Consolas", 10))
        ent_expr.pack(side="left", padx=(0, 10))
        ent_expr.insert(0, "( 3 * 12000 ) + ( 2 * 8500 ) - 5000")

        def _aksi():
            expr = ent_expr.get().strip()
            t0 = time.perf_counter()
            postfix_tokens, langkah_pf = ke_postfix(expr)
            total, langkah_ev = hitung_postfix(postfix_tokens)
            dt = (time.perf_counter() - t0) * 1000

            pf_str = " ".join(postfix_tokens)
            self._catat_command("stack_postfix", f"postfix: {pf_str[:25]}... TOTAL: Rp {total:,}", "M2 - stack", dt)

            # Tampilkan detail ke teks hasil persis seperti tabel di halaman 8 PDF
            self.txt_hasil.delete("1.0", "end")
            self.txt_hasil.insert("end", f"=== MESIN KASIR (STACK) ===\n")
            self.txt_hasil.insert("end", f"Infix   : {expr}\n")
            self.txt_hasil.insert("end", f"Postfix : {pf_str}\n")
            self.txt_hasil.insert("end", f"TOTAL   : Rp {total:,}\n\n".replace(",", "."))
            self.txt_hasil.insert("end", f"Tahap 1: Konversi Infix -> Postfix\n")
            self.txt_hasil.insert("end", f"{'-'*65}\n")
            self.txt_hasil.insert("end", f"{'Token':<8} {'Tindakan':<30} {'Stack':<12} {'Keluaran'}\n")
            self.txt_hasil.insert("end", f"{'-'*65}\n")
            for tok, tind, stk, out in langkah_pf:
                self.txt_hasil.insert("end", f"{tok:<8} {tind:<30} {stk:<12} {out}\n")

            self.txt_hasil.insert("end", f"\nTahap 2: Evaluasi Postfix\n")
            self.txt_hasil.insert("end", f"{'-'*65}\n")
            for tok, tind, stk, _ in langkah_ev:
                self.txt_hasil.insert("end", f"{tok:<8} {tind:<30} stack: [{stk}]\n")

        btn = tk.Button(row, text="HITUNG STRUK", command=_aksi,
                        bg="#8b5cf6", fg="#ffffff", font=("Segoe UI", 9, "bold"),
                        relief="flat", padx=12, pady=2)
        btn.pack(side="left", padx=5)

    def _buat_form_enqueue(self):
        self._tampilkan_mode_tabel()
        row = tk.Frame(self.form_container, bg="#f9fafb")
        row.pack(fill="x", pady=2)

        lbl = tk.Label(row, text="Nama Pelanggan:", font=("Segoe UI", 9), bg="#f9fafb")
        lbl.pack(side="left", padx=(0, 5))
        ent = tk.Entry(row, width=20, font=("Segoe UI", 9))
        ent.pack(side="left", padx=(0, 10))
        ent.insert(0, "Pelanggan Baru")

        def _aksi():
            nama = ent.get().strip()
            oid_baru = f"O-{len(self.data_mentah) + 1:06d}"
            p = Pesanan(oid_baru, nama, "resto-antrean", "menu-antrean", 10000, 3, int(time.time()), 0, "ANTRE")
            self.data_mentah.append(p)

            t0 = time.perf_counter()
            self.queue_naif.enqueue(p)
            self.queue_circ.enqueue(p)
            self.undo_redo.catat("enqueue", p)
            dt = (time.perf_counter() - t0) * 1000

            detail = f"{p.oid} masuk belakang kedua antrean"
            self._catat_command("queue_enqueue", detail, "M2 - queue", dt)
            messagebox.showinfo("Enqueue", f"{p.oid} berhasil masuk kedua antrean (Naif & Circular).")

        btn = tk.Button(row, text="ENQUEUE KEDUA ANTREAN", command=_aksi,
                        bg="#2563eb", fg="#ffffff", font=("Segoe UI", 9, "bold"),
                        relief="flat", padx=12, pady=2)
        btn.pack(side="left", padx=5)

    def _buat_form_dequeue(self, versi):
        self._tampilkan_mode_tabel()
        row = tk.Frame(self.form_container, bg="#f9fafb")
        row.pack(fill="x", pady=2)

        lbl = tk.Label(row, text="Jumlah yang dilayani:", font=("Segoe UI", 9), bg="#f9fafb")
        lbl.pack(side="left", padx=(0, 5))

        ent_count = tk.Entry(row, width=8, font=("Segoe UI", 9))
        ent_count.pack(side="left", padx=(0, 10))
        ent_count.insert(0, "1")

        def _aksi():
            try:
                cnt = int(ent_count.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Jumlah harus angka bulat")
                return

            dilayani = []
            total_geser = 0
            t0 = time.perf_counter()

            if versi == "naif":
                for _ in range(cnt):
                    if self.queue_naif.is_empty():
                        break
                    p, gsr = self.queue_naif.dequeue()
                    dilayani.append(p)
                    total_geser += gsr
                dt = (time.perf_counter() - t0) * 1000
                cmd = "queue_dequeue_naive"
                modul = "M2 - queue naif"
                detail = f"{len(dilayani)} keluar | {total_geser:,} elemen digeser".replace(",", ".")
            else:
                for _ in range(cnt):
                    if self.queue_circ.is_empty():
                        break
                    p = self.queue_circ.dequeue()
                    dilayani.append(p)
                dt = (time.perf_counter() - t0) * 1000
                cmd = "queue_dequeue_circular"
                modul = "M2 - queue circular"
                detail = f"{len(dilayani)} keluar | 0 elemen digeser"

            if dilayani:
                self.undo_redo.catat(f"dequeue_{versi}", dilayani)
                self._catat_command(cmd, detail, modul, dt)
                self._tampilkan_daftar(dilayani)
            else:
                messagebox.showinfo("Queue", "Antrean kosong, tidak ada pesanan dilayani.")

        btn_bg = "#d97706" if versi == "naif" else "#059669"
        btn = tk.Button(row, text=f"DEQUEUE ({versi.upper()})", command=_aksi,
                        bg=btn_bg, fg="#ffffff", font=("Segoe UI", 9, "bold"),
                        relief="flat", padx=12, pady=2)
        btn.pack(side="left", padx=5)

    def _buat_form_undo_redo(self, mode):
        self._tampilkan_mode_teks()
        row = tk.Frame(self.form_container, bg="#f9fafb")
        row.pack(fill="x", pady=2)

        def _aksi():
            t0 = time.perf_counter()
            if mode == "undo":
                entry = self.undo_redo.undo_last()
                cmd = "stack_undo"
            else:
                entry = self.undo_redo.redo_last()
                cmd = "stack_redo"
            dt = (time.perf_counter() - t0) * 1000

            if entry is None:
                messagebox.showinfo("Info", f"Tumpukan {mode} kosong, tidak ada yang bisa diproses.")
                self._catat_command(cmd, f"tumpukan {mode} kosong", "M2 - stack", dt)
                return

            aksi, data = entry
            # jalankan efek ke antrean
            if mode == "undo":
                if aksi.startswith("dequeue"):
                    # kembalikan pesanan ke depan antrean circular
                    for p in reversed(data):
                        self.queue_circ.enqueue_front(p)
                    detail = f"{len(data)} pesanan dikembalikan ke DEPAN circular"
                elif aksi == "enqueue":
                    # keluarkan pesanan dari belakang
                    # (pada circular queue, count berkurang & rear mundur)
                    self.queue_circ.count -= 1
                    self.queue_circ.rear = (self.queue_circ.rear - 1) % self.queue_circ.capacity
                    detail = f"{data.oid} dikeluarkan lagi dari belakang"
            else:
                # redo: jalankan aksi semula
                if aksi.startswith("dequeue"):
                    for _ in range(len(data)):
                        self.queue_circ.dequeue()
                    detail = f"{len(data)} pesanan dikeluarkan lagi"
                elif aksi == "enqueue":
                    self.queue_circ.enqueue(data)
                    detail = f"{data.oid} dimasukkan kembali ke belakang"

            self._catat_command(cmd, detail, "M2 - stack", dt)
            self.txt_hasil.delete("1.0", "end")
            self.txt_hasil.insert("end", f"Status Undo/Redo:\n")
            self.txt_hasil.insert("end", f"Aksi diproses : {aksi}\n")
            self.txt_hasil.insert("end", f"Keterangan    : {detail}\n")
            self.txt_hasil.insert("end", f"Kedalaman Undo: {self.undo_redo.undo_depth}\n")
            self.txt_hasil.insert("end", f"Kedalaman Redo: {self.undo_redo.redo_depth}\n")
            self.txt_hasil.insert("end", f"Panjang Queue : {len(self.queue_circ)}\n")

        btn_bg = "#64748b" if mode == "undo" else "#475569"
        btn = tk.Button(row, text=f"JALANKAN {mode.upper()}", command=_aksi,
                        bg=btn_bg, fg="#ffffff", font=("Segoe UI", 9, "bold"),
                        relief="flat", padx=14, pady=2)
        btn.pack(side="left", padx=5)

    def _buat_form_sort(self, algo):
        self._tampilkan_mode_tabel()
        row = tk.Frame(self.form_container, bg="#f9fafb")
        row.pack(fill="x", pady=2)

        lbl_kunci = tk.Label(row, text="Kunci:", font=("Segoe UI", 9), bg="#f9fafb")
        lbl_kunci.pack(side="left", padx=(0, 4))

        cmb_kunci = ttk.Combobox(row, values=["harga", "oid", "selesai"], width=8, state="readonly")
        cmb_kunci.set("harga")
        cmb_kunci.pack(side="left", padx=(0, 10))

        lbl_n = tk.Label(row, text="Jumlah baris:", font=("Segoe UI", 9), bg="#f9fafb")
        lbl_n.pack(side="left", padx=(0, 4))

        ent_n = tk.Entry(row, width=9, font=("Segoe UI", 9))
        ent_n.pack(side="left", padx=(0, 10))
        default_n = "2000" if algo == "insertion" else "4000"
        ent_n.insert(0, default_n)

        def _aksi():
            if not self.data_mentah:
                messagebox.showwarning("Peringatan", "Muat data pesanan.csv terlebih dahulu.")
                return

            try:
                n = int(ent_n.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Jumlah baris harus angka bulat")
                return

            kunci_nama = cmb_kunci.get()
            if kunci_nama == "harga":
                fn_kunci = by_harga
            elif kunci_nama == "oid":
                fn_kunci = by_oid
            else:
                fn_kunci = by_selesai

            # ambil cuplikan data
            sample = [self.data_mentah[i] for i in range(min(n, len(self.data_mentah)))]

            t0 = time.perf_counter()
            if algo == "insertion":
                hasil, comp, move, err = insertion_sort(sample, fn_kunci)
                dt = (time.perf_counter() - t0) * 1000
                if err:
                    self._catat_command("insertion_sort", f"jumlah={n} | {err}", "M3 - insertion sort", dt)
                    messagebox.showwarning("Ditolak", err)
                    return
                cmd = "insertion_sort"
                modul = "M3 - insertion sort"
            else:
                hasil, comp, move, err = merge_sort(sample, fn_kunci)
                dt = (time.perf_counter() - t0) * 1000
                cmd = "merge_sort"
                modul = "M3 - merge sort"

            detail = f"{len(hasil):,} pesanan terurut | {comp:,} perbandingan".replace(",", ".")
            self._catat_command(cmd, detail, modul, dt)
            self._tampilkan_daftar(hasil[:200]) # tampilkan 200 teratas ke tabel

        btn = tk.Button(row, text=f"JALANKAN {algo.upper()} SORT", command=_aksi,
                        bg="#7c3aed", fg="#ffffff", font=("Segoe UI", 9, "bold"),
                        relief="flat", padx=12, pady=2)
        btn.pack(side="left", padx=5)

    def _buat_form_search(self, algo):
        self._tampilkan_mode_teks()
        row = tk.Frame(self.form_container, bg="#f9fafb")
        row.pack(fill="x", pady=2)

        lbl = tk.Label(row, text="Target OID:", font=("Segoe UI", 9), bg="#f9fafb")
        lbl.pack(side="left", padx=(0, 5))

        ent_target = tk.Entry(row, width=14, font=("Segoe UI", 9))
        ent_target.pack(side="left", padx=(0, 10))
        ent_target.insert(0, "O-137442")

        def _aksi():
            if not self.data_mentah:
                messagebox.showwarning("Peringatan", "Muat data pesanan.csv terlebih dahulu.")
                return

            target = ent_target.get().strip()

            if algo == "linear":
                t0 = time.perf_counter()
                idx, comp = linear_search(self.data_mentah, target, by_oid)
                dt = (time.perf_counter() - t0) * 1000

                if idx != -1:
                    detail = f"ditemukan di indeks {idx:,} | {comp:,} perbandingan".replace(",", ".")
                    p = self.data_mentah[idx]
                    info_pesanan = f"\nDetail Pesanan:\nOID       : {p.oid}\nPelanggan : {p.pelanggan}\nResto     : {p.resto}\nMenu      : {p.menu}\nHarga     : Rp {p.harga:,}\nPrioritas : {p.prioritas}\nStatus    : {p.status}\n".replace(",", ".")
                else:
                    detail = f"tidak ditemukan | {comp:,} perbandingan".replace(",", ".")
                    info_pesanan = "\nPesanan tidak ditemukan dalam dataset."

                self._catat_command("linear_search", f"{target} | {detail}", "M3 - linear", dt)

                self.txt_hasil.delete("1.0", "end")
                self.txt_hasil.insert("end", f"=== HASIL LINEAR SEARCH ===\n")
                self.txt_hasil.insert("end", f"Target OID       : {target}\n")
                self.txt_hasil.insert("end", f"Jumlah Baris     : {len(self.data_mentah):,}\n".replace(",", "."))
                self.txt_hasil.insert("end", f"Hasil            : {detail}\n")
                self.txt_hasil.insert("end", f"Waktu Eksekusi   : {dt:.2f} ms\n")
                self.txt_hasil.insert("end", info_pesanan)

            else: # binary search
                # butuh daftar terurut by oid (dibangun sekali memakai merge sort)
                if self.oid_sorted_cache is None:
                    t_build0 = time.perf_counter()
                    sorted_list, _, _, _ = merge_sort(list(self.data_mentah), by_oid)
                    self.oid_sorted_time_ms = (time.perf_counter() - t_build0) * 1000
                    self.oid_sorted_cache = sorted_list
                    self._catat_command("build_sorted_oid", f"dibangun sekali (merge sort)", "M3 - binary prep", self.oid_sorted_time_ms)

                t0 = time.perf_counter()
                idx, comp = binary_search(self.oid_sorted_cache, target, by_oid)
                dt = (time.perf_counter() - t0) * 1000

                if idx != -1:
                    detail = f"ditemukan di baris {idx + 1:,} | {comp} perbandingan".replace(",", ".")
                    p = self.oid_sorted_cache[idx]
                    info_pesanan = f"\nDetail Pesanan:\nOID       : {p.oid}\nPelanggan : {p.pelanggan}\nResto     : {p.resto}\nMenu      : {p.menu}\nHarga     : Rp {p.harga:,}\nPrioritas : {p.prioritas}\nStatus    : {p.status}\n".replace(",", ".")
                else:
                    detail = f"tidak ditemukan | {comp} perbandingan"
                    info_pesanan = "\nPesanan tidak ditemukan dalam dataset."

                self._catat_command("binary_search", f"{target} | {detail}", "M3 - binary", dt)

                self.txt_hasil.delete("1.0", "end")
                self.txt_hasil.insert("end", f"=== HASIL BINARY SEARCH ===\n")
                self.txt_hasil.insert("end", f"Target OID       : {target}\n")
                self.txt_hasil.insert("end", f"Waktu Bangun OID : {self.oid_sorted_time_ms:.2f} ms (merge sort sekali)\n")
                self.txt_hasil.insert("end", f"Hasil            : {detail}\n")
                self.txt_hasil.insert("end", f"Waktu Pencarian  : {dt:.2f} ms\n")
                self.txt_hasil.insert("end", info_pesanan)

        btn = tk.Button(row, text=f"CARI OID ({algo.upper()})", command=_aksi,
                        bg="#0284c7", fg="#ffffff", font=("Segoe UI", 9, "bold"),
                        relief="flat", padx=12, pady=2)
        btn.pack(side="left", padx=5)

    # ================= AKSI UTAMA =================

    def _aksi_load_csv(self):
        lokasi_default = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "pesanan.csv")
        if os.path.exists(lokasi_default):
            path = lokasi_default
        else:
            path = filedialog.askopenfilename(
                title="Pilih file pesanan.csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
            )

        if not path:
            return

        self.root.config(cursor="watch")
        self.root.update()

        t0 = time.perf_counter()
        raw = load_pesanan(path)
        dt = (time.perf_counter() - t0) * 1000

        self.data_mentah = raw
        self.oid_sorted_cache = None # reset cache

        # masukkan ke Array M1
        self.array_pesanan = Array(len(raw) + 10)
        for p in raw:
            self.array_pesanan.append(p)

        # masukkan ke LinkList M1 (cuplikan 5000 awal agar hemat memori)
        self.linklist_pesanan = LinkList()
        batas_ll = min(len(raw), 5000)
        for i in range(batas_ll):
            self.linklist_pesanan.append(raw[i])

        # masukkan pesanan berstatus ANTRE ke M2 queue
        self.queue_naif = AntreanNaif()
        self.queue_circ = AntreanMelingkar()
        antre_count = 0
        for p in raw:
            if p.status == "ANTRE":
                self.queue_naif.enqueue(p)
                self.queue_circ.enqueue(p)
                antre_count += 1

        self.root.config(cursor="")
        self.lbl_info_data.config(text=f"Data: {len(raw):,} baris | Antre: {antre_count:,}".replace(",", "."))
        self._catat_command("load_csv", f"{len(raw):,} pesanan ({antre_count:,} ANTRE)", "DATA", dt)

        self._tampilkan_daftar(raw[:200])
        messagebox.showinfo("Sukses", f"Berhasil memuat {len(raw):,} data pesanan.\n{antre_count:,} pesanan dimasukkan ke antrean M2.")

    def _tampilkan_daftar(self, list_pesanan, append_only=False):
        if not append_only:
            for item in self.tree.get_children():
                self.tree.delete(item)

        for i, p in enumerate(list_pesanan):
            no = i + 1
            hrg_fmt = f"Rp {p.harga:,}".replace(",", ".")
            self.tree.insert("", "end", values=(
                no, p.oid, p.pelanggan, p.resto, p.menu, hrg_fmt, p.prioritas, p.status
            ))
