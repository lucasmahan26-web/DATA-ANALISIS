"""
Verifica que todos los enlaces internos del workspace resuelvan a un archivo
o directorio existente, y que ningun archivo PUBLICO enlace a uno PRIVADO.

Un enlace roto en un portafolio se lee como falta de atencion al detalle —
exactamente lo contrario de lo que busca un analista. Este script convierte
esa afirmacion en algo comprobable.

Que revisa:
  1. Enlaces markdown  [texto](ruta/relativa.md)  -> el destino debe existir
  2. Si hay repositorio git: que un archivo versionado (publico) no enlace a
     un archivo ignorado (privado). En GitHub ese enlace daria 404.

Se saltean los enlaces http(s), mailto y los anclas puras (#seccion).

Ejecutar:  <python> scripts/verificar_enlaces.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# [texto](destino)  — el destino no puede contener parentesis sin escapar,
# lo cual es suficiente para este workspace.
PATRON = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")

IGNORAR = {"http://", "https://", "mailto:", "tel:"}


def archivos_publicos() -> set[Path] | None:
    """Lista de archivos versionados segun git. None si no hay repo o falla."""
    try:
        salida = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return None
    if salida.returncode != 0:
        return None
    lineas = [l.strip() for l in salida.stdout.splitlines() if l.strip()]
    if not lineas:
        return None
    return {(ROOT / l).resolve() for l in lineas}


def main() -> int:
    publicos = archivos_publicos()
    archivos = sorted(ROOT.rglob("*.md"))
    revisados = 0
    roto: list[tuple[Path, int, str]] = []
    fuga: list[tuple[Path, int, str]] = []

    for archivo in archivos:
        if ".git" in archivo.parts:
            continue
        for n, linea in enumerate(
            archivo.read_text(encoding="utf-8").splitlines(), start=1
        ):
            for destino in PATRON.findall(linea):
                if destino.startswith(tuple(IGNORAR)) or destino.startswith("#"):
                    continue
                # Quitar ancla final: archivo.md#seccion -> archivo.md
                ruta_txt = destino.split("#", 1)[0]
                if not ruta_txt:
                    continue
                revisados += 1
                objetivo = (archivo.parent / ruta_txt).resolve()
                try:
                    objetivo.relative_to(ROOT)
                except ValueError:
                    roto.append((archivo, n, destino))  # fuera del workspace
                    continue
                if not objetivo.exists():
                    roto.append((archivo, n, destino))
                    continue

                # Chequeo 2: un archivo publico no puede enlazar a uno privado.
                if publicos is not None and archivo.resolve() in publicos:
                    candidatos = [objetivo]
                    if objetivo.is_dir():
                        candidatos = [p for p in objetivo.rglob("*") if p.is_file()]
                    if candidatos and not any(c in publicos for c in candidatos):
                        fuga.append((archivo, n, destino))

    print(f"[i] Archivos .md analizados   : {len(archivos)}")
    print(f"[i] Enlaces internos revisados: {revisados}")
    print(f"[i] Archivos versionados (git): "
          f"{len(publicos) if publicos is not None else 'sin repositorio'}")

    codigo = 0
    if roto:
        print(f"\n[!] Enlaces rotos: {len(roto)}")
        for archivo, n, destino in roto:
            print(f"    {archivo.relative_to(ROOT)}:{n}  ->  {destino}")
        codigo = 1

    if fuga:
        print(f"\n[!] Archivos PUBLICOS que enlazan a archivos NO publicados: {len(fuga)}")
        print("    (en GitHub darian error 404)")
        for archivo, n, destino in fuga:
            print(f"    {archivo.relative_to(ROOT)}:{n}  ->  {destino}")
        codigo = 1

    if codigo == 0:
        extra = (" y ningun archivo publico enlaza a uno no publicado" if publicos else "")
        print(f"\n[OK] Los {revisados} enlaces internos resuelven correctamente{extra}.")
    return codigo


if __name__ == "__main__":
    sys.exit(main())

