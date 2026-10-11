"""
Verifica que los enlaces EXTERNOS del workspace sigan vivos.

Por que existe:
  El roadmap recomienda unas 30 fuentes gratuitas (cursos, documentacion,
  datasets). Nunca se comprobo que existan. Un enlace muerto en la lista de
  recursos hace perder tiempo justo cuando la persona esta arrancando, que es
  el peor momento posible.

Criterio de clasificacion (para no llenar de falsos positivos):
  - 200, 301, 302  -> OK
  - 403, 429, 401  -> el sitio bloquea peticiones automatizadas. NO es un enlace
                      muerto: se marca como "revisar a mano", no como falla.
  - 5xx            -> error del SERVIDOR, normalmente transitorio. "revisar".
  - error de SSL   -> problema de certificados de Python en Windows, no del sitio.
                      Se comprobo con otra herramienta que datos.gob.es responde 200.
                      Clasificarlo como "muerto" seria un falso positivo.
  - 404, 410       -> MUERTO. Es un hallazgo real.
  - error de DNS   -> MUERTO (el dominio no resuelve).

Ejecutar:  <python> scripts/verificar_recursos.py [--solo-fallos]
"""

from __future__ import annotations

import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
TIMEOUT = 12
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

PATRON_URL = re.compile(r"https?://[^\s\)\]<>\"'`]+")

# Dominios que se sabe que bloquean automatizacion; no vale la pena reintentar.
BLOQUEAN_AUTOMATICO = ("coursera.org", "grow.google", "linkedin.com", "indeed.com")


def normalizar(url: str) -> str:
    url = url.rstrip(".,;:)")
    return url.split("#", 1)[0]


def recolectar() -> dict[str, set[str]]:
    """{url: {archivos donde aparece}}"""
    urls: dict[str, set[str]] = {}
    for archivo in sorted(ROOT.rglob("*.md")):
        if ".git" in archivo.parts:
            continue
        for m in PATRON_URL.finditer(archivo.read_text(encoding="utf-8")):
            u = normalizar(m.group(0))
            if u:
                urls.setdefault(u, set()).add(str(archivo.relative_to(ROOT)))
    return urls


def comprobar(url: str) -> tuple[str, str]:
    """Devuelve (estado, detalle)."""
    if any(d in url for d in BLOQUEAN_AUTOMATICO):
        return "revisar", "el sitio bloquea peticiones automaticas"
    try:
        req = Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        with urlopen(req, timeout=TIMEOUT) as r:
            return "ok", str(r.status)
    except HTTPError as e:
        if e.code in (403, 429, 401):
            return "revisar", f"HTTP {e.code}: bloquea peticiones automaticas"
        if e.code in (404, 410):
            return "muerto", f"HTTP {e.code}"
        if 500 <= e.code < 600:
            return "revisar", f"HTTP {e.code}: error del servidor (puede ser transitorio)"
        return "revisar", f"HTTP {e.code}"
    except URLError as e:
        razon = str(e.reason)
        # Un fallo de certificado es de ESTE equipo, no del sitio.
        if "CERTIFICATE" in razon.upper() or "SSL" in razon.upper():
            return "revisar", "SSL: problema de certificados local, no del sitio"
        return "muerto", f"error de red: {e.reason}"
    except Exception as e:                        # noqa: BLE001
        if "CERTIFICATE" in str(e).upper() or "SSL" in type(e).__name__.upper():
            return "revisar", "SSL: problema de certificados local, no del sitio"
        return "revisar", f"{type(e).__name__}: {e}"


def main() -> int:
    solo_fallos = "--solo-fallos" in sys.argv
    urls = recolectar()
    print(f"[i] Enlaces externos unicos en el workspace: {len(urls)}\n")

    with ThreadPoolExecutor(max_workers=12) as ex:
        resultados = list(ex.map(lambda u: (u, *comprobar(u)), sorted(urls)))

    ok = [r for r in resultados if r[1] == "ok"]
    revisar = [r for r in resultados if r[1] == "revisar"]
    muertos = [r for r in resultados if r[1] == "muerto"]

    if not solo_fallos:
        print(f"[1] Vivos ({len(ok)})")
        for url, _e, det in ok:
            print(f"    {det:>4}  {url}")

    print(f"\n[2] No verificables automaticamente ({len(revisar)})")
    print("    (NO significa que esten muertos: el sitio bloquea scripts)")
    for url, _e, det in revisar:
        print(f"    {det:<42} {url}")

    print(f"\n[3] MUERTOS ({len(muertos)})")
    if muertos:
        for url, _e, det in muertos:
            print(f"    {det:<42} {url}")
            print(f"         citado en: {', '.join(sorted(urls[url]))}")
    else:
        print("    ninguno")

    if muertos:
        print(f"\n[!] {len(muertos)} enlaces muertos: hay que reemplazarlos en la "
              f"lista de recursos", file=sys.stderr)
        return 1
    print(f"\n[OK] Ningun enlace externo muerto. {len(ok)} responden y {len(revisar)} "
          "no se pueden verificar automaticamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
