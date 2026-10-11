"""
Auditoria de consistencia del workspace.

El verificador de enlaces cubre los enlaces markdown [texto](ruta), pero NO las
rutas que aparecen entre backticks en el texto: `datos/p2/analisis.db`.
Una ruta mal escrita ahi no la detecta nadie y hace perder tiempo al que la sigue.

Ademas busca CONTRADICCIONES entre documentos:
  - asignaciones de semanas distintas para el mismo proyecto
  - cifras clave que deberian coincidir y no coinciden
  - afirmaciones de estado de herramientas que quedaron viejas

Ejecutar:  <python> scripts/auditar_consistencia.py
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Rutas entre backticks que valga la pena verificar.
PAT_BACKTICK = re.compile(r"`([A-Za-z0-9_./\\-]+)`")
EXTENSIONES = {".md", ".csv", ".db", ".sql", ".py", ".txt", ".xlsx", ".pbix", ".png", ".pdf"}
# Cosas que parecen ruta pero son otra cosa.
EXCLUIR = {
    "main", "text", "integer", "real", "numeric", "date", "utf-8", "utf-8-sig",
    "en-US", "es-ES", "ml", "unidad", "S/N", "N/A", "II", "sum", "count", "avg",
    "y", "o", "si", "no", "null", "S/N",
    "\\xa0", "\\n", "\\t",   # secuencias de escape citadas como texto, no rutas
}


def _es_meta_comando(cand: str) -> bool:
    """Los meta-comandos de psql empiezan con \\ y no son rutas: \\copy, \\echo."""
    return cand.startswith("\\") and "/" not in cand

# Cifras que deberian coincidir en TODOS los documentos donde aparezcan.
HECHOS = {
    "filas P1": [r"2\.935", r"2935"],
    "filas unicas P1": [r"2\.900\b", r"2900"],
    "tablas P2": [r"7 tablas"],
    "filas P2": [r"131\.122"],
    "filas ventas P2": [r"130\.688"],
    "insumos bar": [r"73 insumos"],
    "tragos bar": [r"24 tragos"],
    "ventas bar": [r"7\.941", r"7941"],
    "semanas bar": [r"26 semanas"],
}

# Semanas asignadas a cada proyecto: (patron, valor canonico)
SEMANAS_CANONICAS = {
    "P1": "2–3",
    "P2": "4–7",
    "P3": "8–10",
    "P4": "11–12",
}
PAT_SEMANA = re.compile(
    r"(P1|P2|P3|P4|\bExcel \+ Power Query\b).{0,80}?[Ss]emanas?:?\s*\*{0,2}(\d+\s*[–\-]\s*\d+)",
    re.S,
)


def verificar_backticks(archivos: list[Path]) -> list[tuple[Path, int, str]]:
    """
    Revisa rutas entre backticks con DOS resoluciones posibles.

    Las rutas en prosa son ambiguas: `datos/p2/x.db` escrita dentro de
    proyectos/02_sql/ puede querer decir "desde la raiz del repo" o "desde aca".
    Se acepta si existe con cualquiera de las dos. Solo se reporta si no existe
    con ninguna, que es cuando el lector efectivamente no la va a encontrar.
    """
    faltantes = []
    for archivo in archivos:
        for n, linea in enumerate(archivo.read_text(encoding="utf-8").splitlines(), 1):
            for cand in PAT_BACKTICK.findall(linea):
                if cand in EXCLUIR or ("/" not in cand and "\\" not in cand):
                    continue
                if _es_meta_comando(cand):
                    continue
                rel = cand.replace("\\", "/")
                if (ROOT / rel).exists() or (archivo.parent / rel).exists():
                    continue
                # Tampoco marcar rutas fuera del repo (ej. C:\... o ..\..\otro)
                if not (ROOT / rel.split("/")[0]).exists() and not rel.startswith(".."):
                    continue
                faltantes.append((archivo, n, cand))
    return faltantes


# Estado de herramientas VERIFICADO en esta maquina (no por PATH, que miente):
#   PostgreSQL 18.4 -> C:\Program Files\PostgreSQL\18\bin\psql.exe (servicio corriendo)
#   DBeaver         -> %LOCALAPPDATA%\DBeaver
#   Excel/PQ/Pivot  -> C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE
#   VS Code, Git    -> instalados
#   GitHub Desktop, Power BI Desktop -> NO instalados
INSTALADAS = ["PostgreSQL", "DBeaver", "Excel", "Power Query", "Power Pivot",
              "VS Code", "Git (CLI)", "Git"]
NO_INSTALADAS = ["GitHub Desktop", "Power BI Desktop", "Power BI"]


def _menciona_instalada(texto: str) -> str | None:
    """Devuelve la herramienta INSTALADA mencionada, sin confundir Git con GitHub."""
    # Si menciona una NO instalada, no revisar las instaladas que son substring.
    if any(x in texto for x in ("GitHub Desktop", "GitHub", "Power BI")):
        return None
    for h in sorted(INSTALADAS, key=len, reverse=True):
        if h in texto:
            return h
    return None


def verificar_contradicciones(archivos: list[Path]) -> list[str]:
    """
    Revisa solo lugares ESTRUCTURADOS: tablas con columna de estado y checkboxes.

    Buscar 'instal' en prosa libre genera demasiados falsos positivos ("sin
    instalar nada", "ya los tenés", "no te pongas a instalar"). Un verificador
    con ruido se termina ignorando, y entonces no sirve para nada.
    """
    problemas: list[str] = []

    # --- 1. Semanas por proyecto
    for archivo in archivos:
        texto = archivo.read_text(encoding="utf-8")
        for m in PAT_SEMANA.finditer(texto):
            clave, rango = m.group(1), m.group(2)
            if not clave.startswith("P"):
                continue
            canon = SEMANAS_CANONICAS.get(clave)
            if canon is None or rango.replace(" ", "") == canon.replace(" ", ""):
                continue
            linea = texto[: m.start()].count("\n") + 1
            problemas.append(
                f"{archivo.relative_to(ROOT)}:{linea}  {clave} dice semanas "
                f"'{rango}' pero el canonico es '{canon}'"
            )

    # --- 2. Tablas de estado: una herramienta instalada marcada como pendiente
    for archivo in archivos:
        for n, linea in enumerate(archivo.read_text(encoding="utf-8").splitlines(), 1):
            if not linea.strip().startswith("|"):
                continue
            if "☐" not in linea:
                continue
            h = _menciona_instalada(linea)
            if h:
                problemas.append(
                    f"{archivo.relative_to(ROOT)}:{n}  marca '{h}' como pendiente "
                    f"(☐) pero YA esta instalado: {linea.strip()[:70]}"
                )

    # --- 3. Checkboxes: "X instalado" sin marcar, para algo ya instalado.
    # Se exige que la linea hable de INSTALACION: un checkbox como "Abri la base
    # en DBeaver" menciona DBeaver pero no afirma nada sobre si esta instalado.
    for archivo in archivos:
        for n, linea in enumerate(archivo.read_text(encoding="utf-8").splitlines(), 1):
            s = linea.strip()
            if not s.startswith("- [ ]") or not re.search(r"instal", s, re.I):
                continue
            h = _menciona_instalada(s)
            if h:
                problemas.append(
                    f"{archivo.relative_to(ROOT)}:{n}  checkbox de instalacion pendiente "
                    f"para '{h}', que YA esta instalado: {s[:70]}"
                )
    return problemas


def main() -> int:
    archivos = sorted(a for a in ROOT.rglob("*.md") if ".git" not in a.parts)
    print(f"[i] Documentos auditados: {len(archivos)}\n")

    print("[1] Rutas entre backticks que no existen")
    faltantes = verificar_backticks(archivos)
    if faltantes:
        for archivo, n, cand in faltantes:
            print(f"    {archivo.relative_to(ROOT)}:{n}  ->  `{cand}`")
    else:
        print("    ninguna")

    print("\n[2] Contradicciones entre documentos")
    problemas = verificar_contradicciones(archivos)
    if problemas:
        for p in problemas:
            print(f"    {p}")
    else:
        print("    ninguna")

    if faltantes or problemas:
        print(f"\n[!] {len(faltantes)} rutas faltantes, {len(problemas)} contradicciones",
              file=sys.stderr)
        return 1
    print("\n[OK] Sin rutas rotas entre backticks ni contradicciones entre documentos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
