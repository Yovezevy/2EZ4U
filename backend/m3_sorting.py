# m3_sorting.py
# implementasi bubble sort, merge sort, quick sort
# buat ngurutin data pesanan berdasarkan kolom tertentu

import time


def bubble_sort(arr, key_func, ascending=True):
    """
    Bubble sort langsung di Array objek.
    arr harus punya method .get(), .set(), .size
    Worst case O(n^2), best case O(n) kalo udah terurut
    """
    n = arr.size
    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):
            a = key_func(arr.get(j))
            b = key_func(arr.get(j + 1))
            if ascending:
                do_swap = a > b
            else:
                do_swap = a < b
            if do_swap:
                arr.swap(j, j + 1)
                swapped = True
        if not swapped:
            break  # udah terurut, ga perlu lanjut


def merge_sort(data_list, key_func, ascending=True):
    """
    Merge sort, input list biasa, return list baru yang terurut.
    O(n log n) selalu, tapi butuh memory tambahan O(n)
    """
    if len(data_list) <= 1:
        return list(data_list)
    return _merge_sort(list(data_list), key_func, ascending)


def _merge_sort(items, key_func, asc):
    if len(items) <= 1:
        return items
    mid = len(items) // 2
    kiri = _merge_sort(items[:mid], key_func, asc)
    kanan = _merge_sort(items[mid:], key_func, asc)
    return _gabung(kiri, kanan, key_func, asc)


def _gabung(kiri, kanan, key_func, asc):
    hasil = []
    i = 0
    j = 0
    while i < len(kiri) and j < len(kanan):
        k1 = key_func(kiri[i])
        k2 = key_func(kanan[j])
        if asc:
            ambil_kiri = k1 <= k2
        else:
            ambil_kiri = k1 >= k2
        if ambil_kiri:
            hasil.append(kiri[i])
            i += 1
        else:
            hasil.append(kanan[j])
            j += 1
    # sisa
    while i < len(kiri):
        hasil.append(kiri[i])
        i += 1
    while j < len(kanan):
        hasil.append(kanan[j])
        j += 1
    return hasil


def quick_sort(data_list, key_func, ascending=True):
    """
    Quick sort, return list baru yang terurut.
    Rata-rata O(n log n), worst case O(n^2)
    Pake median-of-three biar ngurangin kemungkinan worst case
    """
    items = list(data_list)
    if len(items) > 1:
        _quick_sort(items, 0, len(items) - 1, key_func, ascending)
    return items


def _quick_sort(items, lo, hi, key_func, asc):
    if lo < hi:
        p = _partition(items, lo, hi, key_func, asc)
        _quick_sort(items, lo, p - 1, key_func, asc)
        _quick_sort(items, p + 1, hi, key_func, asc)


def _partition(items, lo, hi, key_func, asc):
    # median of three buat pilih pivot yang lumayan bagus
    mid = (lo + hi) // 2
    if key_func(items[lo]) > key_func(items[mid]):
        items[lo], items[mid] = items[mid], items[lo]
    if key_func(items[lo]) > key_func(items[hi]):
        items[lo], items[hi] = items[hi], items[lo]
    if key_func(items[mid]) > key_func(items[hi]):
        items[mid], items[hi] = items[hi], items[mid]
    # pivot di posisi hi
    items[mid], items[hi] = items[hi], items[mid]

    pivot = key_func(items[hi])
    i = lo - 1
    for j in range(lo, hi):
        val = key_func(items[j])
        if asc:
            cocok = val <= pivot
        else:
            cocok = val >= pivot
        if cocok:
            i += 1
            items[i], items[j] = items[j], items[i]
    items[i + 1], items[hi] = items[hi], items[i + 1]
    return i + 1


# fungsi key buat sorting pesanan
def by_harga(p):
    return p.harga

def by_prioritas(p):
    return p.prioritas

def by_oid(p):
    return p.oid

def by_waktu_masuk(p):
    return p.t_masuk


def sort_dan_ukur(data_list, algo, key_func, ascending=True):
    """
    Jalanin sorting + hitung waktu eksekusi.
    Return (hasil_sorted, waktu_ms)
    """
    start = time.perf_counter()
    if algo == "bubble":
        # bubble sort butuh Array, jadi convert dulu
        from backend.m1_pesanan import Array
        arr = Array(len(data_list) + 1)
        for item in data_list:
            arr.append(item)
        bubble_sort(arr, key_func, ascending)
        hasil = list(arr)
    elif algo == "merge":
        hasil = merge_sort(data_list, key_func, ascending)
    elif algo == "quick":
        hasil = quick_sort(data_list, key_func, ascending)
    else:
        hasil = list(data_list)
    elapsed = (time.perf_counter() - start) * 1000
    return hasil, elapsed
