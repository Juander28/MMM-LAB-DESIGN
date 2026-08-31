# =====================================================================
#  clonar_2025_puertos_libres.ps1
#
#  Crea un contenedor NUEVO a partir del Chipathon 2025 (a7576a766fd7)
#  con puertos DISTINTOS, para que conviva con el chipathon26 que ya
#  esta corriendo. No borra nada: el contenedor viejo queda intacto.
#
#  Puertos nuevos:   noVNC -> 8081   VNC -> 5902   Jupyter -> 8889
#  (el 2026 se queda con 80 / 5901 / 8888)
#
#  Uso:
#    powershell -ExecutionPolicy Bypass -File "<ruta>\clonar_2025_puertos_libres.ps1"
# =====================================================================
$ErrorActionPreference = "Stop"

$OLD   = "a7576a766fd7"                          # contenedor 2025 (exited)
$NEW   = "chip25_gui"                            # contenedor nuevo
$SNAP  = "iic-osic-tools:chipathon2025-snap"     # imagen-foto del viejo
$DRIVE = "I:\My Drive\UCI\PHD\RESEARCH\100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION\BIOELECTRONIC SIGNAL ADQUISITION"

Write-Host "== 1. Configuracion actual del contenedor 2025 ==" -ForegroundColor Cyan
docker inspect $OLD --format "  Carpetas montadas: {{json .HostConfig.Binds}}"
docker inspect $OLD --format "  Puertos actuales : {{json .HostConfig.PortBindings}}"

Write-Host ""
Write-Host "== 2. Guardando una foto del contenedor (no se pierde nada de adentro) ==" -ForegroundColor Cyan
docker commit $OLD $SNAP | Out-Null
Write-Host "  imagen creada: $SNAP"

Write-Host ""
Write-Host "== 3. Reutilizando las mismas carpetas montadas ==" -ForegroundColor Cyan
$bindsJson = docker inspect $OLD --format "{{json .HostConfig.Binds}}"
$binds = @()
if ($bindsJson -and $bindsJson.Trim() -ne "null") { $binds = $bindsJson | ConvertFrom-Json }
$vArgs = @()
foreach ($b in $binds) { $vArgs += "-v"; $vArgs += $b; Write-Host "  reusando: $b" }
if (($binds -join ";") -notmatch "BIOELECTRONIC") {
    $vArgs += "-v"; $vArgs += "${DRIVE}:/foss/designs"
    Write-Host "  agregando: tu carpeta del Drive -> /foss/designs"
}

Write-Host ""
Write-Host "== 4. Creando el contenedor nuevo con puertos libres ==" -ForegroundColor Cyan
docker rm -f $NEW 2>$null | Out-Null
docker run -d --name $NEW -p 8081:80 -p 5902:5901 -p 8889:8888 @vArgs $SNAP | Out-Null

Start-Sleep -Seconds 4
docker ps --filter "name=$NEW" --format "  {{.Names}}  {{.Status}}  {{.Ports}}"

Write-Host ""
Write-Host "LISTO. Ahora tienes los DOS corriendo a la vez:" -ForegroundColor Yellow
Write-Host "  chipathon26 (el de siempre) : http://localhost      / Jupyter http://localhost:8888"
Write-Host "  chip25_gui  (el del 2025)   : http://localhost:8081 / Jupyter http://localhost:8889"
Write-Host ""
Write-Host "Para correr las simulaciones dentro del 2025:" -ForegroundColor Yellow
Write-Host '  docker exec -it chip25_gui bash -lc "cd /foss/designs/simulaciones/test1 && ./run_test1.sh"'
Write-Host ""
Write-Host "Si la carpeta /foss/designs saliera vacia, copiala a mano:" -ForegroundColor DarkGray
Write-Host "  docker cp `"$DRIVE\simulaciones`" ${NEW}:/foss/designs/simulaciones"
Write-Host ""
Write-Host "Para apagarlo al terminar:  docker stop $NEW" -ForegroundColor DarkGray
