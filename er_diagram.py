"""ER diagramma generatori: SQLAlchemy metadata'dan Graphviz (.dot) va .png hosil qiladi.

Ishga tushirish:  python -m app.er_diagram     (PNG uchun Graphviz `dot` dasturi kerak)
"""
from __future__ import annotations

import shutil
import subprocess
from html import escape
from pathlib import Path

from sqlalchemy import MetaData

from app.config import BASE_DIR
from app.models import Base

HEADER_FILL = "#C6E0B4"  # och yashil
ROW_FILL = "#FFFFFF"
LINK_FILL = "#FCE4D6"  # och shaftoli (oraliq jadval)


def metadata_to_dot(metadata: MetaData, junction_tables: set[str] | None = None) -> str:
    junction_tables = junction_tables or set()
    lines = [
        "digraph ER {",
        '  graph [rankdir=LR, splines=true, nodesep=0.5, ranksep=1.3, pad=0.3, bgcolor="white"];',
        '  node [shape=plain, fontname="DejaVu Sans", fontsize=11];',
        '  edge [fontname="DejaVu Sans", fontsize=10, color="#222222", dir=both,'
        " arrowtail=tee, arrowhead=crow, labeldistance=2.2, labelangle=25];",
    ]
    for table in metadata.sorted_tables:
        fk_cols = {c.name for c in table.columns if c.foreign_keys}
        fill = LINK_FILL if table.name in junction_tables else HEADER_FILL
        rows = [
            f'<TR><TD COLSPAN="2" BGCOLOR="{fill}"><B>{escape(table.name)}</B></TD></TR>'
        ]
        for col in table.columns:
            flags = []
            if col.primary_key:
                flags.append("PK")
            if col.name in fk_cols:
                flags.append("FK")
            if col.unique:
                flags.append("UQ")
            flag_txt = ",".join(flags)
            rows.append(
                f'<TR><TD ALIGN="LEFT" BGCOLOR="{ROW_FILL}">{escape(col.name)}</TD>'
                f'<TD ALIGN="LEFT" BGCOLOR="{ROW_FILL}">{escape(str(col.type))}'
                f"{(' ' + flag_txt) if flag_txt else ''}</TD></TR>"
            )
        label = '<<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">' + "".join(rows) + "</TABLE>>"
        lines.append(f'  "{table.name}" [label={label}];')
    for table in metadata.sorted_tables:
        for fk in table.foreign_key_constraints:
            parent = fk.referred_table.name
            col = list(fk.columns)[0].name
            lines.append(
                f'  "{parent}" -> "{table.name}" [taillabel="1", headlabel="N", label="{col}"];'
            )
    lines.append("}")
    return "\n".join(lines) + "\n"


def render(metadata: MetaData, name: str, junction_tables: set[str] | None = None) -> Path:
    docs = Path(BASE_DIR) / "docs"
    docs.mkdir(exist_ok=True)
    dot_path = docs / f"{name}.dot"
    dot_path.write_text(metadata_to_dot(metadata, junction_tables), encoding="utf-8")
    png_path = docs / f"{name}.png"
    if shutil.which("dot"):
        subprocess.run(["dot", "-Tpng", "-Gdpi=130", str(dot_path), "-o", str(png_path)], check=True)
    return png_path


def main() -> None:
    p1 = render(Base.metadata, "er_diagram")
    print(f"Yaratildi: {p1.name} (docs/ papkasida)")


if __name__ == "__main__":
    main()
