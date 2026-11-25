"""Tiny helper to generate draw.io (.drawio) files: component diagrams and sequence diagrams."""
from xml.sax.saxutils import quoteattr

C = {  # zone colours
    "client": ("#dae8fc", "#6c8ebf"), "edge": ("#fff2cc", "#d6b656"), "core": ("#d5e8d4", "#82b366"),
    "agent": ("#e1d5e7", "#9673a6"), "model": ("#f8cecc", "#b85450"), "data": ("#f5f5f5", "#666666"),
    "obs": ("#ffe6cc", "#d79b00"), "ext": ("#ffffff", "#000000"), "sec": ("#fad9d5", "#ae4132"),
}


class Diagram:
    def __init__(self, name, width=1600, height=1000):
        self.name, self.w, self.h, self.cells, self.n = name, width, height, [], 0
        self.geo = {}

    def _id(self):
        self.n += 1
        return f"c{self.n}"

    def _add(self, cid, value, style, geo, vertex=True, parent="1", extra="", box=None):
        if box:
            self.geo[cid] = box
        kind = 'vertex="1"' if vertex else 'edge="1"'
        self.cells.append(f'<mxCell id="{cid}" value={quoteattr(value)} style="{style}" {kind} parent="{parent}" {extra}>{geo}</mxCell>')
        return cid

    def box(self, label, x, y, w=160, h=60, zone="core", shape="rounded=1", extra_style="", parent="1"):
        fill, stroke = C[zone]
        style = f"{shape};whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontSize=12;{extra_style}"
        return self._add(self._id(), label, style, f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>', parent=parent, box=(x, y, w, h))

    def zone(self, label, x, y, w, h, zone="data"):
        fill, stroke = C[zone]
        style = (f"rounded=0;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};dashed=1;"
                 "verticalAlign=top;align=left;spacingLeft=8;fontStyle=1;fontSize=13;opacity=60;")
        return self._add(self._id(), label, style, f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>', box=(x, y, w, h))

    def db(self, label, x, y, w=120, h=70, zone="data"):
        return self.box(label, x, y, w, h, zone, shape="shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=12")

    def actor(self, label, x, y):
        return self._add(self._id(), label, "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;",
                         f'<mxGeometry x="{x}" y="{y}" width="30" height="60" as="geometry"/>', box=(x, y, 30, 60))

    def note(self, label, x, y, w=220, h=60):
        return self.box(label, x, y, w, h, "obs", shape="shape=note;size=12", extra_style="align=left;spacingLeft=6;fontSize=11;")

    def text(self, label, x, y, w=300, h=30, size=12, bold=False):
        style = f"text;html=1;align=left;verticalAlign=middle;fontSize={size};" + ("fontStyle=1;" if bold else "")
        return self._add(self._id(), label, style, f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>')

    def emph(self, cid, color="#E8590C", width=3):
        """Highlight an existing shape: thicker border in the highlight colour."""
        for i, cell in enumerate(self.cells):
            if cell.startswith(f'<mxCell id="{cid}" '):
                head, rest = cell.split('style="', 1)
                style, tail = rest.split('"', 1)
                self.cells[i] = f'{head}style="{style}strokeColor={color};strokeWidth={width};"{tail}'
                return cid
        raise KeyError(cid)

    def badge(self, cid, n, color="#E8590C"):
        """Numbered circle on the top-left corner of a shape (design highlight)."""
        x, y, _, _ = self.geo[cid]
        style = (f"ellipse;whiteSpace=wrap;html=1;fillColor={color};strokeColor={color};fontColor=#ffffff;"
                 "fontStyle=1;fontSize=13;")
        return self._add(self._id(), str(n), style, f'<mxGeometry x="{x - 13}" y="{y - 13}" width="26" height="26" as="geometry"/>')

    def link(self, src, tgt, label="", dashed=False, color="#333333", both=False, exit=None, entry=None, points=None, width=1):
        """Orthogonal edge. Ports are chosen from the relative position of the two shapes unless given.
        exit/entry = (x, y) relative (0..1); points = list of absolute waypoints."""
        if (exit is None or entry is None) and src in self.geo and tgt in self.geo:
            sx, sy, sw, sh = self.geo[src]; tx, ty, tw, th = self.geo[tgt]
            dx = (tx + tw / 2) - (sx + sw / 2); dy = (ty + th / 2) - (sy + sh / 2)
            if abs(dx) >= abs(dy):
                auto_exit, auto_entry = ((1, .5), (0, .5)) if dx > 0 else ((0, .5), (1, .5))
            else:
                auto_exit, auto_entry = ((.5, 1), (.5, 0)) if dy > 0 else ((.5, 0), (.5, 1))
            exit = exit or auto_exit; entry = entry or auto_entry
        style = (f"edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;strokeColor={color};fontSize=10;"
                 "labelBackgroundColor=#ffffff;" + ("dashed=1;" if dashed else "") + ("startArrow=block;" if both else "")
                 + (f"strokeWidth={width};" if width != 1 else ""))
        if exit:
            style += f"exitX={exit[0]};exitY={exit[1]};exitDx=0;exitDy=0;"
        if entry:
            style += f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;"
        pts = ""
        if points:
            pts = '<Array as="points">' + "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in points) + "</Array>"
        return self._add(self._id(), label, style, f'<mxGeometry relative="1" as="geometry">{pts}</mxGeometry>', vertex=False,
                         extra=f'source="{src}" target="{tgt}"')

    def xml(self):
        body = "".join(self.cells)
        return (f'<mxfile host="drawio"><diagram name={quoteattr(self.name)} id="d1">'
                f'<mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" '
                f'fold="1" page="1" pageScale="1" pageWidth="{self.w}" pageHeight="{self.h}" math="0" shadow="0">'
                f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>{body}</root></mxGraphModel></diagram></mxfile>')

    def save(self, path):
        open(path, "w", encoding="utf-8").write(self.xml())


class Sequence(Diagram):
    """Sequence diagram: participants with lifelines; messages are free edges at explicit y positions."""

    def __init__(self, name, participants, gap=190, top=60, pw=150):
        super().__init__(name)
        self.gap, self.top, self.pw, self.y = gap, top, pw, top + 80
        self.parts = {}
        for i, (key, label, zone) in enumerate(participants):
            self.parts[key] = (40 + i * gap, label, zone)
        self.w = 80 + len(participants) * gap

    def cx(self, key):
        return self.parts[key][0] + self.pw / 2

    def msg(self, a, b, label, ret=False, step=42):
        self.y += step
        x1, x2 = self.cx(a), self.cx(b)
        style = ("html=1;verticalAlign=bottom;fontSize=10;labelBackgroundColor=#ffffff;endArrow=" +
                 ("open;dashed=1;" if ret else "block;"))
        if a == b:  # self message: small loop
            geo = (f'<mxGeometry relative="1" as="geometry"><mxPoint x="{x1}" y="{self.y}" as="sourcePoint"/>'
                   f'<mxPoint x="{x1}" y="{self.y + 18}" as="targetPoint"/><Array as="points">'
                   f'<mxPoint x="{x1 + 40}" y="{self.y}"/><mxPoint x="{x1 + 40}" y="{self.y + 18}"/></Array></mxGeometry>')
            self.y += 10
            style = "html=1;align=left;spacingLeft=44;fontSize=10;endArrow=block;"
        else:
            geo = (f'<mxGeometry relative="1" as="geometry"><mxPoint x="{x1}" y="{self.y}" as="sourcePoint"/>'
                   f'<mxPoint x="{x2}" y="{self.y}" as="targetPoint"/></mxGeometry>')
        self._add(self._id(), label, style, geo, vertex=False)

    def note_over(self, a, b, label, h=36, zone="obs"):
        self.y += 14
        x1 = min(self.parts[a][0], self.parts[b][0])
        x2 = max(self.parts[a][0], self.parts[b][0]) + self.pw
        self.box(label, x1, self.y, x2 - x1, h, zone, shape="rounded=0", extra_style="fontSize=10;align=center;")
        self.y += h

    def frame(self, label, a, b, start_y, end_y):
        x1 = min(self.parts[a][0], self.parts[b][0]) - 10
        x2 = max(self.parts[a][0], self.parts[b][0]) + self.pw + 10
        style = ("shape=umlFrame;whiteSpace=wrap;html=1;width=110;height=22;fontSize=10;fillColor=none;"
                 "strokeColor=#888888;dashed=1;")
        self._add(self._id(), label, style, f'<mxGeometry x="{x1}" y="{start_y}" width="{x2 - x1}" height="{end_y - start_y}" as="geometry"/>')

    def finish(self):
        height = self.y + 60
        for key, (x, label, zone) in self.parts.items():
            fill, stroke = C[zone]
            style = (f"shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=0;collapsible=0;"
                     f"recursiveResize=0;outlineConnect=0;size=50;fillColor={fill};strokeColor={stroke};fontSize=11;")
            self.cells.insert(0, f'<mxCell id="ll_{key}" value={quoteattr(label)} style="{style}" vertex="1" parent="1">'
                                 f'<mxGeometry x="{x}" y="{self.top}" width="{self.pw}" height="{height - self.top}" as="geometry"/></mxCell>')
        self.h = height + 40
