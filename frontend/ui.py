# ui.py
# tampilan antarmuka tkinter untuk proyek 2EZ4U
# tata letak presisi sesuai spesifikasi modul & referensi desain:
# 1. header biru tua atas
# 2. sidebar kiri dengan tombol kotak berbingkai solid & kategori M1-M4
# 3. panel form dinamis di kanan atas + kotak notifikasi status
# 4. tabbed view: [Tabel Semua Pesanan] [Log & Adu Performa] [Transkrip Postfix Kasir]
# 5. pagination bar: navigasi halaman, ukuran tampil, filter sumber data
# 6. command panel bawah: baris input perintah interaktif + riwayat log
# 7. status bar bawah dengan badge runtime & ringkasan dataset
# DILARANG MENGGUNAKAN dict, set, sorted, .sort(), literal {}, collections.*, heapq, bisect.

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
        self.root.title("2EZ4U Food Delivery")
        self.root.geometry("1200x760")
        self.root.minsize(1050, 680)
        self.root.configure(bg="#f1f5f9")

        # dataset backend
        self.data_mentah = []              # list seluruh pesanan (M1)
        self.array_pesanan = Array(4)      # M1: Array dinamis
        self.linklist_pesanan = LinkList() # M1: Singly Linked list
        self.queue_naif = AntreanNaif()    # M2: Antrean naif O(n)
        self.queue_circ = AntreanMelingkar() # M2: Antrean circular O(1)
        self.undo_redo = UndoRedo()        # M2: Undo/redo stack

        self.data_terurut = []             # M3: hasil pengurutan terakhir
        self.oid_sorted_cache = None       # M3: cache terurut oid untuk binary search
        self.oid_sorted_time_ms = 0.0

        # state pagination & tampilan tabel
        self.sumber_data_aktif = "M1"      # "M1", "M2", "M3"
        self.halaman_aktif = 1
        self.ukuran_halaman = 100          # 100, 500, atau -1 (semua)
        self.baris_disorot = -1

        # state menu tombol aktif
        self.menu_aktif = "M1_ARRAY_LIHAT"
        self.dict_tombol = []              # list pasangan (kode, button_widget)

        # bangun tata letak
        self._bangun_komponen_utama()

        # muat data awal secara otomatis jika pesanan.csv ada
        self.root.after(100, self._muat_data_otomatis)

    # ================= 1. TATA LETAK UTAMA =================

    def _bangun_komponen_utama(self):
        # 1. Header Atas Biru Tua
        self.header = tk.Frame(self.root, bg="#16324f", height=42)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        lbl_judul = tk.Label(self.header, text="2EZ4U Food Delivery",
                             font=("Segoe UI", 12, "bold"),
                             bg="#16324f", fg="#ffffff")
        lbl_judul.pack(side="left", padx=14, pady=8)

        self.lbl_header_info = tk.Label(self.header, text="Data: memuat...",
                                        font=("Segoe UI", 9),
                                        bg="#16324f", fg="#cbd5e1")
        self.lbl_header_info.pack(side="right", padx=14)

        # 2. Status Bar Paling Bawah
        self.statusbar = tk.Frame(self.root, bg="#e2e8f0", height=24,
                                  highlightbackground="#cbd5e1", highlightthickness=1)
        self.statusbar.pack(fill="x", side="bottom")
        self.statusbar.pack_propagate(False)

        self.badge_runtime = tk.Label(self.statusbar, text="[M1-M3 Inisialisasi]",
                                      font=("Segoe UI", 8, "bold"),
                                      bg="#0f172a", fg="#38bdf8", padx=8)
        self.badge_runtime.pack(side="left", fill="y")

        self.lbl_status_teks = tk.Label(self.statusbar,
                                        text="Total: 0 pesanan | Antrean: 0 pesanan | M3 Siap",
                                        font=("Segoe UI", 8),
                                        bg="#e2e8f0", fg="#334155")
        self.lbl_status_teks.pack(side="left", padx=10)

        # 3. Panel COMMAND Bawah
        self.frame_cmd = tk.Frame(self.root, bg="#ffffff", height=155,
                                  highlightbackground="#94a3b8", highlightthickness=1)
        self.frame_cmd.pack(fill="x", side="bottom", padx=8, pady=(0, 4))
        self.frame_cmd.pack_propagate(False)

        self._bangun_panel_command()

        # 4. Area Tengah (Sidebar Kiri + Konten Kanan)
        tengah = tk.Frame(self.root, bg="#f1f5f9")
        tengah.pack(fill="both", expand=True, padx=8, pady=(6, 4))

        # 4a. Sidebar Kiri
        self.frame_sidebar = tk.Frame(tengah, bg="#ffffff", width=235,
                                      highlightbackground="#94a3b8", highlightthickness=1)
        self.frame_sidebar.pack(side="left", fill="y", padx=(0, 6))
        self.frame_sidebar.pack_propagate(False)

        self._bangun_sidebar()

        # 4b. Konten Kanan
        self.frame_konten = tk.Frame(tengah, bg="#f1f5f9")
        self.frame_konten.pack(side="left", fill="both", expand=True)

        self._bangun_area_konten()

    # ================= 2. SIDEBAR NAVIGASI KIRI =================

    def _bangun_sidebar(self):
        # canvas scrollable untuk sidebar
        scroll_bar = tk.Scrollbar(self.frame_sidebar, orient="vertical")
        scroll_bar.pack(side="right", fill="y")

        self.canvas_sidebar = tk.Canvas(self.frame_sidebar, bg="#ffffff",
                                        highlightthickness=0, yscrollcommand=scroll_bar.set)
        self.canvas_sidebar.pack(side="left", fill="both", expand=True)
        scroll_bar.config(command=self.canvas_sidebar.yview)

        self.isi_sidebar = tk.Frame(self.canvas_sidebar, bg="#ffffff")
        self.win_sidebar = self.canvas_sidebar.create_window((0, 0), window=self.isi_sidebar,
                                                             anchor="nw", width=220)

        def _on_cfg(e):
            self.canvas_sidebar.configure(scrollregion=self.canvas_sidebar.bbox("all"))
        self.isi_sidebar.bind("<Configure>", _on_cfg)

        def _on_wheel(e):
            self.canvas_sidebar.yview_scroll(int(-1 * (e.delta / 120)), "units")
        self.canvas_sidebar.bind("<MouseWheel>", _on_wheel)
        self.isi_sidebar.bind("<MouseWheel>", _on_wheel)

        # --- DATA ---
        self._tambah_header_sidebar("DATA")
        btn_load = tk.Button(self.isi_sidebar, text="Load",
                             command=self._aksi_load_csv_dialog,
                             font=("Segoe UI", 8), bg="#ffffff", fg="#000000",
                             relief="solid", bd=1, anchor="w", padx=8, pady=2)
        btn_load.pack(fill="x", padx=8, pady=(1, 6))

        # --- M1 - DATA PESANAN ---
        self._tambah_header_sidebar("M1 - DATA PESANAN")
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
            ("ADU PERFORMA ARRAY VS LINKEDLIST", "M1_BENCHMARK"),
        ]
        for teks, kode in m1_items:
            self._tambah_tombol_sidebar(teks, kode)

        # --- M2 - ANTREAN & TUMPUKAN ---
        self._tambah_header_sidebar("M2 - ANTREAN & TUMPUKAN")
        m2_items = [
            ("STACK - POSTFIX (MESIN KASIR)", "M2_STACK_POSTFIX"),
            ("QUEUE - ENQUEUE", "M2_QUEUE_ENQUEUE"),
            ("QUEUE - DEQUEUE NAIF", "M2_QUEUE_DEQUEUE_NAIF"),
            ("QUEUE - DEQUEUE CIRCULAR", "M2_QUEUE_DEQUEUE_CIRC"),
            ("STACK - UNDO", "M2_STACK_UNDO"),
            ("STACK - REDO", "M2_STACK_REDO"),
            ("ADU PERFORMA DEQUEUE NAIF VS CIRCULAR", "M2_BENCHMARK"),
        ]
        for teks, kode in m2_items:
            self._tambah_tombol_sidebar(teks, kode)

        # --- M3 - SORT & SEARCH (LAPORAN) ---
        self._tambah_header_sidebar("M3 - SORT & SEARCH (LAPORAN)")
        m3_items = [
            ("SORT - INSERTION SORT", "M3_SORT_INSERTION"),
            ("SORT - MERGE SORT", "M3_SORT_MERGE"),
            ("SEARCH - LINEAR SEARCH", "M3_SEARCH_LINEAR"),
            ("SEARCH - BINARY SEARCH", "M3_SEARCH_BINARY"),
            ("Laporan harian", "M3_LAPORAN_HARIAN"),
            ("Cari di laporan", "M3_CARI_LAPORAN"),
            ("ADU PERFORMA SORT & SEARCH (M3)", "M3_BENCHMARK"),
        ]
        for teks, kode in m3_items:
            self._tambah_tombol_sidebar(teks, kode)

        # --- M4 - PENCARIAN HASH ---
        self._tambah_header_sidebar("M4 - PENCARIAN HASH")

    def _tambah_header_sidebar(self, teks):
        lbl = tk.Label(self.isi_sidebar, text=teks,
                       font=("Segoe UI", 8, "bold"),
                       bg="#ffffff", fg="#64748b", anchor="w")
        lbl.pack(fill="x", padx=8, pady=(7, 2))

    def _tambah_tombol_sidebar(self, teks, kode):
        btn = tk.Button(self.isi_sidebar, text=teks,
                        command=lambda k=kode: self._ganti_menu(k),
                        font=("Segoe UI", 7, "bold"), bg="#ffffff", fg="#1e293b",
                        relief="solid", bd=1, anchor="w", padx=6, pady=2)
        btn.pack(fill="x", padx=8, pady=1)
        self.dict_tombol.append((kode, btn))

    def _update_highlight_sidebar(self):
        for k, btn in self.dict_tombol:
            if k == self.menu_aktif:
                btn.config(bg="#d8e6f3", fg="#0f172a", relief="solid")
            else:
                btn.config(bg="#ffffff", fg="#1e293b", relief="solid")

    # ================= 3. AREA KONTEN KANAN =================

    def _bangun_area_konten(self):
        # 3a. Judul Menu & Form Dinamis
        self.frame_form_top = tk.Frame(self.frame_konten, bg="#ffffff",
                                       highlightbackground="#cbd5e1", highlightthickness=1)
        self.frame_form_top.pack(fill="x", side="top", pady=(0, 6))

        self.lbl_judul_aksi = tk.Label(self.frame_form_top, text="",
                                       font=("Segoe UI", 11, "bold"),
                                       bg="#ffffff", fg="#0f172a")
        self.lbl_judul_aksi.pack(anchor="w", padx=12, pady=(6, 1))

        self.lbl_sub_aksi = tk.Label(self.frame_form_top, text="",
                                     font=("Segoe UI", 8, "italic"),
                                     bg="#ffffff", fg="#475569")
        self.lbl_sub_aksi.pack(anchor="w", padx=12, pady=(0, 4))

        # Kontainer input dinamis
        self.kontainer_input = tk.Frame(self.frame_form_top, bg="#ffffff")
        self.kontainer_input.pack(fill="x", padx=12, pady=(2, 4))

        self.lbl_helper_input = tk.Label(self.frame_form_top, text="",
                                         font=("Segoe UI", 8, "italic"),
                                         bg="#ffffff", fg="#64748b")
        self.lbl_helper_input.pack(anchor="w", padx=12, pady=(0, 4))

        # Kotak Notifikasi / Banner Status (seperti di gambar)
        self.banner_status = tk.Frame(self.frame_form_top, bg="#f8fafc",
                                      highlightbackground="#e2e8f0", highlightthickness=1)
        self.banner_status.pack(fill="x", padx=12, pady=(2, 8))

        self.lbl_banner_teks = tk.Label(
            self.banner_status,
            text="Memuat dataset pesanan.csv...",
            font=("Segoe UI", 8), bg="#f8fafc", fg="#1e293b", anchor="w"
        )
        self.lbl_banner_teks.pack(fill="x", padx=8, pady=4)

        # 3b. Tabbed View Notebook
        self.notebook = ttk.Notebook(self.frame_konten)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Tabel Semua Pesanan
        self.tab_tabel = tk.Frame(self.notebook, bg="#ffffff")
        self.notebook.add(self.tab_tabel, text="📋 Tabel Semua Pesanan")

        self._bangun_tab_tabel()

        # Tab 2: Log & Adu Performa
        self.tab_log = tk.Frame(self.notebook, bg="#ffffff")
        self.notebook.add(self.tab_log, text="⚡ Log & Adu Performa")

        self._bangun_tab_log()

        # Tab 3: Transkrip Postfix Kasir
        self.tab_postfix = tk.Frame(self.notebook, bg="#ffffff")
        self.notebook.add(self.tab_postfix, text="🧾 Transkrip Postfix Kasir")

        self._bangun_tab_postfix()

    def _bangun_tab_tabel(self):
        # Frame Treeview
        frame_tree = tk.Frame(self.tab_tabel, bg="#ffffff")
        frame_tree.pack(fill="both", expand=True)

        scroll_y = ttk.Scrollbar(frame_tree, orient="vertical")
        scroll_x = ttk.Scrollbar(frame_tree, orient="horizontal")

        cols = ("oid", "pelanggan", "resto", "menu", "harga", "prioritas",
                "t_masuk_detik", "t_selesai_detik", "status")
        self.tree = ttk.Treeview(frame_tree, columns=cols, show="headings",
                                 yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set,
                                 selectmode="browse")

        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)

        col_config = [
            ("oid", "oid", 80),
            ("pelanggan", "pelanggan", 170),
            ("resto", "resto", 120),
            ("menu", "menu", 120),
            ("harga", "harga", 80),
            ("prioritas", "prioritas", 65),
            ("t_masuk_detik", "t_masuk_detik", 100),
            ("t_selesai_detik", "t_selesai_detik", 100),
            ("status", "status", 80),
        ]
        for col_id, col_name, w in col_config:
            self.tree.heading(col_id, text=col_name)
            self.tree.column(col_id, width=w, anchor="center")

        # style baris disorot
        self.tree.tag_configure("sorot", background="#fef08a", foreground="#000000")

        # Pagination & Filter Bar di bawah tabel persis seperti di gambar
        self.bar_halaman = tk.Frame(self.tab_tabel, bg="#f8fafc", height=32,
                                    highlightbackground="#cbd5e1", highlightthickness=1)
        self.bar_halaman.pack(fill="x", side="bottom")

        btn_awal = tk.Button(self.bar_halaman, text="⏮ Awal", font=("Segoe UI", 7),
                             command=self._hal_awal, relief="groove", bd=1, padx=4)
        btn_awal.pack(side="left", padx=(6, 2), pady=3)

        btn_prev = tk.Button(self.bar_halaman, text="◀ Sebelumnya", font=("Segoe UI", 7),
                             command=self._hal_prev, relief="groove", bd=1, padx=4)
        btn_prev.pack(side="left", padx=2, pady=3)

        self.lbl_indikator_hal = tk.Label(self.bar_halaman, text="Halaman 1 / 1",
                                          font=("Segoe UI", 8, "bold"),
                                          bg="#f8fafc", fg="#0f172a")
        self.lbl_indikator_hal.pack(side="left", padx=6)

        btn_next = tk.Button(self.bar_halaman, text="Berikutnya ▶", font=("Segoe UI", 7),
                             command=self._hal_next, relief="groove", bd=1, padx=4)
        btn_next.pack(side="left", padx=2, pady=3)

        btn_akhir = tk.Button(self.bar_halaman, text="Akhir ⏭", font=("Segoe UI", 7),
                              command=self._hal_akhir, relief="groove", bd=1, padx=4)
        btn_akhir.pack(side="left", padx=2, pady=3)

        sep1 = tk.Label(self.bar_halaman, text="|  Tampilkan:", font=("Segoe UI", 8),
                        bg="#f8fafc", fg="#64748b")
        sep1.pack(side="left", padx=(8, 4))

        self.btn_limit_100 = tk.Button(self.bar_halaman, text="100", font=("Segoe UI", 7),
                                       command=lambda: self._set_limit(100), relief="groove", bd=1, padx=4)
        self.btn_limit_100.pack(side="left", padx=1)

        self.btn_limit_500 = tk.Button(self.bar_halaman, text="500", font=("Segoe UI", 7),
                                       command=lambda: self._set_limit(500), relief="groove", bd=1, padx=4)
        self.btn_limit_500.pack(side="left", padx=1)

        self.btn_limit_semua = tk.Button(self.bar_halaman, text="Semua Data", font=("Segoe UI", 7),
                                         command=lambda: self._set_limit(-1), relief="groove", bd=1, padx=4)
        self.btn_limit_semua.pack(side="left", padx=1)

        sep2 = tk.Label(self.bar_halaman, text="|  Sumber Data:", font=("Segoe UI", 8),
                        bg="#f8fafc", fg="#64748b")
        sep2.pack(side="left", padx=(8, 4))

        self.btn_src_m1 = tk.Button(self.bar_halaman, text="M1 (Semua)", font=("Segoe UI", 7),
                                    command=lambda: self._ganti_sumber_data("M1"), relief="solid", bd=1, padx=4)
        self.btn_src_m1.pack(side="left", padx=1)

        self.btn_src_m2 = tk.Button(self.bar_halaman, text="M2 (Antrean)", font=("Segoe UI", 7),
                                    command=lambda: self._ganti_sumber_data("M2"), relief="groove", bd=1, padx=4)
        self.btn_src_m2.pack(side="left", padx=1)

        self.btn_src_m3 = tk.Button(self.bar_halaman, text="M3 (Terurut)", font=("Segoe UI", 7),
                                    command=lambda: self._ganti_sumber_data("M3"), relief="groove", bd=1, padx=4)
        self.btn_src_m3.pack(side="left", padx=1)

        self.lbl_ringkasan_baris = tk.Label(self.bar_halaman, text="[M1 (Semua)] 0 data",
                                            font=("Segoe UI", 8), bg="#f8fafc", fg="#64748b")
        self.lbl_ringkasan_baris.pack(side="right", padx=10)

    def _bangun_tab_log(self):
        scroll_log = tk.Scrollbar(self.tab_log, orient="vertical")
        scroll_log.pack(side="right", fill="y")

        self.txt_log = tk.Text(self.tab_log, font=("Consolas", 9),
                               bg="#ffffff", fg="#0f172a",
                               yscrollcommand=scroll_log.set, relief="flat", padx=12, pady=10)
        self.txt_log.pack(fill="both", expand=True)
        scroll_log.config(command=self.txt_log.yview)

    def _bangun_tab_postfix(self):
        scroll_pf = tk.Scrollbar(self.tab_postfix, orient="vertical")
        scroll_pf.pack(side="right", fill="y")

        self.txt_postfix = tk.Text(self.tab_postfix, font=("Consolas", 9),
                                   bg="#ffffff", fg="#0f172a",
                                   yscrollcommand=scroll_pf.set, relief="flat", padx=12, pady=10)
        self.txt_postfix.pack(fill="both", expand=True)
        scroll_pf.config(command=self.txt_postfix.yview)

    # ================= 4. PANEL COMMAND (BAWAH) =================

    def _bangun_panel_command(self):
        # Judul panel
        lbl_cmd = tk.Label(self.frame_cmd,
                           text="COMMAND (Konsol Perintah Interaktif & Riwayat)",
                           font=("Segoe UI", 8, "bold"),
                           bg="#ffffff", fg="#1e293b", anchor="w")
        lbl_cmd.pack(fill="x", padx=8, pady=(4, 2))

        # Baris input interaktif
        bar_input = tk.Frame(self.frame_cmd, bg="#ffffff")
        bar_input.pack(fill="x", padx=8, pady=(0, 4))

        lbl_prompt = tk.Label(bar_input, text=">", font=("Consolas", 10, "bold"),
                              bg="#ffffff", fg="#0284c7")
        lbl_prompt.pack(side="left", padx=(0, 4))

        self.ent_cmd_input = tk.Entry(bar_input, font=("Consolas", 9),
                                      relief="solid", bd=1)
        self.ent_cmd_input.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.ent_cmd_input.bind("<Return>", lambda e: self._eksekusi_command_input())

        btn_jalankan = tk.Button(bar_input, text="JALANKAN",
                                 command=self._eksekusi_command_input,
                                 font=("Segoe UI", 7, "bold"),
                                 bg="#16324f", fg="#ffffff", relief="flat", padx=10, pady=2)
        btn_jalankan.pack(side="right")

        # Riwayat teks perintah
        frame_hist = tk.Frame(self.frame_cmd, bg="#ffffff")
        frame_hist.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        scroll_cmd = tk.Scrollbar(frame_hist, orient="vertical")
        scroll_cmd.pack(side="right", fill="y")

        self.txt_cmd_hist = tk.Text(frame_hist, font=("Consolas", 9),
                                    bg="#ffffff", fg="#0f172a",
                                    yscrollcommand=scroll_cmd.set,
                                    relief="solid", bd=1, height=4)
        self.txt_cmd_hist.pack(side="left", fill="both", expand=True)
        scroll_cmd.config(command=self.txt_cmd_hist.yview)

    def _catat_log(self, baris_teks):
        self.txt_cmd_hist.insert("end", baris_teks + "\n")
        self.txt_cmd_hist.see("end")

    # ================= 5. SISTEM FORM DINAMIS =================

    def _ganti_menu(self, kode):
        self.menu_aktif = kode
        self._update_highlight_sidebar()

        for w in self.kontainer_input.winfo_children():
            w.destroy()

        if kode == "M1_ARRAY_LIHAT":
            self.lbl_judul_aksi.config(text="Array: Lihat Data Pesanan (Tabel Lengkap)")
            self.lbl_sub_aksi.config(text="Melihat seluruh daftar pesanan secara terstruktur atau melompat ke indeks ke-i (O(1)).")
            self.lbl_helper_input.config(text="masukkan nomor indeks (0 s/d n-1) untuk menguji kecepatan akses dan menyorot baris pada tabel di bawah")

            lbl_idx = tk.Label(self.kontainer_input, text="Lompat ke Indeks (ke-i):",
                               font=("Segoe UI", 8, "bold"), bg="#ffffff")
            lbl_idx.pack(side="left", padx=(0, 6))

            ent_idx = tk.Entry(self.kontainer_input, width=8, font=("Segoe UI", 8), relief="solid", bd=1)
            ent_idx.pack(side="left", padx=(0, 8))
            ent_idx.insert(0, "0")

            def _aksi_sorot():
                try:
                    i = int(ent_idx.get().strip())
                except ValueError:
                    messagebox.showerror("Error", "Indeks harus bilangan bulat")
                    return
                t0 = time.perf_counter()
                try:
                    p = self.array_pesanan.lihat_pesanan(i)
                    dt = (time.perf_counter() - t0) * 1000
                    self._catat_log(f"array_lihat         -> idx {i}: {p.oid} ({p.pelanggan})   {dt:6.2f} ms")
                    self._lompat_ke_indeks(i)
                except IndexError:
                    messagebox.showerror("Error", f"Indeks {i} di luar rentang!")

            btn_cari = tk.Button(self.kontainer_input, text="CARI & SOROT",
                                 command=_aksi_sorot,
                                 font=("Segoe UI", 8, "bold"),
                                 bg="#0d47a1", fg="#ffffff", relief="flat", padx=10, pady=2)
            btn_cari.pack(side="left", padx=(0, 6))

            btn_semua = tk.Button(self.kontainer_input, text="TAMPILKAN SEMUA DATA",
                                  command=lambda: self._set_limit(-1),
                                  font=("Segoe UI", 8, "bold"),
                                  bg="#0288d1", fg="#ffffff", relief="flat", padx=10, pady=2)
            btn_semua.pack(side="left")

        elif kode.startswith("M1_ARRAY_TAMBAH") or kode.startswith("M1_LL_TAMBAH"):
            tipe = "Array" if "ARRAY" in kode else "Linked List"
            if "REGULER" in kode:
                prio = 3
                pos = "REGULER (masuk paling belakang)"
            elif "PRIORITAS" in kode:
                prio = 2
                pos = "PRIORITAS (menyerobot ke tengah n/2)"
            else:
                prio = 1
                pos = "VIP (langsung paling depan / indeks 0)"

            self.lbl_judul_aksi.config(text=f"{tipe}: Tambah Pesanan {pos}")
            self.lbl_sub_aksi.config(text=f"Menambahkan data pesanan baru ke dalam struktur data {tipe}.")
            self.lbl_helper_input.config(text="Isi data pelanggan, resto, menu, harga, lalu tekan tombol TAMBAH.")

            lbl_n = tk.Label(self.kontainer_input, text="Nama:", font=("Segoe UI", 8), bg="#ffffff")
            lbl_n.pack(side="left", padx=(0, 2))
            ent_n = tk.Entry(self.kontainer_input, width=14, font=("Segoe UI", 8), relief="solid", bd=1)
            ent_n.pack(side="left", padx=(0, 6))
            ent_n.insert(0, "Pelanggan Baru")

            lbl_r = tk.Label(self.kontainer_input, text="Resto:", font=("Segoe UI", 8), bg="#ffffff")
            lbl_r.pack(side="left", padx=(0, 2))
            ent_r = tk.Entry(self.kontainer_input, width=12, font=("Segoe UI", 8), relief="solid", bd=1)
            ent_r.pack(side="left", padx=(0, 6))
            ent_r.insert(0, "kafe-teknik")

            lbl_m = tk.Label(self.kontainer_input, text="Menu:", font=("Segoe UI", 8), bg="#ffffff")
            lbl_m.pack(side="left", padx=(0, 2))
            ent_m = tk.Entry(self.kontainer_input, width=12, font=("Segoe UI", 8), relief="solid", bd=1)
            ent_m.pack(side="left", padx=(0, 6))
            ent_m.insert(0, "paket-siang")

            lbl_h = tk.Label(self.kontainer_input, text="Harga:", font=("Segoe UI", 8), bg="#ffffff")
            lbl_h.pack(side="left", padx=(0, 2))
            ent_h = tk.Entry(self.kontainer_input, width=8, font=("Segoe UI", 8), relief="solid", bd=1)
            ent_h.pack(side="left", padx=(0, 8))
            ent_h.insert(0, "15000")

            def _aksi_tambah():
                try:
                    hrg = int(ent_h.get().strip())
                except ValueError:
                    messagebox.showerror("Error", "Harga harus angka!")
                    return
                oid_baru = f"O-{len(self.data_mentah) + 1:06d}"
                p = Pesanan(oid_baru, ent_n.get().strip(), ent_r.get().strip(),
                            ent_m.get().strip(), hrg, prio, int(time.time()), 0, "ANTRE")
                t0 = time.perf_counter()
                if tipe == "Array":
                    if prio == 3: self.array_pesanan.tambah_reguler(p)
                    elif prio == 2: self.array_pesanan.tambah_prioritas(p)
                    else: self.array_pesanan.tambah_vip(p)
                    cmd = "array_tambah"
                else:
                    if prio == 3: self.linklist_pesanan.tambah_reguler(p)
                    elif prio == 2: self.linklist_pesanan.tambah_prioritas(p)
                    else: self.linklist_pesanan.tambah_vip(p)
                    cmd = "ll_tambah"
                dt = (time.perf_counter() - t0) * 1000

                self.data_mentah.append(p)
                self._catat_log(f"{cmd:<19} -> {p.oid} P{prio} ({p.pelanggan})     {dt:6.2f} ms")
                self._segarkan_tabel()
                messagebox.showinfo("Sukses", f"Pesanan {p.oid} berhasil ditambahkan!")

            btn_tb = tk.Button(self.kontainer_input, text="TAMBAH PESANAN",
                               command=_aksi_tambah,
                               font=("Segoe UI", 8, "bold"),
                               bg="#10b981", fg="#ffffff", relief="flat", padx=10, pady=2)
            btn_tb.pack(side="left")

        elif kode == "M1_LL_LIHAT" or kode == "M1_ARRAY_HAPUS" or kode == "M1_LL_HAPUS":
            tipe = "Array" if "ARRAY" in kode else "Linked List"
            aksi = "Hapus" if "HAPUS" in kode else "Lihat"

            self.lbl_judul_aksi.config(text=f"{tipe}: {aksi} Pesanan ke-i")
            self.lbl_sub_aksi.config(text=f"Operasi {aksi.lower()} elemen pada indeks tertentu.")
            self.lbl_helper_input.config(text="Masukkan indeks yang dituju.")

            lbl_idx = tk.Label(self.kontainer_input, text="Indeks ke-i:",
                               font=("Segoe UI", 8, "bold"), bg="#ffffff")
            lbl_idx.pack(side="left", padx=(0, 6))

            ent_idx = tk.Entry(self.kontainer_input, width=8, font=("Segoe UI", 8), relief="solid", bd=1)
            ent_idx.pack(side="left", padx=(0, 8))
            ent_idx.insert(0, "0")

            def _aksi_lh():
                try:
                    i = int(ent_idx.get().strip())
                except ValueError:
                    messagebox.showerror("Error", "Indeks harus bilangan bulat")
                    return
                t0 = time.perf_counter()
                try:
                    if tipe == "Array":
                        if aksi == "Lihat":
                            res = self.array_pesanan.lihat_pesanan(i)
                            cmd = "array_lihat"
                        else:
                            res = self.array_pesanan.hapus_pesanan(i)
                            cmd = "array_hapus"
                    else:
                        if aksi == "Lihat":
                            res = self.linklist_pesanan.lihat_pesanan(i)
                            cmd = "ll_lihat"
                        else:
                            res = self.linklist_pesanan.hapus_pesanan(i)
                            cmd = "ll_hapus"
                    dt = (time.perf_counter() - t0) * 1000
                    self._catat_log(f"{cmd:<19} -> idx {i}: {res.oid} ({res.pelanggan})   {dt:6.2f} ms")
                    if aksi == "Hapus":
                        self._segarkan_tabel()
                        messagebox.showinfo("Sukses", f"Pesanan {res.oid} berhasil dihapus!")
                    else:
                        self._lompat_ke_indeks(i)
                except IndexError:
                    messagebox.showerror("Error", f"Indeks {i} di luar jangkauan!")

            btn_bg = "#ef4444" if aksi == "Hapus" else "#0d47a1"
            btn_act = tk.Button(self.kontainer_input, text=aksi.upper(),
                                command=_aksi_lh,
                                font=("Segoe UI", 8, "bold"),
                                bg=btn_bg, fg="#ffffff", relief="flat", padx=12, pady=2)
            btn_act.pack(side="left")

        elif kode == "M1_BENCHMARK":
            self.lbl_judul_aksi.config(text="Adu Performa M1: Array Dinamis vs Singly Linked List")
            self.lbl_sub_aksi.config(text="Perbandingan empiris akses acak, penyisipan depan/tengah/belakang, dan penghapusan.")
            self.lbl_helper_input.config(text="Tekan tombol di bawah untuk menjalankan pengujian benchmark.")

            btn_bench = tk.Button(self.kontainer_input, text="JALANKAN BENCHMARK M1",
                                  command=self._jalankan_benchmark_m1,
                                  font=("Segoe UI", 8, "bold"),
                                  bg="#6366f1", fg="#ffffff", relief="flat", padx=12, pady=2)
            btn_bench.pack(side="left")

        elif kode == "M2_STACK_POSTFIX":
            self.lbl_judul_aksi.config(text="Stack: Mesin Kasir (Konversi Infix ke Postfix & Hitung Total)")
            self.lbl_sub_aksi.config(text="Algoritma Shunting-Yard dengan Stack operator dan evaluasi operand.")
            self.lbl_helper_input.config(text="Masukkan ekspresi matematika struk belanja, contoh: ( 3 * 12000 ) + ( 2 * 8500 ) - 5000")

            lbl_e = tk.Label(self.kontainer_input, text="Ekspresi:", font=("Segoe UI", 8, "bold"), bg="#ffffff")
            lbl_e.pack(side="left", padx=(0, 6))

            ent_e = tk.Entry(self.kontainer_input, width=40, font=("Consolas", 9), relief="solid", bd=1)
            ent_e.pack(side="left", padx=(0, 8))
            ent_e.insert(0, "( 3 * 12000 ) + ( 2 * 8500 ) - 5000")

            def _aksi_hitung():
                expr = ent_e.get().strip()
                t0 = time.perf_counter()
                tokens, l_pf = ke_postfix(expr)
                total, l_ev = hitung_postfix(tokens)
                dt = (time.perf_counter() - t0) * 1000

                pf_str = " ".join(tokens)
                self._catat_log(f"stack_postfix       -> {pf_str[:25]}... = Rp {total:,}   {dt:6.2f} ms")

                # Tampilkan ke tab 3
                self.txt_postfix.delete("1.0", "end")
                self.txt_postfix.insert("end", f"=== HASIL KALKULATOR STRUK KASIR (STACK) ===\n\n")
                self.txt_postfix.insert("end", f"Infix   : {expr}\n")
                self.txt_postfix.insert("end", f"Postfix : {pf_str}\n")
                self.txt_postfix.insert("end", f"TOTAL   : Rp {total:,}\n\n".replace(",", "."))
                self.txt_postfix.insert("end", "Tahap 1: Konversi Infix ke Postfix (Shunting-Yard)\n")
                self.txt_postfix.insert("end", "-" * 70 + "\n")
                self.txt_postfix.insert("end", f"{'Token':<8} {'Tindakan':<30} {'Isi Stack':<15} {'Keluaran'}\n")
                self.txt_postfix.insert("end", "-" * 70 + "\n")
                for tk_i, act_i, stk_i, out_i in l_pf:
                    self.txt_postfix.insert("end", f"{tk_i:<8} {act_i:<30} {stk_i:<15} {out_i}\n")

                self.txt_postfix.insert("end", "\nTahap 2: Evaluasi Ekspresi Postfix\n")
                self.txt_postfix.insert("end", "-" * 70 + "\n")
                for tk_i, act_i, stk_i, _ in l_ev:
                    self.txt_postfix.insert("end", f"{tk_i:<8} {act_i:<30} stack: [{stk_i}]\n")

                self.notebook.select(self.tab_postfix)

            btn_hitung = tk.Button(self.kontainer_input, text="HITUNG STRUK",
                                   command=_aksi_hitung,
                                   font=("Segoe UI", 8, "bold"),
                                   bg="#8b5cf6", fg="#ffffff", relief="flat", padx=12, pady=2)
            btn_hitung.pack(side="left")

        elif kode == "M2_QUEUE_ENQUEUE":
            self.lbl_judul_aksi.config(text="Queue: Enqueue Pesanan (Masuk ke Kedua Antrean)")
            self.lbl_sub_aksi.config(text="Memasukkan pesanan baru ke belakang antrean Naif dan Circular.")
            self.lbl_helper_input.config(text="Masukkan nama pelanggan baru.")

            lbl_n = tk.Label(self.kontainer_input, text="Pelanggan:", font=("Segoe UI", 8), bg="#ffffff")
            lbl_n.pack(side="left", padx=(0, 6))

            ent_n = tk.Entry(self.kontainer_input, width=20, font=("Segoe UI", 8), relief="solid", bd=1)
            ent_n.pack(side="left", padx=(0, 8))
            ent_n.insert(0, "Pelanggan Antre")

            def _aksi_enq():
                nama = ent_n.get().strip()
                oid = f"O-{len(self.data_mentah) + 1:06d}"
                p = Pesanan(oid, nama, "resto-antre", "menu-antre", 12000, 3, int(time.time()), 0, "ANTRE")
                t0 = time.perf_counter()
                self.queue_naif.enqueue(p)
                self.queue_circ.enqueue(p)
                self.undo_redo.catat("enqueue", p)
                dt = (time.perf_counter() - t0) * 1000

                self.data_mentah.append(p)
                self._catat_log(f"queue_enqueue       -> {p.oid} masuk kedua antrean      {dt:6.2f} ms")
                self._segarkan_tabel()
                messagebox.showinfo("Sukses", f"{p.oid} masuk antrean!")

            btn_enq = tk.Button(self.kontainer_input, text="ENQUEUE",
                                command=_aksi_enq,
                                font=("Segoe UI", 8, "bold"),
                                bg="#2563eb", fg="#ffffff", relief="flat", padx=12, pady=2)
            btn_enq.pack(side="left")

        elif kode == "M2_QUEUE_DEQUEUE_NAIF" or kode == "M2_QUEUE_DEQUEUE_CIRC":
            versi = "Naif" if "NAIF" in kode else "Circular"
            self.lbl_judul_aksi.config(text=f"Queue: Dequeue {versi} (Layani Pesanan Paling Depan)")
            ket = "Menggeser seluruh sisa elemen ke kiri O(n)." if versi == "Naif" else "Pointer front maju modulo O(1) tanpa geser."
            self.lbl_sub_aksi.config(text=ket)
            self.lbl_helper_input.config(text="Tentukan jumlah pesanan yang ingin dilayani sekaligus.")

            lbl_c = tk.Label(self.kontainer_input, text="Jumlah pesanan:", font=("Segoe UI", 8), bg="#ffffff")
            lbl_c.pack(side="left", padx=(0, 6))

            ent_c = tk.Entry(self.kontainer_input, width=8, font=("Segoe UI", 8), relief="solid", bd=1)
            ent_c.pack(side="left", padx=(0, 8))
            ent_c.insert(0, "1")

            def _aksi_deq():
                try:
                    cnt = int(ent_c.get().strip())
                except ValueError:
                    messagebox.showerror("Error", "Jumlah harus angka!")
                    return
                t0 = time.perf_counter()
                dilayani = []
                total_geser = 0
                if versi == "Naif":
                    for _ in range(cnt):
                        if self.queue_naif.is_empty(): break
                        p, gsr = self.queue_naif.dequeue()
                        p.status = "DONE"
                        dilayani.append(p)
                        total_geser += gsr
                    dt = (time.perf_counter() - t0) * 1000
                    cmd = "dequeue_naif"
                    rincian = f"{len(dilayani)} keluar | {total_geser:,} geser".replace(",", ".")
                else:
                    for _ in range(cnt):
                        if self.queue_circ.is_empty(): break
                        p = self.queue_circ.dequeue()
                        p.status = "DONE"
                        dilayani.append(p)
                    dt = (time.perf_counter() - t0) * 1000
                    cmd = "dequeue_circ"
                    rincian = f"{len(dilayani)} keluar | 0 geser"

                if dilayani:
                    self.undo_redo.catat(f"dequeue_{versi.lower()}", dilayani)
                    self._catat_log(f"{cmd:<19} -> {rincian:<30} {dt:6.2f} ms")
                    self._ganti_sumber_data("M2")
                else:
                    messagebox.showinfo("Kosong", "Antrean kosong!")

            btn_bg = "#d97706" if versi == "Naif" else "#059669"
            btn_deq = tk.Button(self.kontainer_input, text=f"DEQUEUE {versi.upper()}",
                                command=_aksi_deq,
                                font=("Segoe UI", 8, "bold"),
                                bg=btn_bg, fg="#ffffff", relief="flat", padx=12, pady=2)
            btn_deq.pack(side="left")

        elif kode == "M2_STACK_UNDO" or kode == "M2_STACK_REDO":
            mode = "Undo" if "UNDO" in kode else "Redo"
            self.lbl_judul_aksi.config(text=f"Stack: {mode} Aksi Terakhir")
            self.lbl_sub_aksi.config(text=f"Membatalkan atau mengulang aksi terakhir pada antrean.")
            self.lbl_helper_input.config(text=f"Kedalaman Undo: {self.undo_redo.undo_depth} | Kedalaman Redo: {self.undo_redo.redo_depth}")

            def _aksi_ur():
                t0 = time.perf_counter()
                entry = self.undo_redo.undo_last() if mode == "Undo" else self.undo_redo.redo_last()
                dt = (time.perf_counter() - t0) * 1000
                if not entry:
                    messagebox.showinfo("Info", f"Tumpukan {mode} kosong!")
                    return
                aksi_nama, data = entry
                if mode == "Undo":
                    if aksi_nama.startswith("dequeue"):
                        for p in reversed(data):
                            p.status = "ANTRE"
                            self.queue_circ.enqueue_front(p)
                        info = f"{len(data)} pesanan dikembalikan ke antrean"
                    else:
                        self.queue_circ.count -= 1
                        self.queue_circ.rear = (self.queue_circ.rear - 1) % self.queue_circ.capacity
                        info = f"{data.oid} dicabut dari antrean"
                else:
                    if aksi_nama.startswith("dequeue"):
                        for _ in range(len(data)):
                            p = self.queue_circ.dequeue()
                            p.status = "DONE"
                        info = f"{len(data)} pesanan dikeluarkan lagi"
                    else:
                        self.queue_circ.enqueue(data)
                        info = f"{data.oid} dimasukkan kembali"

                cmd = "stack_undo" if mode == "Undo" else "stack_redo"
                self._catat_log(f"{cmd:<19} -> {info:<30} {dt:6.2f} ms")
                self.lbl_helper_input.config(text=f"Kedalaman Undo: {self.undo_redo.undo_depth} | Kedalaman Redo: {self.undo_redo.redo_depth}")
                self._ganti_sumber_data("M2")

            btn_ur = tk.Button(self.kontainer_input, text=f"JALANKAN {mode.upper()}",
                               command=_aksi_ur,
                               font=("Segoe UI", 8, "bold"),
                               bg="#475569", fg="#ffffff", relief="flat", padx=12, pady=2)
            btn_ur.pack(side="left")

        elif kode == "M2_BENCHMARK":
            self.lbl_judul_aksi.config(text="Adu Performa M2: Dequeue Naif vs Circular Queue")
            self.lbl_sub_aksi.config(text="Mengukur pergeseran elemen dan selisih waktu eksekusi antrean.")
            self.lbl_helper_input.config(text="Tekan tombol di bawah untuk menjalankan pengujian.")

            btn_b2 = tk.Button(self.kontainer_input, text="JALANKAN BENCHMARK M2",
                               command=self._jalankan_benchmark_m2,
                               font=("Segoe UI", 8, "bold"),
                               bg="#d97706", fg="#ffffff", relief="flat", padx=12, pady=2)
            btn_b2.pack(side="left")

        elif kode == "M3_SORT_INSERTION" or kode == "M3_SORT_MERGE":
            algo = "Insertion" if "INSERTION" in kode else "Merge"
            self.lbl_judul_aksi.config(text=f"Sort: {algo} Sort (Stabil, Kunci Tertentu)")
            ket = "Batas 20.000 baris O(n^2), in-place." if algo == "Insertion" else "Skala penuh O(n log n), divide-and-conquer."
            self.lbl_sub_aksi.config(text=ket)
            self.lbl_helper_input.config(text="Pilih kunci pengurutan dan jumlah baris data.")

            lbl_k = tk.Label(self.kontainer_input, text="Kunci:", font=("Segoe UI", 8), bg="#ffffff")
            lbl_k.pack(side="left", padx=(0, 4))
            cmb_k = ttk.Combobox(self.kontainer_input, values=["harga", "oid", "selesai"], width=8, state="readonly")
            cmb_k.set("harga")
            cmb_k.pack(side="left", padx=(0, 8))

            lbl_n = tk.Label(self.kontainer_input, text="Jumlah Baris:", font=("Segoe UI", 8), bg="#ffffff")
            lbl_n.pack(side="left", padx=(0, 4))
            ent_n = tk.Entry(self.kontainer_input, width=8, font=("Segoe UI", 8), relief="solid", bd=1)
            ent_n.pack(side="left", padx=(0, 8))
            ent_n.insert(0, "2000" if algo == "Insertion" else "4000")

            def _aksi_sort():
                try:
                    n = int(ent_n.get().strip())
                except ValueError:
                    messagebox.showerror("Error", "Jumlah baris harus angka!")
                    return
                kunci_teks = cmb_k.get()
                if kunci_teks == "harga": fn_k = by_harga
                elif kunci_teks == "oid": fn_k = by_oid
                else: fn_k = by_selesai

                sample = [self.data_mentah[i] for i in range(min(n, len(self.data_mentah)))]
                t0 = time.perf_counter()
                if algo == "Insertion":
                    res, comp, move, err = insertion_sort(sample, fn_k)
                    dt = (time.perf_counter() - t0) * 1000
                    if err:
                        self._catat_log(f"insertion_sort      -> jumlah={n} DITOLAK: > 20.000 baris")
                        messagebox.showwarning("Ditolak", err)
                        return
                    cmd = "insertion_sort"
                else:
                    res, comp, move, err = merge_sort(sample, fn_k)
                    dt = (time.perf_counter() - t0) * 1000
                    cmd = "merge_sort"

                rincian = f"{len(res):,} urut | {comp:,} comp".replace(",", ".")
                self._catat_log(f"{cmd:<19} -> {rincian:<30} {dt:6.2f} ms")
                self.data_terurut = res
                self._ganti_sumber_data("M3")
                self.notebook.select(self.tab_tabel)

            btn_sort = tk.Button(self.kontainer_input, text=f"URUTKAN ({algo.upper()})",
                                 command=_aksi_sort,
                                 font=("Segoe UI", 8, "bold"),
                                 bg="#7c3aed", fg="#ffffff", relief="flat", padx=12, pady=2)
            btn_sort.pack(side="left")

        elif kode == "M3_SEARCH_LINEAR" or kode == "M3_SEARCH_BINARY":
            algo = "Linear" if "LINEAR" in kode else "Binary"
            self.lbl_judul_aksi.config(text=f"Search: {algo} Search (Pencarian OID Pesanan)")
            ket = "Menelusuri satu per satu dari depan O(n)." if algo == "Linear" else "Pencarian biner O(log n) pada daftar terurut OID."
            self.lbl_sub_aksi.config(text=ket)
            self.lbl_helper_input.config(text="Masukkan target Order ID (OID), contoh: O-137442")

            lbl_t = tk.Label(self.kontainer_input, text="Target OID:", font=("Segoe UI", 8), bg="#ffffff")
            lbl_t.pack(side="left", padx=(0, 4))
            ent_t = tk.Entry(self.kontainer_input, width=12, font=("Segoe UI", 8), relief="solid", bd=1)
            ent_t.pack(side="left", padx=(0, 8))
            ent_t.insert(0, "O-137442")

            def _aksi_search():
                target = ent_t.get().strip()
                if algo == "Linear":
                    t0 = time.perf_counter()
                    idx, comp = linear_search(self.data_mentah, target, by_oid)
                    dt = (time.perf_counter() - t0) * 1000
                    if idx != -1:
                        info = f"ditemukan di idx {idx:,} | {comp:,} comp".replace(",", ".")
                        self._lompat_ke_indeks(idx)
                    else:
                        info = f"tidak ditemukan | {comp:,} comp".replace(",", ".")
                    self._catat_log(f"linear_search       -> {target} {info}   {dt:6.2f} ms")
                else:
                    if self.oid_sorted_cache is None:
                        t_b = time.perf_counter()
                        s_list, _, _, _ = merge_sort(list(self.data_mentah), by_oid)
                        self.oid_sorted_time_ms = (time.perf_counter() - t_b) * 1000
                        self.oid_sorted_cache = s_list
                        self._catat_log(f"build_sorted_oid    -> daftar terurut oid dibangun  {self.oid_sorted_time_ms:6.2f} ms")

                    t0 = time.perf_counter()
                    idx, comp = binary_search(self.oid_sorted_cache, target, by_oid)
                    dt = (time.perf_counter() - t0) * 1000
                    if idx != -1:
                        info = f"ditemukan di baris {idx+1:,} | {comp} comp".replace(",", ".")
                        self.data_terurut = self.oid_sorted_cache
                        self._ganti_sumber_data("M3")
                        self._lompat_ke_indeks(idx)
                    else:
                        info = f"tidak ditemukan | {comp} comp"
                    self._catat_log(f"binary_search       -> {target} {info}   {dt:6.2f} ms")

            btn_s = tk.Button(self.kontainer_input, text=f"CARI ({algo.upper()})",
                              command=_aksi_search,
                              font=("Segoe UI", 8, "bold"),
                              bg="#0284c7", fg="#ffffff", relief="flat", padx=12, pady=2)
            btn_s.pack(side="left")

        elif kode == "M3_LAPORAN_HARIAN" or kode == "M3_CARI_LAPORAN":
            self.lbl_judul_aksi.config(text="M3: Laporan Harian Terurut Waktu Selesai")
            self.lbl_sub_aksi.config(text="Mengurutkan seluruh data menurut t_selesai menggunakan Merge Sort.")
            self.lbl_helper_input.config(text="Tekan tombol untuk menyusun laporan harian.")

            def _aksi_lap():
                t0 = time.perf_counter()
                res, comp, move, _ = merge_sort(list(self.data_mentah), by_selesai)
                dt = (time.perf_counter() - t0) * 1000
                self.data_terurut = res
                self._catat_log(f"laporan_harian      -> {len(res):,} pesanan terurut selesai {dt:6.2f} ms")
                self._ganti_sumber_data("M3")
                self.notebook.select(self.tab_tabel)

            btn_lp = tk.Button(self.kontainer_input, text="SUSUN LAPORAN HARIAN",
                               command=_aksi_lap,
                               font=("Segoe UI", 8, "bold"),
                               bg="#059669", fg="#ffffff", relief="flat", padx=12, pady=2)
            btn_lp.pack(side="left")

        elif kode == "M3_BENCHMARK":
            self.lbl_judul_aksi.config(text="Adu Performa M3: Sorting & Searching")
            self.lbl_sub_aksi.config(text="Tabel empiris n vs perbandingan Insertion Sort vs Merge Sort & Linear vs Binary Search.")
            self.lbl_helper_input.config(text="Tekan tombol di bawah untuk menjalankan pengujian.")

            btn_b3 = tk.Button(self.kontainer_input, text="JALANKAN BENCHMARK M3",
                               command=self._jalankan_benchmark_m3,
                               font=("Segoe UI", 8, "bold"),
                               bg="#7c3aed", fg="#ffffff", relief="flat", padx=12, pady=2)
            btn_b3.pack(side="left")

    # ================= 6. PAGINATION & TABEL =================

    def _dapatkan_dataset_aktif(self):
        if self.sumber_data_aktif == "M1":
            return self.data_mentah
        elif self.sumber_data_aktif == "M2":
            # ambil pesanan yang ada di circular queue
            hasil = []
            idx = self.queue_circ.front
            for _ in range(self.queue_circ.count):
                if self.queue_circ.data[idx] is not None:
                    hasil.append(self.queue_circ.data[idx])
                idx = (idx + 1) % self.queue_circ.capacity
            return hasil
        else:
            return self.data_terurut if self.data_terurut else self.data_mentah

    def _segarkan_tabel(self):
        dataset = self._dapatkan_dataset_aktif()
        total = len(dataset)

        if self.ukuran_halaman == -1:
            jml_hal = 1
            self.halaman_aktif = 1
            start = 0
            end = total
        else:
            jml_hal = max(1, (total + self.ukuran_halaman - 1) // self.ukuran_halaman)
            if self.halaman_aktif > jml_hal: self.halaman_aktif = jml_hal
            if self.halaman_aktif < 1: self.halaman_aktif = 1
            start = (self.halaman_aktif - 1) * self.ukuran_halaman
            end = min(start + self.ukuran_halaman, total)

        self.lbl_indikator_hal.config(text=f"Halaman {self.halaman_aktif} / {jml_hal}")
        self.lbl_ringkasan_baris.config(
            text=f"[{self.sumber_data_aktif}] {start + 1 if total > 0 else 0} - {end} dari {total:,} pesanan".replace(",", ".")
        )

        for itm in self.tree.get_children():
            self.tree.delete(itm)

        cuplikan = dataset[start:end]
        for idx_rel, p in enumerate(cuplikan):
            idx_global = start + idx_rel
            t_msk = str(p.t_masuk) if p.t_masuk > 0 else ""
            t_sls = str(p.t_selesai) if p.t_selesai > 0 else ""
            tag = ("sorot",) if idx_global == self.baris_disorot else ()
            self.tree.insert("", "end", iid=str(idx_global), values=(
                p.oid, p.pelanggan, p.resto, p.menu,
                f"{p.harga}", p.prioritas, t_msk, t_sls, p.status
            ), tags=tag)

        if self.baris_disorot >= start and self.baris_disorot < end:
            try:
                self.tree.see(str(self.baris_disorot))
                self.tree.selection_set(str(self.baris_disorot))
            except Exception:
                pass

    def _lompat_ke_indeks(self, i):
        self.baris_disorot = i
        if self.ukuran_halaman != -1:
            self.halaman_aktif = (i // self.ukuran_halaman) + 1
        self._segarkan_tabel()
        self.notebook.select(self.tab_tabel)

    def _hal_awal(self):
        self.halaman_aktif = 1
        self._segarkan_tabel()

    def _hal_prev(self):
        if self.halaman_aktif > 1:
            self.halaman_aktif -= 1
            self._segarkan_tabel()

    def _hal_next(self):
        dataset = self._dapatkan_dataset_aktif()
        if self.ukuran_halaman != -1:
            jml_hal = max(1, (len(dataset) + self.ukuran_halaman - 1) // self.ukuran_halaman)
            if self.halaman_aktif < jml_hal:
                self.halaman_aktif += 1
                self._segarkan_tabel()

    def _hal_akhir(self):
        dataset = self._dapatkan_dataset_aktif()
        if self.ukuran_halaman != -1:
            self.halaman_aktif = max(1, (len(dataset) + self.ukuran_halaman - 1) // self.ukuran_halaman)
            self._segarkan_tabel()

    def _set_limit(self, lim):
        self.ukuran_halaman = lim
        self.btn_limit_100.config(relief="solid" if lim == 100 else "groove")
        self.btn_limit_500.config(relief="solid" if lim == 500 else "groove")
        self.btn_limit_semua.config(relief="solid" if lim == -1 else "groove")
        self.halaman_aktif = 1
        self._segarkan_tabel()

    def _ganti_sumber_data(self, src):
        self.sumber_data_aktif = src
        self.btn_src_m1.config(relief="solid" if src == "M1" else "groove")
        self.btn_src_m2.config(relief="solid" if src == "M2" else "groove")
        self.btn_src_m3.config(relief="solid" if src == "M3" else "groove")
        self.halaman_aktif = 1
        self._segarkan_tabel()

    # ================= 7. MEMUAT DATASET =================

    def _muat_data_otomatis(self):
        jalur_def = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "pesanan.csv")
        if os.path.exists(jalur_def):
            self._proses_muat_csv(jalur_def)
        else:
            self.lbl_banner_teks.config(text="Berkas data/pesanan.csv tidak ditemukan. Gunakan tombol Load.")

    def _aksi_load_csv_dialog(self):
        path = filedialog.askopenfilename(
            title="Pilih berkas pesanan.csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if path:
            self._proses_muat_csv(path)

    def _proses_muat_csv(self, path):
        self.root.config(cursor="watch")
        self.root.update()

        # 1. Baca CSV
        raw = load_pesanan(path)
        self.data_mentah = raw
        self.oid_sorted_cache = None

        # 2. Masukkan ke Array M1
        t_arr0 = time.perf_counter()
        self.array_pesanan = Array(len(raw) + 10)
        for p in raw:
            self.array_pesanan.append(p)
        dt_arr = (time.perf_counter() - t_arr0) * 1000

        # 3. Masukkan ke Linked List M1 (cuplikan 5000 awal agar responsif)
        t_ll0 = time.perf_counter()
        self.linklist_pesanan = LinkList()
        batas_ll = min(len(raw), 5000)
        for i in range(batas_ll):
            self.linklist_pesanan.append(raw[i])
        dt_ll = (time.perf_counter() - t_ll0) * 1000

        # 4. Masukkan ke Antrean M2 (hanya status ANTRE)
        t_q0 = time.perf_counter()
        self.queue_naif = AntreanNaif()
        self.queue_circ = AntreanMelingkar()
        antre_count = 0
        for p in raw:
            if p.status == "ANTRE":
                self.queue_naif.enqueue(p)
                self.queue_circ.enqueue(p)
                antre_count += 1
        dt_q = (time.perf_counter() - t_q0) * 1000

        self.root.config(cursor="")

        # Catat ke log command persis seperti screenshot
        self._catat_log(f"load                -> M1 - larik           {dt_arr:6.2f} ms")
        self._catat_log(f"                    -> M1 - linked list     {dt_ll:6.2f} ms")
        self._catat_log(f"load_antre          -> M2 - queue           {dt_q:6.2f} ms")

        # Perbarui teks banner status
        pesan_banner = (
            f"Data berhasil dimuat: {len(raw)} pesanan (M1) & {antre_count} antrean ANTRE (M2). "
            f"M3 (Sort & Search) siap. Larik: {dt_arr:.2f} ms | Rantai: {dt_ll:.2f} ms | Antrean: {dt_q:.2f} ms"
        )
        self.lbl_banner_teks.config(text=pesan_banner)
        self.lbl_header_info.config(text=f"Data: {len(raw):,} baris".replace(",", "."))

        self.badge_runtime.config(text=f"[M1-M3 Siap] {dt_arr:.2f} ms")
        self.lbl_status_teks.config(
            text=f"Total: {len(raw):,} pesanan | Antrean: {antre_count:,} pesanan | M3 Siap".replace(",", ".")
        )

        self._ganti_menu("M1_ARRAY_LIHAT")
        self._segarkan_tabel()

    # ================= 8. EKSEKUSI PERINTAH INPUT COMMAND =================

    def _eksekusi_command_input(self):
        raw_cmd = self.ent_cmd_input.get().strip()
        if not raw_cmd:
            return
        self.ent_cmd_input.delete(0, "end")

        parts = raw_cmd.split()
        cmd_nama = parts[0].lower()

        if cmd_nama == "load":
            jalur = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "pesanan.csv")
            self._proses_muat_csv(jalur)
        elif cmd_nama == "array_lihat" and len(parts) > 1:
            try:
                idx = int(parts[1])
                t0 = time.perf_counter()
                p = self.array_pesanan.lihat_pesanan(idx)
                dt = (time.perf_counter() - t0) * 1000
                self._catat_log(f"array_lihat         -> idx {idx}: {p.oid} ({p.pelanggan})   {dt:6.2f} ms")
                self._lompat_ke_indeks(idx)
            except Exception as e:
                self._catat_log(f"error               -> {e}")
        elif cmd_nama == "postfix" and len(parts) > 1:
            expr = " ".join(parts[1:])
            t0 = time.perf_counter()
            tokens, l_pf = ke_postfix(expr)
            total, l_ev = hitung_postfix(tokens)
            dt = (time.perf_counter() - t0) * 1000
            self._catat_log(f"stack_postfix       -> {' '.join(tokens)[:25]}... = Rp {total:,}   {dt:6.2f} ms")
        elif cmd_nama == "dequeue_naif":
            cnt = int(parts[1]) if len(parts) > 1 else 1
            t0 = time.perf_counter()
            dl = []
            gsr = 0
            for _ in range(cnt):
                if self.queue_naif.is_empty(): break
                p, g = self.queue_naif.dequeue()
                dl.append(p)
                gsr += g
            dt = (time.perf_counter() - t0) * 1000
            self._catat_log(f"dequeue_naif        -> {len(dl)} keluar | {gsr:,} geser   {dt:6.2f} ms".replace(",", "."))
            self._ganti_sumber_data("M2")
        elif cmd_nama == "dequeue_circ" or cmd_nama == "dequeue_circular":
            cnt = int(parts[1]) if len(parts) > 1 else 1
            t0 = time.perf_counter()
            dl = []
            for _ in range(cnt):
                if self.queue_circ.is_empty(): break
                dl.append(self.queue_circ.dequeue())
            dt = (time.perf_counter() - t0) * 1000
            self._catat_log(f"dequeue_circ        -> {len(dl)} keluar | 0 geser   {dt:6.2f} ms")
            self._ganti_sumber_data("M2")
        elif cmd_nama == "undo":
            entry = self.undo_redo.undo_last()
            if entry:
                self._catat_log(f"stack_undo          -> batalkan {entry[0]}")
                self._ganti_sumber_data("M2")
            else:
                self._catat_log("stack_undo          -> tumpukan undo kosong")
        elif cmd_nama == "redo":
            entry = self.undo_redo.redo_last()
            if entry:
                self._catat_log(f"stack_redo          -> ulang {entry[0]}")
                self._ganti_sumber_data("M2")
            else:
                self._catat_log("stack_redo          -> tumpukan redo kosong")
        elif cmd_nama == "linear_search" and len(parts) > 1:
            t0 = time.perf_counter()
            idx, c = linear_search(self.data_mentah, parts[1], by_oid)
            dt = (time.perf_counter() - t0) * 1000
            self._catat_log(f"linear_search       -> {parts[1]} di idx {idx} | {c} comp   {dt:6.2f} ms")
            if idx != -1: self._lompat_ke_indeks(idx)
        elif cmd_nama == "binary_search" and len(parts) > 1:
            if not self.oid_sorted_cache:
                s, _, _, _ = merge_sort(list(self.data_mentah), by_oid)
                self.oid_sorted_cache = s
            t0 = time.perf_counter()
            idx, c = binary_search(self.oid_sorted_cache, parts[1], by_oid)
            dt = (time.perf_counter() - t0) * 1000
            self._catat_log(f"binary_search       -> {parts[1]} di baris {idx+1} | {c} comp   {dt:6.2f} ms")
            if idx != -1:
                self.data_terurut = self.oid_sorted_cache
                self._ganti_sumber_data("M3")
                self._lompat_ke_indeks(idx)
        else:
            self._catat_log(f"perintah            -> '{raw_cmd}' (ketik load, array_lihat, dequeue_naif, dll)")

    # ================= 9. BENCHMARK / ADU PERFORMA =================

    def _jalankan_benchmark_m1(self):
        self.txt_log.delete("1.0", "end")
        self.txt_log.insert("end", "========================================================\n")
        self.txt_log.insert("end", "      ADU PERFORMA M1: ARRAY DINAMIS VS LINKED LIST     \n")
        self.txt_log.insert("end", "========================================================\n\n")

        p_test = Pesanan("O-TEST", "Uji Coba", "kafe", "menu", 10000, 3, 0, 0, "ANTRE")
        n_sample = min(len(self.data_mentah), 4000)

        # 1. Akses Acak get(i)
        t0 = time.perf_counter()
        _ = self.array_pesanan.get(n_sample // 2)
        dt_arr_get = (time.perf_counter() - t0) * 1000000

        t0 = time.perf_counter()
        _ = self.linklist_pesanan.get(n_sample // 2)
        dt_ll_get = (time.perf_counter() - t0) * 1000000

        # 2. Sisip Depan VIP
        t0 = time.perf_counter()
        self.array_pesanan.tambah_vip(p_test)
        dt_arr_vip = (time.perf_counter() - t0) * 1000000
        self.array_pesanan.hapus_pesanan(0)

        t0 = time.perf_counter()
        self.linklist_pesanan.tambah_vip(p_test)
        dt_ll_vip = (time.perf_counter() - t0) * 1000000
        self.linklist_pesanan.hapus_pesanan(0)

        # 3. Sisip Belakang Reguler
        t0 = time.perf_counter()
        self.array_pesanan.tambah_reguler(p_test)
        dt_arr_reg = (time.perf_counter() - t0) * 1000000
        self.array_pesanan.pop_back()

        t0 = time.perf_counter()
        self.linklist_pesanan.tambah_reguler(p_test)
        dt_ll_reg = (time.perf_counter() - t0) * 1000000
        self.linklist_pesanan.hapus_pesanan(len(self.linklist_pesanan) - 1)

        self.txt_log.insert("end", f"{'Operasi':<28} {'Array (us)':<16} {'Linked List (us)':<18} {'Pemenang'}\n")
        self.txt_log.insert("end", "-" * 75 + "\n")
        self.txt_log.insert("end", f"{'Lihat ke-(n/2) O(1) vs O(n)':<28} {dt_arr_get:12.2f}    {dt_ll_get:14.2f}     Array\n")
        self.txt_log.insert("end", f"{'Tambah VIP Depan O(n) vs O(1)':<28} {dt_arr_vip:12.2f}    {dt_ll_vip:14.2f}     Linked List\n")
        self.txt_log.insert("end", f"{'Tambah Reguler Belakang O(1)':<28} {dt_arr_reg:12.2f}    {dt_ll_reg:14.2f}     Keduanya O(1)\n")
        self.txt_log.insert("end", "-" * 75 + "\n")
        self.notebook.select(self.tab_log)

    def _jalankan_benchmark_m2(self):
        self.txt_log.delete("1.0", "end")
        self.txt_log.insert("end", "========================================================\n")
        self.txt_log.insert("end", "   ADU PERFORMA M2: DEQUEUE NAIF VS CIRCULAR QUEUE      \n")
        self.txt_log.insert("end", "========================================================\n\n")

        q_naif = AntreanNaif()
        q_circ = AntreanMelingkar()
        for i in range(10000):
            p = Pesanan(f"O-{i}", "User", "R", "M", 10000, 3, 0, 0, "ANTRE")
            q_naif.enqueue(p)
            q_circ.enqueue(p)

        # Dequeue 50 kali
        t0 = time.perf_counter()
        gsr_total = 0
        for _ in range(50):
            _, g = q_naif.dequeue()
            gsr_total += g
        dt_naif = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        for _ in range(50):
            _ = q_circ.dequeue()
        dt_circ = (time.perf_counter() - t0) * 1000

        self.txt_log.insert("end", f"Data antrean awal : 10.000 pesanan\n")
        self.txt_log.insert("end", f"Jumlah dilayani   : 50 kali dequeue\n\n")
        self.txt_log.insert("end", f"Antrean Naif      : {dt_naif:8.2f} ms | Total elemen digeser: {gsr_total:,}\n".replace(",", "."))
        self.txt_log.insert("end", f"Antrean Melingkar : {dt_circ:8.2f} ms | Total elemen digeser: 0\n\n")
        self.txt_log.insert("end", f"Kesimpulan: Antrean Melingkar {dt_naif / max(dt_circ, 0.0001):.1f}x lebih cepat karena tidak ada pergeseran elemen O(n).\n")
        self.notebook.select(self.tab_log)

    def _jalankan_benchmark_m3(self):
        self.txt_log.delete("1.0", "end")
        self.txt_log.insert("end", "========================================================\n")
        self.txt_log.insert("end", "     ADU PERFORMA M3: SORTING & SEARCHING (EMPIRIS)     \n")
        self.txt_log.insert("end", "========================================================\n\n")

        self.txt_log.insert("end", "1. Uji Sorting (Kunci: Harga)\n")
        self.txt_log.insert("end", f"{'Algoritma':<16} {'n':<8} {'Perbandingan':<16} {'Pemindahan':<14} {'Waktu (ms)'}\n")
        self.txt_log.insert("end", "-" * 68 + "\n")

        for n in [10, 2000, 4000]:
            sample = [self.data_mentah[i] for i in range(min(n, len(self.data_mentah)))]
            t0 = time.perf_counter()
            _, c_i, m_i, _ = insertion_sort(list(sample), by_harga)
            dt_i = (time.perf_counter() - t0) * 1000
            self.txt_log.insert("end", f"{'Insertion Sort':<16} {n:<8} {c_i:<16,} {m_i:<14,} {dt_i:8.2f}\n".replace(",", "."))

            t0 = time.perf_counter()
            _, c_m, m_m, _ = merge_sort(list(sample), by_harga)
            dt_m = (time.perf_counter() - t0) * 1000
            self.txt_log.insert("end", f"{'Merge Sort':<16} {n:<8} {c_m:<16,} {m_m:<14,} {dt_m:8.2f}\n".replace(",", "."))

        self.txt_log.insert("end", "\n2. Uji Searching (Target: O-137442)\n")
        self.txt_log.insert("end", "-" * 68 + "\n")
        t0 = time.perf_counter()
        idx_l, c_l = linear_search(self.data_mentah, "O-137442", by_oid)
        dt_l = (time.perf_counter() - t0) * 1000
        self.txt_log.insert("end", f"Linear Search : ditemukan idx {idx_l:,} | {c_l:,} perbandingan | {dt_l:.2f} ms\n".replace(",", "."))

        if not self.oid_sorted_cache:
            s, _, _, _ = merge_sort(list(self.data_mentah), by_oid)
            self.oid_sorted_cache = s
        t0 = time.perf_counter()
        idx_b, c_b = binary_search(self.oid_sorted_cache, "O-137442", by_oid)
        dt_b = (time.perf_counter() - t0) * 1000
        self.txt_log.insert("end", f"Binary Search : ditemukan baris {idx_b+1:,} | {c_b} perbandingan | {dt_b:.2f} ms\n".replace(",", "."))
        self.notebook.select(self.tab_log)
