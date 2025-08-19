COLORS = {
    "dark_grey": (0.1, 0.1, 0.1),
}

def get_color(name):
    if name in COLORS:
        return COLORS[name]
    else:
        raise KeyError(f'Color {name} not found in COLORS dictionary')
