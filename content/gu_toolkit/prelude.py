from __future__ import annotations

__all__=[]
# --- The deliberate classroom prelude ---
import sympy as sp
__all__+=["sp"]
from sympy import *
__all__+= list(getattr(sp, "__all__", []))
import numpy as np
__all__+=["np"]

import pandas as pd
__all__+=["pd"]

# print("__all__ (from prelude):",__all__)

# Standard symbols (override/define explicitly for consistency)
x, y, z, t = sp.symbols("x y z t")
__all__+=["x","y","z","t"]
k, l, m, n = sp.symbols("k l m n", integer=True)
__all__+=["k","l","m","n"]
f, g, h = sp.symbols("f g h", cls=sp.Function)
__all__+=["f","g","h"]


class IndexedSymbol:
    def __init__(self, base_name):
        self.base_name = base_name
    
    def __getitem__(self, n):
        return sp.symbols(f'{self.base_name}_{n}')
    
    def __call__(self, *indices):
        """Alternative syntax: a(1,2) instead of a[1,2]"""
        if len(indices) == 1:
            return self[indices[0]]
        else:
            indices_str = '_'.join(str(i) for i in indices)
            return sp.symbols(f'{self.base_name}_{indices_str}')
        
a = IndexedSymbol('a')
b = IndexedSymbol('b')
c = IndexedSymbol('c')
__all__+=["a","b","c"]

from IPython.display import Latex 
__all__+=["Latex"]

