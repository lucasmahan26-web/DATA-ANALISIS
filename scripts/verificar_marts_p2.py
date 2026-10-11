"""
Verifica la especificacion de la capa marts del Proyecto 2.

Que valida:
  1. Que la spec mencione todas las tablas del DDL que necesita.
  2. Que las referencias a columnas de ORIGEN existan realmente en el DDL
     (si no, manda al alumno a buscar una columna que no existe).
  3. Que las 10 preguntas de negocio del README esten cubiertas por algun mart.
  4. Que los tipos declarados sean tipos validos de PostgreSQL.

Criterio para no llenar de falsos positivos (leccion aprendida a golpes):
  - Se revisa SOLO el contenido entre backticks de la columna "Definicion de
    negocio". Es donde esta el codigo. La prosa en espanol de las otras celdas
    NO se escanea: hacerlo genera cientos de falsos positivos y vuelve inutil
    el verificador.
  - Dentro de los backticks se descartan los literales entre comillas y las
    palabras reservadas de SQL.

Ejecutar:  <python> scripts/verificar_marts_p2.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DDL = ROOT / "scripts" / "P2_01_crear_tablas.sql"
MART = ROOT / "proyectos" / "02_sql" / "01_marts.md"
README_P2 = ROOT / "proyectos" / "02_sql" / "README.md"

TIPOS_VALIDOS = {"int", "integer", "text", "numeric", "date", "bool", "boolean",
                 "timestamp", "varchar", "bigint"}

RESERVADAS = {
    "sum", "avg", "min", "max", "count", "rank", "row_number", "dense_rank",
    "nullif", "coalesce", "round", "case", "when", "then", "else", "end",
    "partition", "by", "order", "over", "rows", "between", "unbounded",
    "preceding", "current", "row", "lag", "lead", "case", "cast", "extract",
    "year", "month", "day", "date_trunc", "to_char", "and", "or", "not", "in",
    "is", "as", "desc", "asc", "distinct", "select", "from", "where",
}


def columnas_del_ddl() -> dict[str, set[str]]:
    """{tabla: {columnas}} a partir del DDL real."""
    texto = DDL.read_text(encoding="utf-8")
    tablas: dict[str, set[str]] = {}
    for m in re.finditer(r"CREATE TABLE (\w+)\s*\((.*?)\n\);", texto, re.S):
        nombre, cuerpo = m.group(1), m.group(2)
        cols = set()
        for linea in cuerpo.splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("--"):
                continue
            partes = linea.split()
            if len(partes) >= 2 and re.fullmatch(r"[a-z_][a-z0-9_]*", partes[0]):
                cols.add(partes[0])
        tablas[nombre] = cols
    return tablas


def filas_de_la_spec() -> list[tuple[str, str, str]]:
    """[(nombre_columna, tipo, definicion)] de las tablas de la especificacion."""
    filas = []
    for linea in MART.read_text(encoding="utf-8").splitlines():
        s = linea.strip()
        if not s.startswith("|"):
            continue
        celdas = [c.strip() for c in s.split("|")]
        # | `` | ... -> celdas[0]='' celdas[1]=nombre celdas[2]=tipo celdas[3]=def
        if len(celdas) < 5:
            continue
        m = re.fullmatch(r"`([a-z_][a-z0-9_]*)`", celdas[1])
        if not m:
            continue
        filas.append((m.group(1), celdas[2], celdas[3]))
    return filas


def identificadores_en_backticks(texto: str) -> set[str]:
    """Identificadores citados como codigo, sin literales ni palabras reservadas."""
    ids: set[str] = set()
    for bloque in re.findall(r"`([^`]+)`", texto):
        # Quitar literales de texto: 'S', 'N', '2024-03'
        bloque = re.sub(r"'[^']*'", " ", bloque)
        for palabra in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", bloque):
            p = palabra.lower()
            if p in RESERVADAS or len(p) < 3:
                continue
            ids.add(p)
    return ids


def main() -> int:
    for ruta in (DDL, MART, README_P2):
        if not ruta.exists():
            sys.exit(f"[!] Falta {ruta}")

    ddl = columnas_del_ddl()
    todas_ddl = set().union(*ddl.values()) if ddl else set()
    filas = filas_de_la_spec()
    texto_mart = MART.read_text(encoding="utf-8")
    definidas = {f[0] for f in filas}

    print(f"[i] Tablas en el DDL        : {len(ddl)}")
    print(f"[i] Columnas en el DDL      : {len(todas_ddl)}")
    print(f"[i] Columnas definidas spec : {len(definidas)}")

    fallos: list[str] = []

    # ------------------------------------------------ 1. tablas del DDL usadas
    print("\n[1] Tablas del DDL mencionadas por la especificacion")
    usadas = sorted(t for t in ddl if re.search(rf"\b{t}\b", texto_mart))
    print(f"    {', '.join(usadas)}")
    faltantes = sorted(set(ddl) - set(usadas))
    if faltantes:
        print(f"    NO mencionadas: {', '.join(faltantes)}")
        if len(faltantes) > 2:
            fallos.append(f"la spec ignora {len(faltantes)} tablas del DDL")

    # ------------------------------------------- 2. tipos declarados validos
    print("\n[2] Tipos declarados")
    tipos = {f[1] for f in filas if f[1]}
    invalidos = sorted(t for t in tipos if t.lower() not in TIPOS_VALIDOS)
    print(f"    {', '.join(sorted(tipos))}")
    if invalidos:
        fallos.append(f"tipos invalidos para PostgreSQL: {invalidos}")
        print(f"    INVALIDOS: {invalidos}")
    else:
        print("    todos son tipos validos de PostgreSQL")

    # -------------------------------- 3. columnas de origen citadas existen
    print("\n[3] Referencias a columnas dentro de las definiciones de negocio")
    desconocidas: dict[str, list[str]] = {}
    for nombre, _tipo, definicion in filas:
        for ident in identificadores_en_backticks(definicion):
            if ident in todas_ddl or ident in definidas or ident in ddl:
                continue
            desconocidas.setdefault(ident, []).append(nombre)
    if desconocidas:
        for ident, donde in sorted(desconocidas.items()):
            print(f"    '{ident}' no existe en el DDL (citada en: {', '.join(donde)})")
        fallos.append(f"{len(desconocidas)} identificadores sin resolver")
    else:
        print("    todas resuelven contra el DDL o contra columnas del propio mart")

    # ------------------------------------------- 4. cobertura de las preguntas
    print("\n[4] Cobertura de las 10 preguntas del README")
    readme = README_P2.read_text(encoding="utf-8")
    en_readme = sorted({int(m.group(1)) for m in
                        re.finditer(r"^\|\s*(\d{1,2})\s*\|", readme, re.M)
                        if 1 <= int(m.group(1)) <= 10})
    bloque = texto_mart.split("## Cobertura", 1)
    cubiertas: set[int] = set()
    if len(bloque) == 2:
        cubiertas = {int(m.group(1)) for m in
                     re.finditer(r"^\|\s*(\d{1,2})\s*\|", bloque[1], re.M)}
    print(f"    En el README  : {en_readme}")
    print(f"    En la spec    : {sorted(cubiertas)}")
    faltan = [n for n in range(1, 11) if n not in cubiertas]
    if faltan:
        fallos.append(f"la spec no cubre las preguntas {faltan}")
        print(f"    FALTAN: {faltan}")
    else:
        print("    las 10 estan cubiertas")

    # ---------------------------------------- 5. nombres de marts coherentes
    print("\n[5] Nombres de marts: cuerpo vs tabla de cobertura")
    en_cuerpo = set(re.findall(r"`(mart_\w+)`", texto_mart))
    en_cob = set(re.findall(r"`(mart_\w+)`", bloque[1])) if len(bloque) == 2 else set()
    print(f"    Definidos: {', '.join(sorted(en_cuerpo))}")
    huerfanos = en_cob - en_cuerpo
    if huerfanos:
        fallos.append(f"la cobertura cita marts inexistentes: {sorted(huerfanos)}")
        print(f"    COBERTURA CITA SIN DEFINIR: {sorted(huerfanos)}")
    sin_pregunta = sorted(en_cuerpo - en_cob)
    if sin_pregunta:
        print(f"    Definidos sin pregunta asignada (puede ser intencional): {sin_pregunta}")

    if fallos:
        print(f"\n[!] PROBLEMAS: {fallos}", file=sys.stderr)
        return 1
    print("\n[OK] La especificacion es consistente: tablas y columnas resuelven "
          "contra el DDL, tipos validos y las 10 preguntas cubiertas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
