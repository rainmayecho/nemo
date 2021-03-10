class _TranspositionTable(dict):
    pass


TTable = None


def init_ttable():
    global TTable
    TTable = _TranspositionTable()
    return TTable
