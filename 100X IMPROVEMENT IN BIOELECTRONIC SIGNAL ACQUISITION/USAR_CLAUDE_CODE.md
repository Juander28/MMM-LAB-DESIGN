# Usar Claude Code dentro del contenedor

Guia corta para Juan. La idea: en vez de darme acceso remoto a tu Docker,
corres un agente **dentro** del contenedor — ahi tiene acceso directo a xschem,
ngspice y todos estos archivos, sin exponer nada de tu maquina.

---

## Paso 0 — Un solo contenedor para todo

Decision tomada: se usa **un unico contenedor**, el que ya esta corriendo
(`iic-osic-tools_chipathon_xvnc`, imagen chipathon26). No hace falta cambiar
puertos ni crear contenedores nuevos.

Los archivos viven en `"C:\Users\juand\Documents\GitHub\sscs-2026-zotnetic\designs\100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION"` en Windows, que
el contenedor monta como `/foss/designs/100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION`. Editas en Windows, se ve
adentro al instante, y al reves. **No hace falta `docker cp` nunca.**

Para confirmar el montaje (una sola vez):

```powershell
docker inspect iic-osic-tools_chipathon_xvnc --format "{{json .Mounts}}"
```

Debe aparecer `C:\Users\juand\Documents\GitHub\sscs-2026-zotnetic\designs` -> `/foss/designs`.

## Paso 1 — Entrar al contenedor

```powershell
docker exec -it iic-osic-tools_chipathon_xvnc bash
```

(Si te cansa el nombre largo: `docker rename iic-osic-tools_chipathon_xvnc osic`
y despues es solo `docker exec -it osic bash`.)

## Paso 2 — Instalar Claude Code (una sola vez)

```bash
cd "/foss/designs/100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION"
bash instalar_claude_code.sh
```

El script prueba primero el instalador nativo (`curl https://claude.ai/install.sh`),
que no necesita Node.js, y si falla intenta por `npm`. Al final te dice si quedo
instalado y donde.

> Si el contenedor no tiene salida a internet, ninguno de los dos metodos va a
> funcionar. En ese caso avisame y buscamos otra ruta.

## Paso 3 — Autenticarse (una sola vez)

Al correr `claude` por primera vez te va a pedir iniciar sesion. Dos caminos:

**a) Por navegador.** Imprime un enlace. Abrelo en el Firefox que trae el propio
contenedor (entra por noVNC a `http://localhost`, que es donde escucha este
contenedor), o copia el enlace y pegalo en el navegador de Windows.

**b) Por API key.** Si prefieres, exporta la clave:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.bashrc
```

## Paso 4 — Usarlo

```bash
cd "/foss/designs/100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION"
claude
```

Al arrancar en esta carpeta lee **`CLAUDE.md`** automaticamente, asi que ya sabe:
el punto de diseno verificado, los cinco hallazgos importantes, las reglas de
diseno ajustadas, la trampa de resolucion del span completo, y el estado del
modelo de TFT. No tienes que explicarle nada.

---

## Cosas que le puedes pedir directamente

```
Corre run_test1.sh y dime si los notches siguen en 55.888 y 100.003 MHz.

Mide la profundidad REAL del canal B con el zoom, no con el span completo.

Agrega un tercer canal en 133.3 MHz al esquematico de test1 y co-sintonizalo
sin romper los otros dos.

Barre cpB de 100 a 250 fF y dime en que punto deja de cumplir BW <= 30 kHz.

Que pasa con el punto de diseno si Kp baja a 50u (mas parecido a un TFT IGZO)?

Convierte el X10 a los valores rediseniados con L=100n y verifica cuantos
canales dan notch medible.
```

## Consejo

Como el contenedor tiene las herramientas reales, pidele siempre que **verifique
ejecutando**, no que teorice. La regla del proyecto (esta en CLAUDE.md) es:
si genera un esquematico, que lo vuelva a netlistear y simular antes de afirmar
que funciona.

---

## Persistir la instalacion

Los archivos del proyecto estan a salvo pase lo que pase: viven en Windows
(`"C:\Users\juand\Documents\GitHub\sscs-2026-zotnetic\designs\100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION"`), no dentro del contenedor.

Lo unico que se perderia al borrar el contenedor es Claude Code instalado.
Para que quede fijo, guarda una foto despues de instalarlo:

```powershell
docker commit iic-osic-tools_chipathon_xvnc iic-osic-tools:chipathon26-claude
```

Y la proxima vez arranca desde esa imagen en vez de la original.
