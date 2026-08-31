# =====================================================================
#  correr_simulaciones_2025.ps1
#  Corre las simulaciones TEST1 y X10 en un contenedor temporal creado
#  desde la imagen del Chipathon 2025 (hpretl/iic-osic-tools:chipathon),
#  SIN tocar el chipathon26 que tengas corriendo (no publica puertos).
#
#  Uso:  abre PowerShell y pega:
#    powershell -ExecutionPolicy Bypass -File "I:\My Drive\UCI\PHD\RESEARCH\100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION\BIOELECTRONIC SIGNAL ADQUISITION\correr_simulaciones_2025.ps1"
# =====================================================================
$ErrorActionPreference = "Stop"
$SIM = "I:\My Drive\UCI\PHD\RESEARCH\100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION\BIOELECTRONIC SIGNAL ADQUISITION\simulaciones"

Write-Host ">> Lanzando contenedor temporal 'chip25' (imagen 2025, sin puertos)..." -ForegroundColor Cyan
docker rm -f chip25 2>$null | Out-Null
docker run -d --rm --name chip25 --entrypoint sleep hpretl/iic-osic-tools:chipathon infinity | Out-Null

Write-Host ">> Copiando carpeta simulaciones al contenedor..." -ForegroundColor Cyan
docker cp "$SIM" chip25:/headless/simulaciones

Write-Host ""
Write-Host ">> TEST1 (esperado: notch A ~55.890 MHz y notch B ~100.002 MHz)" -ForegroundColor Green
docker exec chip25 bash -lc "cd /headless/simulaciones/test1 && (bash run_test1.sh || (echo '--- xschem fallo; usando netlist pre-generado ---' && ngspice -b cross_coupled_test1.spice && python3 analyze_notch.py test1_ac.csv))"

Write-Host ""
Write-Host ">> X10 (esperado: SIN notches medibles con los valores actuales)" -ForegroundColor Green
docker exec chip25 bash -lc "cd /headless/simulaciones/x10 && (bash run_x10.sh || (echo '--- xschem fallo; usando netlist pre-generado ---' && ngspice -b cross_coupled_x10.spice && python3 analyze_notch.py x10_ac.csv))"

Write-Host ""
Write-Host ">> Copiando resultados de vuelta a tu Drive..." -ForegroundColor Cyan
docker cp chip25:/headless/simulaciones/test1/test1_ac.csv "$SIM\test1\" 2>$null
docker cp chip25:/headless/simulaciones/x10/x10_ac.csv "$SIM\x10\" 2>$null

docker stop chip25 | Out-Null
Write-Host ""
Write-Host "LISTO. Referencia (span completo, paso 3.5 kHz):" -ForegroundColor Yellow
Write-Host "  TEST1  notch 1: f0 ~ 55.888 MHz  (~16 dB aparentes en span completo)"
Write-Host "  TEST1  notch 2: f0 ~ 100.003 MHz (~14 dB aparentes en span completo)"
Write-Host "  (la profundidad real 35.9/39.7 dB se ve con los zooms: edita el bloque"
Write-Host "   PARAMS del .sch y descomenta una linea .ac de zoom)"
Write-Host "  X10: sin notches (<0.03 dB) - ver LC_design_values.xlsx para el rediseno"
