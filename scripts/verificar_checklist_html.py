"""
Verifica CHECKLIST.html: que el JavaScript no tenga errores de sintaxis y que
los datos del checklist sean coherentes.

Por que existe:
  Un archivo HTML que "se ve bien" en el editor puede tener un error de sintaxis
  en el script y quedar completamente en blanco al abrirlo. Sin abrir un
  navegador, la unica forma de comprobarlo es pasar el codigo por un parser real.

Que valida:
  1. El JavaScript extraido del <script> pasa `node --check` (parser de verdad).
  2. El array BLOQUES es JSON valido y tiene la estructura esperada.
  3. Las etiquetas HTML principales estan balanceadas.
  4. Que no haya recursos externos (tiene que funcionar con doble clic, offline).

Ejecutar:  <python> scripts/verificar_checklist_html.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "CHECKLIST.html"
NODE = Path("C:/Users/lucas/.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/"
            "node/bin/node.exe")

ESPERADO = {
    "bloques": 6,
    "tareas_por_bloque": [8, 6, 6, 6, 6, 5],
}


def extraer_script(texto: str) -> str:
    m = re.search(r"<script>(.*?)</script>", texto, re.S)
    if not m:
        sys.exit("[!] No encuentro el bloque <script>")
    return m.group(1)


def extraer_bloques(script: str) -> list:
    """Extrae el literal de BLOQUES y lo convierte a objetos de Python."""
    ini = script.index("const BLOQUES = [")
    ini = script.index("[", ini)
    # Recorrer contando corchetes y respetando strings
    prof = 0
    i = ini
    en_str = None
    while i < len(script):
        c = script[i]
        if en_str:
            if c == "\\":
                i += 2
                continue
            if c == en_str:
                en_str = None
        elif c in "\"'`":
            en_str = c
        elif c == "[":
            prof += 1
        elif c == "]":
            prof -= 1
            if prof == 0:
                break
        i += 1
    literal = script[ini:i + 1]
    # El literal usa comillas dobles y templates; para leerlo se evalua con node
    return literal


def main() -> int:
    if not HTML.exists():
        sys.exit(f"[!] No existe {HTML}")
    if not NODE.exists():
        sys.exit(f"[!] No encuentro node en {NODE}")

    texto = HTML.read_text(encoding="utf-8")
    script = extraer_script(texto)
    print(f"[i] Archivo      : {HTML.name} ({len(texto) / 1024:.1f} KB)")
    print(f"[i] Script extraido: {len(script)} caracteres")

    fallos: list[str] = []

    # -------------------------------------------- 1. syntax check con node
    print("\n[1] Sintaxis del JavaScript (node --check)")
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(script)
        tmp = fh.name
    r = subprocess.run([str(NODE), "--check", tmp], capture_output=True, text=True)
    if r.returncode == 0:
        print("    OK: el parser de Node no encontro errores")
    else:
        print("    ERROR DE SINTAXIS:")
        for l in (r.stderr or "").splitlines()[:8]:
            print(f"      {l}")
        fallos.append("error de sintaxis en el JavaScript")
    Path(tmp).unlink(missing_ok=True)

    # ------------------------------------------------ 2. datos del checklist
    print("\n[2] Estructura de los datos (BLOQUES)")
    literal = extraer_bloques(script)
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(f"const B = {literal};\nconsole.log(JSON.stringify(B));\n")
        tmp2 = fh.name
    r2 = subprocess.run([str(NODE), tmp2], capture_output=True, text=True)
    Path(tmp2).unlink(missing_ok=True)
    if r2.returncode != 0:
        print("    ERROR al evaluar BLOQUES:")
        for l in (r2.stderr or "").splitlines()[:6]:
            print(f"      {l}")
        fallos.append("BLOQUES no se puede evaluar")
        bloques = []
    else:
        bloques = json.loads(r2.stdout)
        n = len(bloques)
        print(f"    Bloques: {n}")
        for b in bloques:
            print(f"      {b['n']}. {b['t'][:46]:<48} {len(b['tareas'])} tareas")
        if n != ESPERADO["bloques"]:
            fallos.append(f"hay {n} bloques, se esperaban {ESPERADO['bloques']}")
        conteos = [len(b["tareas"]) for b in bloques]
        if conteos != ESPERADO["tareas_por_bloque"]:
            fallos.append(f"tareas por bloque {conteos} != {ESPERADO['tareas_por_bloque']}")
        for b in bloques:
            for campo in ("n", "t", "tiempo", "cierre", "porque", "tareas"):
                if campo not in b or b[campo] in ("", None):
                    fallos.append(f"bloque {b.get('n')}: falta '{campo}'")

    # ------------------------------------------------------ 3. HTML basico
    print("\n[3] Estructura del HTML")
    # OJO: contar "<head" a secas tambien matchea "<header>". Hay que exigir
    # que despues del nombre venga un espacio o ">".
    conteos_html = {}
    for t in ("html", "head", "body", "style", "script", "div", "ul", "li"):
        abre = len(re.findall(rf"<{t}[\s>]", texto))
        cierra = texto.count(f"</{t}>")
        conteos_html[t] = (abre, cierra)
    for etiqueta, (a, b) in conteos_html.items():
        bal = "OK" if a == b else f"DESBALANCEADO ({a} abre, {b} cierra)"
        if a != b:
            fallos.append(f"<{etiqueta}> desbalanceado")
        print(f"    <{etiqueta:<7}{a:>3} abre / {b:>3} cierra   {bal}")

    # ------------------------------------------- 4. sin recursos externos
    print("\n[4] Autonomia (tiene que funcionar offline con doble clic)")
    externos = re.findall(r'(?:src|href)\s*=\s*["\'](https?://[^"\']+)', texto)
    if externos:
        print(f"    PROBLEMA: {len(externos)} recursos externos: {externos[:3]}")
        fallos.append("depende de recursos externos")
    else:
        print("    OK: sin recursos externos, todo inline")

    # -------------------------------------------------- 5. persistencia
    print("\n[5] Persistencia del progreso")
    if "localStorage" in script:
        print("    OK: usa localStorage (el progreso sobrevive al cerrar)")
    else:
        print("    PROBLEMA: no guarda el progreso")
        fallos.append("no persiste el progreso")

    if fallos:
        print(f"\n[!] PROBLEMAS: {fallos}", file=sys.stderr)
        return 1
    print("\n[OK] CHECKLIST.html: JavaScript valido, 6 bloques, HTML balanceado, "
          "sin dependencias externas y con progreso persistente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
