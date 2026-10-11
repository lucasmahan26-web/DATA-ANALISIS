# =============================================================================
# verificar_postgres.ps1
# =============================================================================
# Verifica los scripts SQL del Proyecto 2 contra PostgreSQL DE VERDAD.
#
# Por que existe:
#   Los datos del Proyecto 2 se validaron contra SQLite, pero el DDL
#   (P2_01_crear_tablas.sql) y las constraints (P2_02_agregar_constraints.sql)
#   estan escritos en sintaxis PostgreSQL y nunca se habian ejecutado contra
#   PostgreSQL. Un error de sintaxis o de tipo ahi lo encuentra el alumno en la
#   semana 4, no nosotros.
#
# Como funciona:
#   Levanta un cluster TEMPORAL con autenticacion trust en el puerto 5433, para
#   no tocar la base real del usuario (que usa scram-sha-256 y tiene contrasena).
#   Al terminar, lo detiene y borra. Todo en un solo proceso: si se corta a la
#   mitad, el arbol de procesos se lleva el servidor y no queda nada colgado.
#
# Ejecutar:  pwsh -File scripts/verificar_postgres.ps1
# =============================================================================

$ErrorActionPreference = "Continue"
$bin  = "C:\Program Files\PostgreSQL\18\bin"
$test = Join-Path $env:TEMP "dsh_pgtest"
$data = Join-Path $test "data"
$port = 5433
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$env:PGCLIENTENCODING = "UTF8"

$fallos = New-Object System.Collections.Generic.List[string]

function Paso($n, $texto) { Write-Host "`n[$n] $texto" }

# ---------------------------------------------------------------- 0. limpieza
Paso 0 "Limpiando restos de corridas anteriores"
& "$bin\pg_ctl.exe" -D $data stop -m immediate 2>&1 | Out-Null
if (Test-Path $test) { Remove-Item $test -Recurse -Force -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Path $test -Force | Out-Null
Write-Host "    ok"

# ------------------------------------------------------------------ 1. initdb
Paso 1 "Creando cluster temporal (trust, UTF8, puerto $port)"
& "$bin\initdb.exe" -D $data -U postgres --auth=trust -E UTF8 --locale=C 2>&1 |
    Select-Object -Last 1
if (-not (Test-Path $data)) { Write-Error "initdb fallo"; exit 1 }

# ------------------------------------------------------------------- 2. start
Paso 2 "Arrancando el servidor"
# NO se usa pg_ctl start: arranca postgres como proceso hijo y hereda los
# handles de stdout/stderr, con lo cual PowerShell se queda esperando a que el
# pipe se cierre... y nunca se cierra, porque el servidor sigue vivo.
# Se lanza postgres.exe directamente con Start-Process (sin -Wait): devuelve el
# control enseguida y el servidor queda corriendo en segundo plano.
$pgOut = Join-Path $test "pg_out.txt"
$pgErr = Join-Path $test "pg_err.txt"
$proc = Start-Process -FilePath "$bin\postgres.exe" `
    -ArgumentList @("-D", "`"$data`"", "-p", $port) `
    -RedirectStandardOutput $pgOut -RedirectStandardError $pgErr `
    -PassThru -WindowStyle Hidden

# Esperar a que responda (hasta 30 s)
$listo = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    $vivo = & "$bin\psql.exe" -p $port -U postgres -d postgres -t -A -c "SELECT 1;" 2>&1
    if (($vivo -join "") -match "1") { $listo = $true; break }
}
if (-not $listo) {
    Write-Host "    ERROR: el servidor no responde en el puerto $port tras 30 s" -ForegroundColor Red
    Get-Content (Join-Path $test "log.txt") -Tail 15 -ErrorAction SilentlyContinue
    Get-Content $pgErr -Tail 15 -ErrorAction SilentlyContinue
    if ($proc) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
    Remove-Item $test -Recurse -Force -ErrorAction SilentlyContinue
    exit 1
}
Write-Host "    servidor respondiendo en el puerto $port (PID $($proc.Id))"

# ---------------------------------------------------------------- 3. createdb
Paso 3 "Creando la base 'analisis'"
& "$bin\createdb.exe" -p $port -U postgres analisis 2>&1

# -------------------------------------------------------------------- 4. DDL
Paso 4 "Ejecutando P2_01_crear_tablas.sql (el DDL entregado, sin modificar)"
$ddl = & "$bin\psql.exe" -p $port -U postgres -d analisis -v ON_ERROR_STOP=1 `
    -f "$repo\scripts\P2_01_crear_tablas.sql" 2>&1
$ddlErr = $ddl | Select-String -Pattern "ERROR|FATAL" 
if ($ddlErr) {
    $fallos.Add("P2_01_crear_tablas.sql dio error: $($ddlErr -join ' | ')")
    Write-Host "    ERROR:" ($ddl | Select-Object -Last 4)
} else {
    Write-Host "    ok, sin errores"
}

Paso 4 "  Tablas creadas:"
& "$bin\psql.exe" -p $port -U postgres -d analisis -t -c `
    "SELECT string_agg(tablename, ', ' ORDER BY tablename) FROM pg_tables WHERE schemaname='public';" 2>&1

# ------------------------------------------------------------------ 5. carga
Paso 5 "Cargando los 7 CSV con \copy (las instrucciones del propio script)"
$tablas = "categorias", "productos", "sucursales", "vendedores", "clientes",
          "medios_pago", "ventas"
$lineas = @("SET client_encoding TO 'UTF8';")
foreach ($t in $tablas) {
    $ruta = "$repo\datos\p2\$t.csv"
    $lineas += "\copy $t FROM '$ruta' WITH (FORMAT csv, HEADER true, NULL '');"
}
$lineas | Out-File -FilePath (Join-Path $test "carga.sql") -Encoding utf8
$carga = & "$bin\psql.exe" -p $port -U postgres -d analisis -v ON_ERROR_STOP=1 `
    -f (Join-Path $test "carga.sql") 2>&1
$cargaErr = $carga | Select-String -Pattern "ERROR|FATAL"
if ($cargaErr) {
    $fallos.Add("la carga dio error: $($cargaErr -join ' | ')")
    Write-Host "    ERROR:" ($carga | Select-Object -Last 6)
} else {
    Write-Host "    ok"
}

# -------------------------------------------------------- 6. conteos de carga
Paso 6 "Verificando los conteos de filas"
$esperado = @{ categorias = 8; productos = 57; sucursales = 12; vendedores = 40;
               clientes = 312; medios_pago = 5; ventas = 130688 }
foreach ($t in $tablas) {
    $real = (& "$bin\psql.exe" -p $port -U postgres -d analisis -t -A `
        -c "SELECT count(*) FROM $t;" 2>&1) -join ""
    $real = $real.Trim()
    $ok = ($real -eq "$($esperado[$t])")
    if (-not $ok) { $fallos.Add("$t tiene $real filas, se esperaban $($esperado[$t])") }
    $estado = if ($ok) { "OK" } else { "FALLA" }
    # OJO: la alineacion de .NET es {1,8} o {1,-8}; {1,>8} NO es valida y tira
    # "La cadena de entrada no tiene el formato correcto".
    Write-Host ("    {0,-14}{1,8} / {2,-8} {3}" -f $t, $real, "$($esperado[$t])", $estado)
}

# ---------------------------------------- 7. consultas de diagnostico en PG
Paso 7 "Ejecutando las consultas de diagnostico de la clave contra PostgreSQL"
$sqlVar = @'
WITH base AS (
    SELECT c.id_insumo, c.semana,
           ((LAG(c.cantidad) OVER (PARTITION BY c.id_insumo ORDER BY c.semana))
             + COALESCE(p.entregas, 0) - c.cantidad) * i.contenido_por_envase AS ml
    FROM conteos c
    JOIN insumos i ON i.id_insumo = c.id_insumo
    LEFT JOIN (SELECT id_insumo, semana, SUM(cantidad) AS entregas
               FROM compras GROUP BY id_insumo, semana) p
           ON p.id_insumo = c.id_insumo AND p.semana = c.semana
)
SELECT count(*) FROM base;
'@
# Control de portabilidad: las queries de diagnostico del P2 tal cual estan
$diag = @'
SELECT 'V1', SUM(c - 1) FROM (SELECT COUNT(*) AS c FROM ventas GROUP BY id_venta HAVING COUNT(*) > 1) t
UNION ALL SELECT 'V2', COUNT(*) FROM ventas v LEFT JOIN productos p ON v.id_producto = p.id_producto WHERE p.id_producto IS NULL
UNION ALL SELECT 'V3', COUNT(*) FROM ventas v LEFT JOIN sucursales s ON v.id_sucursal = s.id_sucursal WHERE s.id_sucursal IS NULL
UNION ALL SELECT 'V6', COUNT(*) FROM ventas WHERE cantidad < 0
UNION ALL SELECT 'V8', COUNT(*) FROM ventas WHERE fecha_venta < '2023-01-01' OR fecha_venta > '2024-12-31'
UNION ALL SELECT 'V11', COUNT(*) FROM ventas WHERE ABS(cantidad * precio_unitario * (1 - CASE WHEN descuento > 1 THEN descuento / 100.0 WHEN descuento < 0 THEN 0 ELSE descuento END) - importe_neto) > 1
UNION ALL SELECT 'D1', SUM(c - 1) FROM (SELECT COUNT(*) AS c FROM clientes GROUP BY id_cliente HAVING COUNT(*) > 1) t
ORDER BY 1;
'@
$diag | Out-File -FilePath (Join-Path $test "diag.sql") -Encoding utf8
$res = & "$bin\psql.exe" -p $port -U postgres -d analisis -f (Join-Path $test "diag.sql") 2>&1
if ($res | Select-String -Pattern "ERROR") {
    $fallos.Add("las consultas de diagnostico fallaron en PostgreSQL: $($res -join ' | ')")
    Write-Host "    ERROR:" ($res | Select-Object -Last 6)
} else {
    $res | Where-Object { $_ -match "^\s*[VD]\d" } | ForEach-Object { Write-Host "    $_" }
}

# ------------------------------------- 7b. calentamiento SQL en PostgreSQL
Paso "7b" "Ejecutando los 28 ejercicios de calentamiento en dialecto PostgreSQL"
$archCalent = "$repo\datos\p2\calentamiento_postgres.sql"
if (-not (Test-Path $archCalent)) {
    $fallos.Add("falta $archCalent; ejecutar scripts/verificar_calentamiento_sql.py")
    Write-Host "    FALTA el archivo de ejercicios"
} else {
    $calent = & "$bin\psql.exe" -p $port -U postgres -d analisis -v ON_ERROR_STOP=1 `
        -f $archCalent 2>&1
    $errCal = $calent | Select-String -Pattern "ERROR"
    if ($errCal) {
        $fallos.Add("ejercicios que fallan en PostgreSQL: $($errCal -join ' | ')")
        Write-Host "    ERROR:" ($errCal | Select-Object -First 4 | ForEach-Object { $_.Line.Trim() })
    } else {
        $n = ($calent | Select-String -Pattern "^--- Ejercicio").Count
        Write-Host "    $n de 28 ejercicios ejecutados sin error"
    }
}

Paso "7b" "Control: el dialecto SQLite DEBE fallar en PostgreSQL"
$dialErr = & "$bin\psql.exe" -p $port -U postgres -d analisis -t -A `
    -c "SELECT strftime('%Y', fecha_venta) FROM ventas LIMIT 1;" 2>&1
if (($dialErr -join "") -match "ERROR") {
    Write-Host "    OK: strftime() no existe en PostgreSQL -> la tabla de dialectos es correcta"
    Write-Host "        ($((($dialErr | Select-String 'ERROR').Line -split '\n')[0].Trim()))"
} else {
    $fallos.Add("strftime() funciono en PostgreSQL: la tabla de dialectos de la guia estaria mal")
    Write-Host "    PROBLEMA: strftime() funciono, la guia miente"
}

# -------------------------------------------------- 8. constraints (deben fallar)
Paso 8 "Ejecutando P2_02_agregar_constraints.sql (DEBE fallar sobre datos crudos)"
$cons = & "$bin\psql.exe" -p $port -U postgres -d analisis `
    -f "$repo\scripts\P2_02_agregar_constraints.sql" 2>&1
$errCons = $cons | Select-String -Pattern "ERROR"
if ($errCons) {
    Write-Host "    OK: el motor rechaza los datos crudos, como esta previsto"
    $errCons | Select-Object -First 3 | ForEach-Object { Write-Host "      $($_.Line.Trim())" }
} else {
    $fallos.Add("P2_02 NO fallo sobre datos crudos: las constraints no se estan aplicando")
    Write-Host "    PROBLEMA: no dio error"
}

# ------------------------------------------------------- 9. limpieza final
Paso 9 "Deteniendo y borrando el cluster temporal"
if ($proc) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 3
# Matar SOLO los procesos del cluster temporal, identificandolos por su linea de
# comando. Buscar por nombre mataria tambien el servicio real del usuario.
Get-CimInstance Win32_Process -Filter "Name='postgres.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*dsh_pgtest*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1
Remove-Item $test -Recurse -Force -ErrorAction SilentlyContinue
$resto = Get-CimInstance Win32_Process -Filter "Name='postgres.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*dsh_pgtest*" }
if ($resto) { $fallos.Add("quedaron $($resto.Count) procesos del cluster temporal vivos") }
Write-Host ("    ok" + $(if ($resto) { " (con procesos residuales)" } else { "" }))

# ------------------------------------------------------------ resultado final
Write-Host "`n" ("=" * 66)
if ($fallos.Count -gt 0) {
    Write-Host "[!] FALLOS ($($fallos.Count)):" -ForegroundColor Red
    $fallos | ForEach-Object { Write-Host "    - $_" }
    exit 1
}
Write-Host "[OK] El DDL ejecuta en PostgreSQL 18, los 7 CSV cargan con \copy,"
Write-Host "     las consultas de diagnostico son portables y las constraints se disparan."
exit 0
