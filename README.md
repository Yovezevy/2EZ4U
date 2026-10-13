# Proyek 2EZ4U APP

Studi Kasus Proyek Akhir  
Mata Kuliah: Struktur Data & Analisa Algoritma (EC234303)  
Departemen Teknik Komputer, FTEIC - Institut Teknologi Sepuluh Nopember  

---

## 1. Deskripsi Proyek
2EZ4U APP adalah mini backend engine dan antarmuka desktop untuk sistem layanan antar makanan/barang (mirip GoFood/GrabFood/ShopeeFood). Proyek ini dirancang untuk menangani beban dataset berskala 200.000 data pesanan (`pesanan.csv`) dengan menerapkan struktur data primitif dan algoritma buatan sendiri dari nol tanpa menggunakan instant function bawaan Python (seperti `dict`, `set`, `sorted`, `.sort()`, `collections.*`, `heapq`, `bisect`, atau literal `{}`).

---

## 2. Struktur Repositori

```text
2EZ4U/
|-- README.md            <- Laporan dokumentasi & analisa
|-- app.py               <- Berkas utama untuk menjalankan aplikasi ("python app.py")
|-- data/
|   |-- pesanan.csv      <- Dataset 200.000 data pesanan
|   `-- peta.csv         <- Data graf peta lokasi rute
|-- backend/
|   |-- __init__.py
|   |-- m1_pesanan.py    <- M1: Array Dinamis & Singly Linked List
|   |-- m2_antrean.py    <- M2: Stack (Kasir, Undo/Redo) & Queue (Naif vs Melingkar)
|   |-- m3_laporan.py    <- M3: Insertion Sort, Merge Sort, Linear Search, Binary Search
|   `-- m3_sorting.py    <- Alias modul sorting
`-- frontend/
    |-- __init__.py
    `-- ui.py            <- Antarmuka Tkinter (3 bagian: Menu, Form/Hasil, COMMAND)
```

---

## 3. Cara Menjalankan Aplikasi

Pastikan Python 3.11+ sudah terpasang.

1. Clone repositori:
   ```bash
   git clone https://github.com/Yovezevy/2EZ4U.git
   cd 2EZ4U
   ```

2. Jalankan aplikasi:
   ```bash
   python app.py
   ```
   *(atau pada Windows gunakan `py app.py`)*

3. Di antarmuka aplikasi:
   - Klik tombol **Load pesanan.csv** di panel kiri atas untuk memuat dataset.
   - Pilih menu di sebelah kiri untuk menguji fitur M1, M2, dan M3.
   - Panel **COMMAND** di bagian bawah mencatat nama perintah, rincian hasil, modul, dan waktu eksekusi (milidetik).

---

## 4. Pembahasan Milestone

### 4.1 Milestone 1 (M1): Array Dinamis vs Singly Linked List
Data pesanan yang sama disimpan pada dua struktur data untuk menguji efisiensi operasi:
- **Lihat pesanan ke-i**: Array unggul dengan akses indeks langsung $O(1)$, sedangkan Linked List memerlukan penelusuran simpul dari head $O(n)$.
- **Tambah REGULER**: Masuk di baris paling belakang. Keduanya $O(1)$ (Array $O(1)$ amortized dengan doubling capacity saat penuh; Linked List $O(1)$ karena menyimpan pointer tail).
- **Tambah PRIORITAS**: Menyerobot ke tengah barisan ($n/2$). Array memerlukan penggeseran $n/2$ elemen ke kanan ($O(n)$), sedangkan Linked List memerlukan penelusuran $n/2$ simpul sebelum penyisipan ($O(n)$).
- **Tambah VIP**: Langsung masuk urutan pertama (indeks 0). Linked List hanya mengubah pointer head ($O(1)$), sedangkan Array harus menggeser seluruh isi elemen ($O(n)$).
- **Hapus pesanan ke-i**: Keduanya $O(n)$ karena Array harus menggeser elemen ke kiri, sementara Linked List harus menelusuri simpul hingga ke posisi sebelum target.

---

### 4.2 Milestone 2 (M2): Stack & Queue

#### A. Stack (Mesin Kasir & Undo/Redo)
1. **Mesin Kasir (Infix ke Postfix & Evaluasi)**:
   - Struk kasir diinput dalam format infix: `( 3 * 12000 ) + ( 2 * 8500 ) - 5000`.
   - Menggunakan algoritma *Shunting-Yard* berbasis Stack untuk mengonversi token infix ke bentuk postfix: `3 12000 * 2 8500 * + 5000 -`.
   - Tahap kedua mengevaluasi token postfix dengan stack operand angka. Urutan pop sangat krusial: pada operator `-` dan `/`, operand yang keluar pertama adalah operand kanan ($a - b$ di mana $b = \text{pop()}$ dan $a = \text{pop()}$). Hasil akhir: **Rp 48.000**.
2. **Undo & Redo**:
   - Setiap aksi `enqueue` atau `dequeue` didorong ke `undo_stack` bersama data pesanan terkait.
   - `undo_last()` membatalkan aksi terakhir (mengembalikan pesanan ke depan antrean jika dequeue, atau mencabut dari belakang jika enqueue) lalu mendorongnya ke `redo_stack`.
   - **Alasan tumpukan redo harus dikosongkan saat ada aksi baru**: Jika pengguna melakukan aksi baru setelah beberapa kali undo, riwayat cabang telah berubah. Menyimpan redo lama akan menyambungkan potongan state lama yang tidak lagi valid ke state baru.

#### B. Queue (Antrean Naif vs Antrean Melingkar)
- **Antrean Naif**: Dibuat di atas array biasa. Saat `dequeue()`, elemen indeks 0 diambil dan seluruh sisa elemen digeser 1 posisi ke kiri ($O(n)$ per layanan). Untuk 19.850 data antrean, 1 kali dequeue memicu 19.850 pergeseran elemen (~1 - 4 ms).
- **Antrean Melingkar (Circular Queue)**: Menggunakan array fixed-size dengan pointer `front` dan `rear` yang berputar menggunakan operasi modulo `(idx + 1) % capacity`. Saat `dequeue()`, hanya pointer `front` yang maju satu langkah ($O(1)$ tanpa pergeseran elemen sama sekali, ~0.01 ms).
- **Alasan menggunakan pencacah `count`**: Jika hanya mengandalkan `front == rear`, kondisi antrean kosong dan kondisi antrean penuh akan bernilai sama sehingga mustahil dibedakan. Dengan menyimpan variabel `count`, kondisi kosong (`count == 0`) dan kondisi penuh (`count == capacity`) dapat dibedakan dengan pasti tanpa perlu mengorbankan 1 slot array kosong.

---

### 4.3 Milestone 3 (M3): Sorting & Searching

#### A. Insertion Sort vs Merge Sort
- **Stabilitas Pengurutan**: Suatu algoritma dikatakan stabil jika data dengan nilai kunci yang sama tidak bertukar posisi relatif.
  - Pada **Insertion Sort**, syarat pergeseran menggunakan operator lebih besar (`>`), bukan `>=`.
  - Pada **Merge Sort**, saat menggabungkan dua subarray kiri dan kanan, syarat pengambilan elemen kiri menggunakan operator `<=`, sehingga elemen yang berada di sisi kiri selalu didahulukan.
- **Batas Maksimal Insertion Sort**: Karena kompleksitasnya $O(n^2)$, pengurutan insertion sort dibatasi maksimal 20.000 baris dengan pesan penolakan aman agar antarmuka tidak mengalami freeze. Untuk dataset besar (hingga 200.000 data), wajib menggunakan Merge Sort ($O(n \log n)$).

#### Tabel Hasil Pengujian Empiris (Kunci: Harga / OID)

| Algoritma | Jumlah Data ($n$) | Kunci | Jumlah Perbandingan | Pemindahan Elemen | Waktu Rata-rata |
|---|---|---|---|---|---|
| **Insertion Sort** | 10 | Harga | 24 | 25 | ~0.02 ms |
| **Insertion Sort** | 2.000 | Harga | 962.430 | 964.428 | ~163 ms |
| **Insertion Sort** | 4.000 | Harga | 3.831.520 | 3.835.518 | ~660 ms |
| **Insertion Sort** | 200.000 | Harga | *DITOLAK (> 20.000)* | - | - |
| **Merge Sort** | 2.000 | Harga | 19.240 | 38.624 | ~6 ms |
| **Merge Sort** | 4.000 | OID | 23.728 | 47.904 | ~10 ms |
| **Merge Sort** | 200.000 | Harga | ~3.226.139 | ~6.852.288 | ~1.12 s |

> **Analisis Grafik & Perbandingan**:
> Saat ukuran data dilipatduakan dari 2.000 menjadi 4.000, jumlah perbandingan Insertion Sort meningkat sekitar **4 kali lipat** ($2^2$), membuktikan sifat $O(n^2)$. Sebaliknya, Merge Sort hanya meningkat sekitar **2 kali lipat**, membuktikan pertumbuhan $O(n \log n)$.

#### B. Linear Search vs Binary Search
- **Linear Search**: Menelusuri data satu per satu dari indeks 0 hingga target ditemukan. Kompleksitas $O(n)$. Tidak memerlukan data terurut.
  - Mencari `O-137442` pada 200.000 data membutuhkan **137.442 perbandingan** (~26 ms).
- **Binary Search**: Membagi ruang pencarian menjadi dua bagian setiap iterasi ($O(\log n)$). Menuntut data sudah terurut menurut kunci yang dicari.
  - Memerlukan persiapan awal satu kali membangun daftar terurut berdasarkan OID menggunakan Merge Sort (~300 - 500 ms).
  - Setelah data terurut, mencari `O-137442` atau `O-199999` hanya memerlukan **16 - 17 perbandingan** (~0.03 - 0.05 ms).
  - *Kesimpulan*: Binary search jauh lebih menguntungkan ketika pencarian dilakukan berulang kali pada dataset yang sama.

---

## 5. Ringkasan Kompleksitas Waktu & Ruang

| Modul | Fitur / Algoritma | Kompleksitas Waktu | Kompleksitas Ruang | Keterangan |
|---|---|---|---|---|
| **M1** | Array - Tambah Reguler | $O(1)$ amortized | $O(n)$ | Doubling array saat penuh |
| **M1** | Array - Tambah VIP | $O(n)$ | $O(n)$ | Geser seluruh elemen ke kanan |
| **M1** | Linked List - Tambah VIP | $O(1)$ | $O(n)$ | Modifikasi pointer head |
| **M1** | Linked List - Tambah Reguler | $O(1)$ | $O(n)$ | Modifikasi pointer tail |
| **M2** | Infix ke Postfix | $O(n)$ | $O(n)$ | Shunting-Yard dengan Stack |
| **M2** | Evaluasi Postfix | $O(n)$ | $O(n)$ | Stack angka |
| **M2** | Queue Naif Dequeue | $O(n)$ | $O(n)$ | Menggeser sisa elemen |
| **M2** | Circular Queue Dequeue | $O(1)$ | $O(n)$ | Pointer front maju dengan modulo |
| **M2** | Undo / Redo | $O(1)$ | $O(k)$ | Stack riwayat |
| **M3** | Insertion Sort | $O(n^2)$ | $O(1)$ | In-place, stabil, batas $n \le 20.000$ |
| **M3** | Merge Sort | $O(n \log n)$ | $O(n)$ | Stabil, sanggup $n = 200.000$ |
| **M3** | Linear Search | $O(n)$ | $O(1)$ | Tanpa syarat terurut |
| **M3** | Binary Search | $O(\log n)$ | $O(1)$ | Syarat data terurut menurut kunci |
