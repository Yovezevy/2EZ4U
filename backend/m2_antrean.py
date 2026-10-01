
class CircularQueue:
    """Antrean melingkar berbasis array tetap (FIFO).

    Kompleksitas:
        enqueue  – O(1)
        dequeue  – O(1)
        peek     – O(1)
    """

    def __init__(self, capacity=200001):
        self.capacity = capacity
        self.data = [None] * self.capacity
        self.front = 0
        self.rear = -1
        self.size = 0

    def is_empty(self):
        return self.size == 0

    def is_full(self):
        return self.size == self.capacity

    def enqueue(self, v):
        """Masukkan elemen ke belakang antrean – O(1)."""
        if self.is_full():
            raise OverflowError("Queue penuh")
        self.rear = (self.rear + 1) % self.capacity
        self.data[self.rear] = v
        self.size += 1

    def dequeue(self):
        """Keluarkan elemen dari depan antrean – O(1)."""
        if self.is_empty():
            raise IndexError("Queue kosong")
        val = self.data[self.front]
        self.data[self.front] = None
        self.front = (self.front + 1) % self.capacity
        self.size -= 1
        return val

    def peek(self):
        """Lihat elemen paling depan tanpa mengeluarkan – O(1)."""
        if self.is_empty():
            raise IndexError("Queue kosong")
        return self.data[self.front]

    def __len__(self):
        return self.size

    def __iter__(self):
        idx = self.front
        for _ in range(self.size):
            yield self.data[idx]
            idx = (idx + 1) % self.capacity

class Stack:
    """Tumpukan (stack) berbasis array dinamis.

    Kompleksitas:
        push – O(1) amortized
        pop  – O(1)
        peek – O(1)
    """

    def __init__(self):
        self.capacity = 16
        self.data = [None] * self.capacity
        self.size = 0

    def _resize(self, new_cap):
        new_data = [None] * new_cap
        for i in range(self.size):
            new_data[i] = self.data[i]
        self.data = new_data
        self.capacity = new_cap

    def is_empty(self):
        return self.size == 0

    def push(self, v):
        """Dorong elemen ke puncak stack – O(1) amortized."""
        if self.size == self.capacity:
            self._resize(self.capacity * 2)
        self.data[self.size] = v
        self.size += 1

    def pop(self):
        """Keluarkan elemen dari puncak stack – O(1)."""
        if self.is_empty():
            raise IndexError("Stack kosong")
        self.size -= 1
        val = self.data[self.size]
        self.data[self.size] = None
        return val

    def peek(self):
        """Lihat elemen paling atas tanpa mengeluarkan – O(1)."""
        if self.is_empty():
            raise IndexError("Stack kosong")
        return self.data[self.size - 1]

    def __len__(self):
        return self.size

    def __iter__(self):
        for i in range(self.size - 1, -1, -1):
            yield self.data[i]

class UndoManager:
    """Mencatat setiap aksi ke dalam Stack sehingga bisa di-undo.

    Cara pakai:
        undo_mgr = UndoManager()

        # Saat user menambah pesanan:
        undo_mgr.catat("tambah", {"indeks": 0, "pesanan": obj})

        # Saat user menekan tombol Undo:
        aksi, data = undo_mgr.undo()
        if aksi == "tambah":
            antrean.hapus_pesanan(data["indeks"])
    """

    def __init__(self):
        self.history = Stack()

    def catat(self, aksi, data):
        """Catat sebuah aksi ke dalam history.

        Args:
            aksi (str): jenis aksi, misal 'tambah_reguler', 'tambah_vip',
                        'tambah_prioritas', 'hapus', 'proses'
            data:       informasi yang dibutuhkan untuk membalik aksi
                        (misal objek Pesanan, indeks, dsb.)
        """
        self.history.push((aksi, data))

    def undo(self):
        """Kembalikan aksi terakhir.

        Returns:
            tuple (aksi, data) atau None jika history kosong.
        """
        if self.history.is_empty():
            return None
        return self.history.pop()

    def is_empty(self):
        return self.history.is_empty()

    def __len__(self):
        return len(self.history)
