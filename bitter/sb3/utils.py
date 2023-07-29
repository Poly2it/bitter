from random import randint

def uid():
    soup = '!#%()*+,-./0123456789:;=?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~'

    chunks = []
    for char in range(20):
        chunks.append(soup[randint(0, len(soup) - 1)])

    return "".join(chunks)