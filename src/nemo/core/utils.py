def lsb_1(v: int) -> int:
    return v & -v


def popcnt(v: int) -> int:
    return bin(v).count("1")
