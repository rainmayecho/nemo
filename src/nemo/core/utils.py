def lsb_1(v: int) -> int:
    """Returns the least significant bit of the input."""
    return v & -v


def popcnt(v: int) -> int:
    """Returns the number of ones in a binary representation of the input."""
    return bin(v).count("1")
