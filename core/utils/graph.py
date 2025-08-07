import numpy as np
from scipy.interpolate import interp1d


_graph_characters = [
    '⠀⢀⢠⢰⢸',
    '⡀⣀⣠⣰⣸',
    '⡄⣄⣤⣴⣼',
    '⡆⣆⣦⣶⣾',
    '⡇⣇⣧⣷⣿']

def generate_graph_string(data: list, characters: int = 12, cbfmt = lambda x: x):
    up = max(data)
    down = min(data)

    if len(data) == characters * 2:
        new_data = np.array(data)
    else:
        f = interp1d(np.arange(len(data)), np.array(data))
        points = np.linspace(0, len(data) - 1, characters * 2)
        new_data = f(points)

    new_data = ((new_data - down) / (up - down + 1e-6)) * 5
    new_data = np.clip(np.floor(new_data), 0, 4)

    it = iter(new_data)
    graph = ''.join([_graph_characters[int(x)][int(y)] for x, y in zip(it,it)])

    return f"{cbfmt(down)}⇣[{graph}]⇡{cbfmt(up)}"
