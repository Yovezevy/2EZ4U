# m3_laporan.py
# modul sorting dan pencarian buat laporan harian
# dilarang pake dict, set, sorted, .sort(), literal {}, dll

import sys

# naikin batas rekursi buat merge sort data besar (200.000 baris)
sys.setrecursionlimit(300000)


# === fungsi pengambil kunci (key extractor) ===

def by_oid(p):
    return p.oid

def by_harga(p):
    return p.harga

def by_selesai(p):
    return p.t_selesai


# === 1. Insertion Sort ===
# in-place, stabil (> bukan >=), batas maksimal 20.000 baris

def insertion_sort(larik, key_func=by_harga):
    n = len(larik)
    comp = 0
    move = 0

    if n > 20000:
        return None, comp, move, "DITOLAK: batasnya 20.000 baris, pakai merge sort untuk data penuh"

    for i in range(1, n):
        simpan = larik[i]
        j = i - 1
        geser = False
        while j >= 0:
            comp += 1
            # pakai > agar stabil (urutan elemen yang sama tetap terjaga)
            if key_func(larik[j]) > key_func(simpan):
                larik[j + 1] = larik[j]
                move += 1
                j -= 1
                geser = True
            else:
                break
        larik[j + 1] = simpan
        move += 1  # penempatan elemen simpan

    return larik, comp, move, None


# === 2. Merge Sort ===
# divide-and-conquer, stabil (<= agar elemen kiri didahulukan)

def merge_sort(larik, key_func=by_harga):
    comp = 0
    move = 0

    def _rec(items):
        nonlocal comp, move
        if len(items) <= 1:
            return items

        mid = len(items) // 2
        kiri = _rec(items[:mid])
        kanan = _rec(items[mid:])

        hasil = []
        i = 0
        j = 0

        while i < len(kiri) and j < len(kanan):
            comp += 1
            # pakai <= biar stabil (elemen dari kiri didahulukan jika kunci sama)
            if key_func(kiri[i]) <= key_func(kanan[j]):
                hasil.append(kiri[i])
                move += 1
                i += 1
            else:
                hasil.append(kanan[j])
                move += 1
                j += 1

        # salin sisa bagian kiri
        while i < len(kiri):
            hasil.append(kiri[i])
            move += 1
            i += 1

        # salin sisa bagian kanan
        while j < len(kanan):
            hasil.append(kanan[j])
            move += 1
            j += 1

        return hasil

    terurut = _rec(larik)
    return terurut, comp, move, None


# === 3. Linear Search ===
# mencari satu per satu dari depan, O(n)

def linear_search(larik, target, key_func=by_oid):
    comp = 0
    n = len(larik)
    for i in range(n):
        comp += 1
        if key_func(larik[i]) == target:
            return i, comp
    return -1, comp


# === 4. Binary Search ===
# pencarian biner pada data yang sudah terurut, O(log n)

def binary_search(larik_terurut, target, key_func=by_oid):
    lo = 0
    hi = len(larik_terurut) - 1
    comp = 0

    while lo <= hi:
        comp += 1
        mid = (lo + hi) // 2
        val = key_func(larik_terurut[mid])

        if val == target:
            return mid, comp
        elif val < target:
            lo = mid + 1
        else:
            hi = mid - 1

    return -1, comp
