"""Independent vector document model. Coordinates are SVG/CSS pixels."""
from dataclasses import dataclass, field, asdict
import copy
import json
import math
from xml.etree.ElementTree import Element, SubElement, tostring

KINDS = {'rect', 'ellipse', 'line', 'bezier', 'text'}

@dataclass
class Shape:
    kind: str
    points: list
    fill: str = '#22c55e'
    stroke: str = '#202020'
    width: float = 1.5
    text: str = ''
    size: float = 24

    def bounds(self):
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        if self.kind == 'text':
            return xs[0], ys[0], xs[0] + max(1, len(self.text)) * self.size * .65, ys[0] + self.size * 1.3
        return min(xs), min(ys), max(xs), max(ys)

    def move(self, dx, dy):
        self.points = [[x + dx, y + dy] for x, y in self.points]

    def samples(self, steps=48):
        if self.kind != 'bezier':
            return self.points
        a, b, c, d = self.points
        return [[(1-t)**3*a[k] + 3*(1-t)**2*t*b[k] + 3*(1-t)*t*t*c[k] + t**3*d[k]
                 for k in (0, 1)] for t in [i/steps for i in range(steps+1)]]

@dataclass
class Document:
    width: float = 1122.52
    height: float = 1587.4
    shapes: list = field(default_factory=list)

    def dumps(self):
        return json.dumps({'format': 'cdvector', 'version': 1, 'width': self.width,
                           'height': self.height, 'shapes': [asdict(s) for s in self.shapes]}, ensure_ascii=False, indent=2)

    @classmethod
    def loads(cls, source):
        data = json.loads(source)
        if data.get('format') != 'cdvector' or data.get('version') != 1:
            raise ValueError('Formato ou versão de projeto não suportado.')
        def number(v):
            return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and abs(v) <= 1e7
        if not all(number(data.get(k)) and data[k] > 0 for k in ('width', 'height')):
            raise ValueError('Dimensões inválidas.')
        if not isinstance(data.get('shapes'), list) or len(data['shapes']) > 10000:
            raise ValueError('Lista de objetos inválida ou muito grande.')
        result = cls(data['width'], data['height'])
        for row in data['shapes']:
            shape = Shape(**row)
            count = {'rect': 2, 'ellipse': 2, 'line': 2, 'bezier': 4, 'text': 1}.get(shape.kind)
            if count is None or len(shape.points) != count:
                raise ValueError('Geometria inválida.')
            if not all(isinstance(p, list) and len(p) == 2 and all(number(v) for v in p) for p in shape.points):
                raise ValueError('Coordenadas inválidas.')
            if not number(shape.width) or shape.width < 0 or not number(shape.size) or shape.size <= 0:
                raise ValueError('Espessura ou tamanho inválido.')
            if not isinstance(shape.text, str) or len(shape.text) > 100000:
                raise ValueError('Texto inválido.')
            for color in (shape.fill, shape.stroke):
                if color != 'none' and (not isinstance(color, str) or len(color) != 7 or color[0] != '#' or any(c not in '0123456789abcdefABCDEF' for c in color[1:])):
                    raise ValueError('Cor inválida.')
            result.shapes.append(shape)
        return result

    def svg(self):
        root = Element('svg', xmlns='http://www.w3.org/2000/svg', width=str(self.width), height=str(self.height), viewBox=f'0 0 {self.width} {self.height}')
        for s in self.shapes:
            attrs = {'fill': s.fill, 'stroke': s.stroke, 'stroke-width': str(s.width)}
            x, y, r, b = s.bounds()
            if s.kind == 'rect':
                SubElement(root, 'rect', attrs | dict(x=str(x), y=str(y), width=str(r-x), height=str(b-y)))
            elif s.kind == 'ellipse':
                SubElement(root, 'ellipse', attrs | dict(cx=str((x+r)/2), cy=str((y+b)/2), rx=str((r-x)/2), ry=str((b-y)/2)))
            elif s.kind == 'line':
                a, b = s.points
                SubElement(root, 'line', attrs | dict(x1=str(a[0]), y1=str(a[1]), x2=str(b[0]), y2=str(b[1])))
            elif s.kind == 'bezier':
                a, b, c, d = s.points
                SubElement(root, 'path', attrs | {'d': f'M {a[0]} {a[1]} C {b[0]} {b[1]} {c[0]} {c[1]} {d[0]} {d[1]}', 'fill': 'none'})
            else:
                SubElement(root, 'text', attrs | {'x': str(x), 'y': str(y), 'dominant-baseline': 'text-before-edge', 'font-family': 'Arial', 'font-size': str(s.size)}).text = s.text
        return tostring(root, encoding='unicode')

class History:
    def __init__(self):
        self.undo_stack, self.redo_stack = [], []

    def record(self, doc):
        self.undo_stack.append(copy.deepcopy(doc))
        self.undo_stack = self.undo_stack[-100:]
        self.redo_stack.clear()

    def undo(self, doc):
        if not self.undo_stack: return doc
        self.redo_stack.append(copy.deepcopy(doc))
        return self.undo_stack.pop()

    def redo(self, doc):
        if not self.redo_stack: return doc
        self.undo_stack.append(copy.deepcopy(doc))
        return self.redo_stack.pop()
