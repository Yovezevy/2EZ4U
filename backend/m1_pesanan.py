# m1_pesanan.py
# modul buat nyimpen data pesanan pake Array sama LinkedList
# ga boleh pake dict, set, list.insert, dll (sesuai aturan tugas)

class Pesanan:
    __slots__ = ("oid", "pelanggan", "resto", "menu",
                 "harga", "prioritas", "t_masuk", "t_selesai", "status")

    def __init__(self, oid, pelanggan, resto, menu,
                 harga, prioritas, t_masuk, t_selesai, status):
        self.oid = oid
        self.pelanggan = pelanggan
        self.resto = resto
        self.menu = menu
        self.harga = int(harga)
        self.prioritas = int(prioritas)
        self.t_masuk = int(t_masuk) if t_masuk else 0
        self.t_selesai = int(t_selesai) if t_selesai else 0
        self.status = status

    def __repr__(self):
        return (f"Pesanan({self.oid}, {self.pelanggan}, {self.resto}, "
                f"{self.menu}, {self.harga}, P{self.prioritas}, {self.status})")


# --- parser csv manual (ga pake import csv) ---

def _parse_csv_line(line):
    fields = []
    current = []
    in_quotes = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            in_quotes = not in_quotes
        elif ch == ',' and not in_quotes:
            fields.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
        i += 1
    fields.append(''.join(current).strip())
    return fields


def load_pesanan(filepath):
    hasil = []
    with open(filepath, 'r', encoding='utf-8') as f:
        f.readline()  # skip header
        for line in f:
            line = line.strip()
            if not line:
                continue
            fields = _parse_csv_line(line)
            if len(fields) >= 9:
                p = Pesanan(
                    fields[0], fields[1], fields[2], fields[3],
                    fields[4], fields[5], fields[6], fields[7], fields[8]
                )
                hasil.append(p)
    return hasil


# === Array Dinamis ===
# pake strategi doubling kalo udah penuh

class Array:
    def __init__(self, capacity=4):
        self.capacity = capacity
        self.size = 0
        self.data = [None] * self.capacity

    def _resize(self, new_cap):
        new_data = [None] * new_cap
        for i in range(self.size):
            new_data[i] = self.data[i]
        self.data = new_data
        self.capacity = new_cap

    def append(self, v):
        # O(1) amortized
        if self.size == self.capacity:
            self._resize(self.capacity * 2)
        self.data[self.size] = v
        self.size += 1

    def insert(self, i, v):
        # O(n) karena harus geser elemen ke kanan
        if i < 0 or i > self.size:
            raise IndexError("Index out of bounds")
        if self.size == self.capacity:
            self._resize(self.capacity * 2)
        for j in range(self.size, i, -1):
            self.data[j] = self.data[j - 1]
        self.data[i] = v
        self.size += 1

    def get(self, i):
        # O(1) akses langsung
        if i < 0 or i >= self.size:
            raise IndexError("Index out of bounds")
        return self.data[i]

    def set(self, i, v):
        if i < 0 or i >= self.size:
            raise IndexError("Index out of bounds")
        self.data[i] = v

    def remove(self, i):
        # O(n) karena harus geser elemen ke kiri
        if i < 0 or i >= self.size:
            raise IndexError("Index out of bounds")
        removed = self.data[i]
        for j in range(i, self.size - 1):
            self.data[j] = self.data[j + 1]
        self.data[self.size - 1] = None
        self.size -= 1
        return removed

    def swap(self, i, j):
        tmp = self.data[i]
        self.data[i] = self.data[j]
        self.data[j] = tmp

    def __len__(self):
        return self.size

    def __iter__(self):
        for i in range(self.size):
            yield self.data[i]

    # method khusus pesanan
    def tambah_reguler(self, v):
        # masuk belakang, O(1) amortized
        self.append(v)

    def tambah_prioritas(self, v):
        # masuk tengah, O(n) geser
        self.insert(self.size // 2, v)

    def tambah_vip(self, v):
        # masuk paling depan, O(n) geser semua
        self.insert(0, v)

    def hapus_pesanan(self, i):
        return self.remove(i)

    def lihat_pesanan(self, i):
        return self.get(i)


# === Linked List ===

class Node:
    __slots__ = ("data", "next")
    def __init__(self, data):
        self.data = data
        self.next = None


class LinkList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def append(self, v):
        # O(1) karena ada pointer tail
        nn = Node(v)
        if self.head is None:
            self.head = nn
            self.tail = nn
        else:
            self.tail.next = nn
            self.tail = nn
        self.size += 1

    def insert(self, i, v):
        # O(n) telusur + O(1) sisip
        if i < 0 or i > self.size:
            raise IndexError("Index out of bounds")
        nn = Node(v)
        if i == 0:
            nn.next = self.head
            self.head = nn
            if self.tail is None:
                self.tail = nn
        else:
            cur = self.head
            for _ in range(i - 1):
                cur = cur.next
            nn.next = cur.next
            cur.next = nn
            if nn.next is None:
                self.tail = nn
        self.size += 1

    def get(self, i):
        # O(n) telusur
        if i < 0 or i >= self.size:
            raise IndexError("Index out of bounds")
        cur = self.head
        for _ in range(i):
            cur = cur.next
        return cur.data

    def remove(self, i):
        # O(n) telusur + O(1) cabut node
        if i < 0 or i >= self.size:
            raise IndexError("Index out of bounds")
        if i == 0:
            removed = self.head.data
            self.head = self.head.next
            if self.head is None:
                self.tail = None
        else:
            cur = self.head
            for _ in range(i - 1):
                cur = cur.next
            removed = cur.next.data
            cur.next = cur.next.next
            if cur.next is None:
                self.tail = cur
        self.size -= 1
        return removed

    def __len__(self):
        return self.size

    def __iter__(self):
        cur = self.head
        while cur is not None:
            yield cur.data
            cur = cur.next

    def tambah_reguler(self, v):
        self.append(v)

    def tambah_prioritas(self, v):
        self.insert(self.size // 2, v)

    def tambah_vip(self, v):
        self.insert(0, v)

    def hapus_pesanan(self, i):
        return self.remove(i)

    def lihat_pesanan(self, i):
        return self.get(i)
