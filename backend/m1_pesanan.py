# ============================================================
# M1 – Pesanan: Array Dinamis & Linked List
# Struktur data dasar untuk menyimpan daftar pesanan 2EZ4U
# ============================================================


class Pesanan:
    """Representasi satu baris pesanan (pengganti dict/namedtuple)."""
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


# ============================================================
# CSV Reader  (tanpa modul csv bawaan)
# ============================================================

def _parse_csv_line(line):
    """Parse satu baris CSV, menangani field yang dikutip (quoted)."""
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
    """Membaca pesanan.csv dan mengembalikan list Python biasa berisi objek Pesanan."""
    hasil = []
    with open(filepath, 'r', encoding='utf-8') as f:
        header = f.readline()  # skip header
        for line in f:
            line = line.strip()
            if not line:
                continue
            fields = _parse_csv_line(line)
            if len(fields) >= 9:
                p = Pesanan(
                    oid=fields[0],
                    pelanggan=fields[1],
                    resto=fields[2],
                    menu=fields[3],
                    harga=fields[4],
                    prioritas=fields[5],
                    t_masuk=fields[6],
                    t_selesai=fields[7],
                    status=fields[8],
                )
                hasil.append(p)
    return hasil


# ============================================================
# Array Dinamis  (tanpa built-in list.append / list.insert)
# ============================================================

class Array:
    """Array dinamis yang tumbuh otomatis (doubling strategy)."""

    def __init__(self, capacity=4):
        self.capacity = capacity
        self.size = 0
        self.data = [None] * self.capacity

    # -- internal --
    def _resize(self, new_capacity):
        new_data = [None] * new_capacity
        for i in range(self.size):
            new_data[i] = self.data[i]
        self.data = new_data
        self.capacity = new_capacity

    # -- primitif --
    def append(self, v):
        """Sisip di akhir – O(1) amortized."""
        if self.size == self.capacity:
            self._resize(self.capacity * 2)
        self.data[self.size] = v
        self.size += 1

    def insert(self, i, v):
        """Sisip pada indeks i – O(n) geser."""
        if i < 0 or i > self.size:
            raise IndexError("Index out of bounds")
        if self.size == self.capacity:
            self._resize(self.capacity * 2)
        for j in range(self.size, i, -1):
            self.data[j] = self.data[j - 1]
        self.data[i] = v
        self.size += 1

    def get(self, i):
        """Akses indeks i – O(1)."""
        if i < 0 or i >= self.size:
            raise IndexError("Index out of bounds")
        return self.data[i]

    def set(self, i, v):
        """Ubah nilai pada indeks i – O(1)."""
        if i < 0 or i >= self.size:
            raise IndexError("Index out of bounds")
        self.data[i] = v

    def remove(self, i):
        """Hapus elemen pada indeks i – O(n) geser."""
        if i < 0 or i >= self.size:
            raise IndexError("Index out of bounds")
        removed = self.data[i]
        for j in range(i, self.size - 1):
            self.data[j] = self.data[j + 1]
        self.data[self.size - 1] = None
        self.size -= 1
        return removed

    def __len__(self):
        return self.size

    def __iter__(self):
        for i in range(self.size):
            yield self.data[i]

    # -- metode bisnis pesanan --
    def tambah_reguler(self, v):
        """Pesanan biasa → masuk di ujung belakang – O(1) amortized."""
        self.append(v)

    def tambah_prioritas(self, v):
        """Pesanan prioritas → masuk di tengah antrean – O(n)."""
        self.insert(self.size // 2, v)

    def tambah_vip(self, v):
        """Pesanan VIP → masuk di urutan pertama – O(n)."""
        self.insert(0, v)

    def hapus_pesanan(self, i):
        """Hapus pesanan pada indeks ke-i – O(n)."""
        return self.remove(i)

    def lihat_pesanan(self, i):
        """Lihat pesanan pada indeks ke-i – O(1)."""
        return self.get(i)


# ============================================================
# Linked List  (Singly Linked List)
# ============================================================

class Node:
    __slots__ = ("data", "next")

    def __init__(self, data):
        self.data = data
        self.next = None


class LinkList:
    """Singly linked list dengan pointer head & tail."""

    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    # -- primitif --
    def append(self, v):
        """Sisip di akhir – O(1)."""
        new_node = Node(v)
        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node
        self.size += 1

    def insert(self, i, v):
        """Sisip pada indeks i – O(n) telusur + O(1) sisip."""
        if i < 0 or i > self.size:
            raise IndexError("Index out of bounds")
        new_node = Node(v)
        if i == 0:
            new_node.next = self.head
            self.head = new_node
            if self.tail is None:
                self.tail = new_node
        else:
            current = self.head
            for _ in range(i - 1):
                current = current.next
            new_node.next = current.next
            current.next = new_node
            if new_node.next is None:
                self.tail = new_node
        self.size += 1

    def get(self, i):
        """Akses indeks i – O(n) telusur."""
        if i < 0 or i >= self.size:
            raise IndexError("Index out of bounds")
        current = self.head
        for _ in range(i):
            current = current.next
        return current.data

    def remove(self, i):
        """Hapus elemen pada indeks i – O(n) telusur + O(1) cabut."""
        if i < 0 or i >= self.size:
            raise IndexError("Index out of bounds")
        if i == 0:
            removed = self.head.data
            self.head = self.head.next
            if self.head is None:
                self.tail = None
        else:
            current = self.head
            for _ in range(i - 1):
                current = current.next
            removed = current.next.data
            current.next = current.next.next
            if current.next is None:
                self.tail = current
        self.size -= 1
        return removed

    def __len__(self):
        return self.size

    def __iter__(self):
        current = self.head
        while current is not None:
            yield current.data
            current = current.next

    # -- metode bisnis pesanan --
    def tambah_reguler(self, v):
        """Pesanan biasa → masuk di ujung belakang – O(1)."""
        self.append(v)

    def tambah_prioritas(self, v):
        """Pesanan prioritas → masuk di tengah antrean – O(n) telusur."""
        self.insert(self.size // 2, v)

    def tambah_vip(self, v):
        """Pesanan VIP → masuk di urutan pertama – O(1)."""
        self.insert(0, v)

    def hapus_pesanan(self, i):
        """Hapus pesanan pada indeks ke-i – O(n)."""
        return self.remove(i)

    def lihat_pesanan(self, i):
        """Lihat pesanan pada indeks ke-i – O(n)."""
        return self.get(i)
