# m2_antrean.py
# stack (postfix calculator + undo/redo) dan queue (naif vs circular)

from backend.m1_pesanan import Array


# === Stack ===

class Stack:
    def __init__(self):
        self.data = Array(16)

    def is_empty(self):
        return self.data.size == 0

    def push(self, v):
        self.data.append(v)

    def pop(self):
        if self.is_empty():
            raise IndexError("Stack kosong")
        return self.data.pop_back()

    def peek(self):
        if self.is_empty():
            raise IndexError("Stack kosong")
        return self.data.get(self.data.size - 1)

    def __len__(self):
        return self.data.size

    def __iter__(self):
        for i in range(self.data.size - 1, -1, -1):
            yield self.data.get(i)


# === Mesin Kasir: infix -> postfix -> hitung ===

def _prioritas_op(op):
    if op in ('+', '-'):
        return 1
    if op in ('*', '/'):
        return 2
    return 0

def tokenize(ekspresi):
    # pecah string jadi list token, angka multi-digit jadi satu token
    tokens = []
    i = 0
    while i < len(ekspresi):
        ch = ekspresi[i]
        if ch == ' ':
            i += 1
            continue
        if ch.isdigit():
            num = []
            while i < len(ekspresi) and ekspresi[i].isdigit():
                num.append(ekspresi[i])
                i += 1
            tokens.append(''.join(num))
        else:
            tokens.append(ch)
            i += 1
    return tokens


def ke_postfix(ekspresi):
    """Konversi infix ke postfix pake shunting-yard. Return (list_postfix, list_langkah)"""
    tokens = tokenize(ekspresi)
    output = []
    ops = Stack()
    langkah = []  # buat ditampilin di UI

    for token in tokens:
        if token.isdigit():
            output.append(token)
            langkah.append((token, "angka, langsung keluar",
                           _stack_str(ops), ' '.join(output)))
        elif token == '(':
            ops.push(token)
            langkah.append((token, "push (",
                           _stack_str(ops), ' '.join(output)))
        elif token == ')':
            while not ops.is_empty() and ops.peek() != '(':
                output.append(ops.pop())
            if not ops.is_empty():
                ops.pop()  # buang '('
            langkah.append((token, "pop sampai (, buang (",
                           _stack_str(ops), ' '.join(output)))
        else:
            # operator: +, -, *, /
            while (not ops.is_empty() and ops.peek() != '(' and
                   _prioritas_op(ops.peek()) >= _prioritas_op(token)):
                output.append(ops.pop())
            ops.push(token)
            langkah.append((token, f"push {token}",
                           _stack_str(ops), ' '.join(output)))

    # sisa stack
    while not ops.is_empty():
        output.append(ops.pop())
    langkah.append(("akhir", "pop sisa stack",
                    _stack_str(ops), ' '.join(output)))

    return output, langkah


def hitung_postfix(postfix_tokens):
    """Evaluasi postfix, return (total, list_langkah)"""
    angka = Stack()
    langkah = []

    for token in postfix_tokens:
        if token.lstrip('-').isdigit():
            angka.push(int(token))
            langkah.append((token, "push", _stack_str(angka), ""))
        else:
            b = angka.pop()  # yang keluar pertama = operand kanan
            a = angka.pop()
            if token == '+':
                hasil = a + b
            elif token == '-':
                hasil = a - b
            elif token == '*':
                hasil = a * b
            elif token == '/':
                hasil = a // b if b != 0 else 0
            angka.push(hasil)
            langkah.append((token, f"{a} {token} {b} = {hasil}",
                           _stack_str(angka), ""))

    total = angka.pop() if not angka.is_empty() else 0
    return total, langkah


def _stack_str(s):
    items = []
    for i in range(s.data.size):
        items.append(str(s.data.get(i)))
    return ' '.join(items)


# === Antrean Naif (buat perbandingan) ===

class AntreanNaif:
    """Queue naif pake Array biasa, dequeue geser semua elemen"""
    def __init__(self):
        self.data = Array(4)
        self.total_geser = 0

    def is_empty(self):
        return self.data.size == 0

    def enqueue(self, v):
        self.data.append(v)

    def dequeue(self):
        if self.is_empty():
            raise IndexError("Queue kosong")
        val = self.data.get(0)
        # geser semua elemen ke kiri, ini yang bikin lambat
        geser = self.data.size - 1
        self.data.remove(0)
        self.total_geser += geser
        return val, geser

    def __len__(self):
        return self.data.size


# === Antrean Melingkar ===

class AntreanMelingkar:
    """Circular queue, dequeue O(1) tanpa geser"""
    def __init__(self, capacity=32768):
        self.capacity = capacity
        self.data = [None] * self.capacity
        self.front = 0
        self.rear = 0
        self.count = 0  # pake count buat bedain kosong vs penuh

    def is_empty(self):
        return self.count == 0

    def is_full(self):
        return self.count == self.capacity

    def _grow(self):
        # kalo penuh, bikin baru 2x lipat
        new_cap = self.capacity * 2
        new_data = [None] * new_cap
        idx = self.front
        for i in range(self.count):
            new_data[i] = self.data[idx]
            idx = (idx + 1) % self.capacity
        self.data = new_data
        self.front = 0
        self.rear = self.count
        self.capacity = new_cap

    def enqueue(self, v):
        if self.is_full():
            self._grow()
        self.data[self.rear] = v
        self.rear = (self.rear + 1) % self.capacity
        self.count += 1

    def dequeue(self):
        if self.is_empty():
            raise IndexError("Queue kosong")
        val = self.data[self.front]
        self.data[self.front] = None
        self.front = (self.front + 1) % self.capacity
        self.count -= 1
        return val

    def peek(self):
        if self.is_empty():
            raise IndexError("Queue kosong")
        return self.data[self.front]

    def enqueue_front(self, v):
        # buat undo: masukin balik ke depan
        if self.is_full():
            self._grow()
        self.front = (self.front - 1) % self.capacity
        self.data[self.front] = v
        self.count += 1

    def __len__(self):
        return self.count


# === Undo / Redo ===

class UndoRedo:
    def __init__(self):
        self.undo_stack = Stack()
        self.redo_stack = Stack()

    def catat(self, aksi, data):
        # aksi baru -> push ke undo, kosongkan redo
        self.undo_stack.push((aksi, data))
        # redo dikosongkan karena riwayat bercabang
        while not self.redo_stack.is_empty():
            self.redo_stack.pop()

    def undo_last(self):
        if self.undo_stack.is_empty():
            return None
        entry = self.undo_stack.pop()
        self.redo_stack.push(entry)
        return entry

    def redo_last(self):
        if self.redo_stack.is_empty():
            return None
        entry = self.redo_stack.pop()
        self.undo_stack.push(entry)
        return entry

    @property
    def undo_depth(self):
        return len(self.undo_stack)

    @property
    def redo_depth(self):
        return len(self.redo_stack)
