import datetime as dt

TIME_CONSTANTS = {'w': 604_800, 'd': 86_400, 'h': 3_600, 'm': 60, 's': 1, 'ms': 0.001, 'μs': 0.000_001}
BYTE_CONSTANTS = {'tb': 1_024**4, 'gb': 1_024**3, 'mb': 1_024**2, 'kb': 1_024, 'b': 1}

def strfdelta(tdelta: dt.timedelta, max_units: int = 3, stop = 'ms', last_decimals = 0, sep=' '):
    seconds = tdelta.total_seconds()
    return auto_ripper(seconds, TIME_CONSTANTS, max_units, stop, last_decimals, sep)

def strfbytes(nbytes: int, max_units: int = 1, stop = None, last_decimals = 2, sep=''):
    return auto_ripper(nbytes, BYTE_CONSTANTS, max_units, stop, last_decimals, sep)

def auto_ripper(remainder: float, fields: dict, max_units: int = 3, stop: str = None, last_decimals: int = 0, sep = " ") -> str:
    values = {}
    assigning = False
    results = []

    for field in fields:
        values[field], remainder = divmod(remainder, fields[field])
        if values[field]:
            assigning = True
        if assigning:
            calc_val = int(values[field])
            results.append([str(calc_val), field])
            max_units -= 1
            if not max_units:
                break
        if stop and field == stop:
            break

    if len(results) == 0:
        return ''

    if last_decimals:
        decimals = int(10**last_decimals * (remainder / fields[field]))
        results[-1][0] = f'{results[-1][0]}.{decimals}'

    return sep.join([f"{x}{y}" for x, y in results])
