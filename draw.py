import argparse
import math

base_style = {'stroke': '#000000', 'stroke-linejoin': 'round'}

def style_dict_to_str(style):
    return ';'.join(f'{k}: {v}' for k, v in style.items())

def pos2path(pos, style=dict(), close=True):
    style_str = style_dict_to_str(style)
    return '<path d="M ' + ' '.join(f'{a},{b}' for a, b in pos) + (' Z"' if close else '"') + f' style="{style_str}" />'

def rect(x, y, w, h, scale, colors=('#60a2c5ff',  '#316884ff', '#bdd1dcff')):
    dw, dh = 0.3*scale, 0.3*scale
    front = pos2path([[x, y], [x, y+h], [x+w, y+h], [x+w, y]], dict(base_style, **{'fill': colors[0]}))
    side = pos2path([[x+w, y+h], [x+w + dw, y+h - dh], [x+w + dw, y-dh], [x+w, y]], dict(base_style, **{'fill': colors[1]}))
    top = pos2path([[x, y], [x+w, y], [x+w + dw, y - dh], [x + dw, y - dh]], dict(base_style, **{'fill': colors[2]}))
    return front + side + top

def skip_connection(x1, y1, x2, y2, base_height):
    return pos2path([[x1, y1], [x1, base_height], [x2, base_height], [x2, y2]],
                    {'fill': 'none', 'stroke': '#000', 'stroke-width': '1', 'marker-end': 'url(#triangle)', 'stroke-dasharray': '2,2'},
                    close=False)

def arrow(x, y, style=dict(), length=25):
    vsize = length / 4
    bsize = length / 12
    head = pos2path([[x + length, y], [x+length / 2, y+vsize], [x+length / 2, y - vsize]], style)
    return head + pos2path([[x, y-bsize], [x, y+bsize], [x+length / 2, y+bsize], [x+length / 2, y-bsize]], style)

def text(x, y, size, txt):
    style = style_dict_to_str({'font-size': str(size) + 'pt', 'font-family': 'Sans', 'font-weight': 'bold'})
    return f'<text x="{x}" y="{y}" style="{style}">{txt}</text>'

color_palettes = {
    'blue': ('#60a2c5',  '#316884', '#bdd1dc'),
    'yellow': ('#c59860', '#6a5526', '#cec0ae'),
    'red': ('#c44747', '#7e2828', '#ba8c8c'),
    'green': ('#499744', '#2d5d2a', '#8cb98a')
}


def draw(channels=(1, 8, 32, 64), pool=(2, 2, 1, 1), sizes=None, connections=(),
         spacing=30, off=(50, 200), log_width=False, min_width=10, sqrt_height=False, font_size=8, scale=150, scale_width=1,
         filename='output.svg', color='blue', arrow_size=0):

    spacings = [[spacing] if len(c) == 1 else [0,spacing] for c in channels]
    spacings = [x for sp in spacings for x in sp]
    channels = [x for c in channels for x in c]
    

    # fill with defaults
    pool = [pool[i] if len(pool) > i else 1 for i, _ in enumerate(channels)] if pool is not None else [1] * len(channels)
    sizes = [sizes[i] if len(sizes) > i else sizes[-1] for i, _ in enumerate(channels)] if sizes is not None else [None] * len(channels)

    svg = """<svg xmlns="http://www.w3.org/2000/svg">
    <defs>
        <marker id="triangle" viewBox="0 0 10 10" refX="10" refY="5" markerUnits="strokeWidth" markerWidth="12" markerHeight="12" orient="auto">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#000"/>
        </marker>
    </defs>
    """
    max_c = max(channels)
    current_x = 0
    current_scale = scale
    current_y = 0

    pos_sizes = []

    for i, (c, p, size, space) in enumerate(zip(channels, pool, sizes, spacings)):
        width = c/max_c if not log_width else math.log(c) / math.log(max(channels))
        width = width * scale_width
        width = max(min_width, width*scale)

        colors = ('#757575', '#505050', '#b0b0b0') if i == 0 else color_palettes[color]

        svg += rect(off[0] + current_x, off[1] + current_y, width, current_scale, current_scale, colors=colors) + '\n'
        svg += text(off[0] + current_x + 0.5*width - 5, off[1] + current_y + current_scale + font_size + 3, font_size, str(c)) + '\n'
        
        if spacings[i-1] > 0 and size is not None:
            svg += text(off[0] + current_x - len(str(size))*font_size, off[1] + scale / 2 + font_size / 2, font_size, str(size)) + '\n'

        if spacings[i] > 0 and i < len(spacings) - 1 and arrow_size > 0:
            svg += arrow(off[0] + current_x + width + (space - 25) / 2, off[1] + scale / 2 - 5, {'stroke': 0}, arrow_size)

        pos_sizes += [[off[0] + current_x + 0.5*width, width, off[1] + current_y]]

        if sqrt_height:
            current_scale = current_scale // math.sqrt(p)
        else:
            current_scale = current_scale // p
        current_y = (scale - current_scale) / 2

        current_x += width + space

    for i, (start, end) in enumerate(connections):
        svg += skip_connection(pos_sizes[start][0] + 0.3*pos_sizes[start][1], pos_sizes[start][2], pos_sizes[end][0], pos_sizes[end][2], off[1] - 100 + i*15)

    svg += '</svg>'
    open(filename, 'w').write(svg)
    print(f'SVG output was written to {filename}')


if __name__ == '__main__':

    def tuple_list(inp):
        return [int(a) for a in inp.split(',')]

    def channels(x):
        if '-' in x:
            return [int(a) for a in x.split('-')]
        else:
            return [int(x)]

    parser = argparse.ArgumentParser()

    parser.add_argument('channels', help="Channel sizes (separated by space)", type=channels, nargs='+')
    parser.add_argument('--pool', help="Pooling (separated by space)", type=float, nargs='+')
    parser.add_argument('--sizes', help="Tensor sizes", type=int, nargs='+')
    parser.add_argument('--connections', help="Connections between layers", type=tuple_list, nargs='+', default=())
    parser.add_argument('--color', help="base color: red, green, blue or yellow", default='blue')
    parser.add_argument('--font-size', help="size of the font", type=float, default=8)
    parser.add_argument('--spacing', help="Spacing between activations", type=float, default=30)
    parser.add_argument('--arrow-size', help="Size of the arrows", type=float, default=0)
    parser.add_argument('--filename', help="output filename", default='output.svg')

    parser.add_argument('--off', help="Offset", default=(50, 200))
    parser.add_argument('--log-width', help="flag to apply logarithm on activation widths", default=False)
    parser.add_argument('--sqrt-height', help="flag to apply square root on activation heights", default=False)
    parser.add_argument('--scale', help="base scale", default=150)
    parser.add_argument('--scale-width', help="scale width", type=float, default=1.0)
    parser.add_argument('--min-width', help="minimal width of activations", default=10)

    args = parser.parse_args()

    channels = args.channels
    del args.__dict__['channels']

    draw(channels, **args.__dict__)


