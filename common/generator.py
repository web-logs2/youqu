import random


def generate_uuid():
    def replacer(c):
        r = random.randint(0, 15)
        v = r if c == 'x' else (r & 0x3 | 0x8)
        return format(v, 'x')

    id_template = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'
    id = ''.join([replacer(c) for c in id_template])
    return id
