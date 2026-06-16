import hashlib
import random
from babytrack.options import Opts

def _hex_from_int(n: int) -> str:
    return "#{:06x}".format(n & 0xFFFFFF)

def resolve_color(opts: Opts, label: str) -> str:
    if opts.color_mode == "single":
        return opts.color
    if opts.color_mode == "by-label":
        h = hashlib.md5(label.encode()).hexdigest()
        return "#" + h[:6]
    return _hex_from_int(random.randint(0, 0xFFFFFF))
