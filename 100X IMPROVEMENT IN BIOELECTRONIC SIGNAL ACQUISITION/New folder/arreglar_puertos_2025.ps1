# =====================================================================
#  arreglar_puertos_2025.ps1   (v2 - robusto)
#
#  Deja el contenedor del Chipathon 2025 funcionando AL MISMO TIEMPO
#  que el chipathon26, en puertos libres elegidos automaticamente.
#  Luego copia la carpeta simulaciones y corre TEST1 y X10 adentro.
#
#  El contenedor viejo NO se toca ni se borra.
#  El chipathon26 sigue corriendo intacto.
#
#  Uso:
#    powershell -ExecutionPolicy Bypass -File "<ruta>\arreglar_puertos_2025.ps1"
# =====================================================================
$ErrorActionPreference = "Stop"

$OLD   = "a7576a766fd7"                        # contenedor 2025 (exited)
$NEW   = "chip25"                              # contenedor nuevo
$SNAP  = "iic-osic-tools:chipathon2025-snap"   # imagen-foto del viejo
$SIM   = "I:\My Drive\UCI\PHD\RESEARCH\100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION\BIOELECTRONIC SIGNAL ADQUISITION\simulaciones"

function Say($t, $c = "Gray") { Write-Host $t -ForegroundColor $c }

function Get-FreePort($candidates) {
    foreach ($p in $candidates) {
        $busy = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
        if (-not $busy) { return $p }
    }
    throw "No encontre puerto libre entre: $($candidates -join ', ')"
}

# --------------------------------------------------------------- 0. checks
Say "== 0. Verificando Docker ==" Cyan
try { docker version --format "  Docker OK: {{.Server.Version}}" } catch {
    throw "Docker Desktop no responde. Abrelo y vuelve a correr este script."
}
if (-not (docker ps -a --format "{{.ID}}" | Select-String -SimpleMatch $OLD.Substring(0,8))) {
    throw "No encontre el contenedor $OLD. Corre 'docker ps -a' y ajusta la variable OLD arriba."
}
if (-not (Test-Path $SIM)) { throw "No encontre la carpeta: $SIM" }

# --------------------------------------------------------------- 1. info
Say ""
Say "== 1. Como estaba configurado el contenedor 2025 ==" Cyan
docker inspect $OLD --format "  Puertos viejos : {{json .HostConfig.PortBindings}}"
docker inspect $OLD --format "  Montajes       : {{json .Mounts}}"

# --------------------------------------------------------------- 2. foto
Say ""
Say "== 2. Guardando una foto del contenedor (no se pierde nada de adentro) ==" Cyan
docker commit $OLD $SNAP | Out-Null
Say "  imagen creada: $SNAP" Green

# --------------------------------------------------------------- 3. montajes
Say ""
Say "== 3. Reutilizando los mismos montajes ==" Cyan
$vArgs = @()
$mountsJson = docker inspect $OLD --format "{{json .Mounts}}"
if ($mountsJson -and $mountsJson.Trim() -ne "null") {
    foreach ($m in ($mountsJson | ConvertFrom-Json)) {
        if     ($m.Type -eq "bind")   { $spec = "$($m.Source):$($m.Destination)" }
        elseif ($m.Type -eq "volume") { $spec = "$($m.Name):$($m.Destination)" }
        else { continue }
        $vArgs += "-v"; $vArgs += $spec
        Say "  reusando: $spec"
    }
}
if ($vArgs.Count -eq 0) { Say "  (el contenedor viejo no tenia montajes)" DarkGray }
# NOTA: no montamos la carpeta del Drive (la unidad I: de Google Drive no siempre
# se puede bind-montear en Docker Desktop). Usamos 'docker cp', que siempre funciona.

# --------------------------------------------------------------- 4. puertos
Say ""
Say "== 4. Eligiendo puertos libres ==" Cyan
$pWeb = Get-FreePort @(8081, 8082, 8083, 8090)
$pVnc = Get-FreePort @(5902, 5903, 5904)
$pJup = Get-FreePort @(8889, 8890, 8891)
Say "  noVNC/web -> $pWeb   VNC -> $pVnc   Jupyter -> $pJup" Green

# --------------------------------------------------------------- 5. run
Say ""
Say "== 5. Creando el contenedor nuevo '$NEW' ==" Cyan
docker rm -f $NEW 2>$null | Out-Null
docker run -d --name $NEW -p "${pWeb}:80" -p "${pVnc}:5901" -p "${pJup}:8888" @vArgs $SNAP | Out-Null
Start-Sleep -Seconds 6

$state = docker inspect $NEW --format "{{.State.Status}}"
if ($state -ne "running") {
    Say "  El contenedor arranco y se detuvo. Ultimas lineas del log:" Red
    docker logs --tail 30 $NEW
    Say "  Plan B (sin GUI, solo simulaciones):" Yellow
    Say "    docker rm -f $NEW"
    Say "    docker run -d --rm --name $NEW --entrypoint sleep $SNAP infinity"
    throw "El contenedor no se mantuvo arriba."
}
docker ps --filter "name=$NEW" --format "  {{.Names}}  {{.Status}}  {{.Ports}}"

# --------------------------------------------------------------- 6. copiar
Say ""
Say "== 6. Copiando la carpeta simulaciones al contenedor ==" Cyan
docker exec $NEW bash -lc "mkdir -p /foss/designs" 2>$null | Out-Null
docker cp "$SIM" "${NEW}:/foss/designs/simulaciones"
docker exec $NEW bash -lc "chmod +x /foss/designs/simulaciones/*/*.sh; ls -la /foss/designs/simulaciones"

# --------------------------------------------------------------- 7. tools
Say ""
Say "== 7. Herramientas dentro del contenedor ==" Cyan
docker exec $NEW bash -lc "which xschem ngspice python3; ngspice -v 2>/dev/null | head -1"

# --------------------------------------------------------------- 8. TEST1
Say ""
Say "== 8. TEST1  (esperado: notch A ~55.888 MHz y notch B ~100.003 MHz) ==" Green
docker exec $NEW bash -lc "cd /foss/designs/simulaciones/test1 && (bash run_test1.sh 2>&1 || (echo '--- xschem fallo, uso el netlist pre-generado ---'; ngspice -b cross_coupled_test1.spice 2>&1; python3 analyze_notch.py test1_ac.csv))" | Select-String -Pattern "notch|puntos|error|Error|f0="

# --------------------------------------------------------------- 9. X10
Say ""
Say "== 9. X10  (esperado: SIN notches medibles con los valores actuales) ==" Green
docker exec $NEW bash -lc "cd /foss/designs/simulaciones/x10 && (bash run_x10.sh 2>&1 || (ngspice -b cross_coupled_x10.spice 2>&1; python3 analyze_notch.py x10_ac.csv))" | Select-String -Pattern "notch|puntos|sin notches|error|Error"

# --------------------------------------------------------------- 10. traer
Say ""
Say "== 10. Trayendo los resultados a tu Drive ==" Cyan
docker cp "${NEW}:/foss/designs/simulaciones/test1/test1_ac.csv" "$SIM\test1\" 2>$null
docker cp "${NEW}:/foss/designs/simulaciones/x10/x10_ac.csv"     "$SIM\x10\"   2>$null
Say "  listo (si existian los CSV)"

# --------------------------------------------------------------- fin
# --------------------------------------------------------------- 11. claude code
Say ""
Say "== 11. Claude Code dentro del contenedor (opcional) ==" Cyan
$r = Read-Host "  Instalar Claude Code adentro ahora? (s/N)"
if ($r -eq "s" -or $r -eq "S") {
    docker exec -it $NEW bash -lc "cd /foss/designs/simulaciones && bash instalar_claude_code.sh"
    Say ""
    Say "  Para usarlo:" Yellow
    Say "    docker exec -it $NEW bash"
    Say "    cd /foss/designs/simulaciones && claude"
} else {
    Say "  Saltado. Cuando quieras:" DarkGray
    Say "    docker exec -it $NEW bash -lc 'cd /foss/designs/simulaciones && bash instalar_claude_code.sh'" DarkGray
}

Say ""
Say "==================== LISTO ====================" Yellow
Say "Los DOS contenedores estan corriendo a la vez:"
Say "  chipathon26 : http://localhost        Jupyter http://localhost:8888"
Say "  $NEW (2025) : http://localhost:$pWeb        Jupyter http://localhost:$pJup"
Say ""
Say "Para entrar por consola al 2025:"
Say "  docker exec -it $NEW bash"
Say "Para abrir el esquematico con interfaz grafica (dentro del noVNC del navegador):"
Say "  xschem /foss/designs/simulaciones/test1/cross_coupled_test1.sch"
Say ""
Say "Referencia esperada (span completo, paso 3.5 kHz):" DarkGray
Say "  TEST1 notch 1: f0 ~  55.888 MHz" DarkGray
Say "  TEST1 notch 2: f0 ~ 100.003 MHz" DarkGray
Say "  X10: sin notches (<0.03 dB) - ver LC_design_values.xlsx" DarkGray
Say ""
Say "Para apagar solo el 2025 cuando termines:  docker stop $NEW" DarkGray
