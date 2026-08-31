#!/bin/bash
# =====================================================================
#  instalar_claude_code.sh
#  Instala Claude Code DENTRO del contenedor (IIC-OSIC-TOOLS / Chipathon)
#
#  Uso (dentro del contenedor):
#      cd "/foss/designs/100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION"
#      bash instalar_claude_code.sh
# =====================================================================
set -u

echo "==================================================================="
echo " Instalando Claude Code dentro del contenedor"
echo "==================================================================="
echo

# --- 0. donde estamos -------------------------------------------------
echo ">> Entorno:"
echo "   usuario : $(whoami)"
echo "   home    : ${HOME:-<sin HOME>}"
echo "   carpeta : $(pwd)"
echo

# --- 1. herramientas del proyecto ------------------------------------
echo ">> Herramientas de simulacion disponibles:"
for t in xschem ngspice python3; do
    if command -v "$t" >/dev/null 2>&1; then
        echo "   OK   $t -> $(command -v $t)"
    else
        echo "   FALTA $t"
    fi
done
echo

# --- 2. instalador nativo (no necesita Node) -------------------------
echo ">> Metodo 1: instalador nativo (recomendado, no requiere Node.js)"
if command -v claude >/dev/null 2>&1; then
    echo "   Claude Code YA esta instalado: $(command -v claude)"
else
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL https://claude.ai/install.sh | bash
    else
        echo "   curl no disponible, saltando al metodo 2"
    fi
fi

# el instalador nativo deja el binario en ~/.local/bin
export PATH="$HOME/.local/bin:$PATH"

# --- 3. respaldo por npm ---------------------------------------------
if ! command -v claude >/dev/null 2>&1; then
    echo
    echo ">> Metodo 2: npm"
    if command -v npm >/dev/null 2>&1; then
        echo "   node: $(node -v 2>/dev/null)  npm: $(npm -v 2>/dev/null)"
        npm install -g @anthropic-ai/claude-code || \
            npm install -g --prefix "$HOME/.local" @anthropic-ai/claude-code
    else
        echo "   npm NO esta en este contenedor."
        echo "   Instala Node.js primero, por ejemplo:"
        echo "     curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
        echo "     sudo apt-get install -y nodejs"
        echo "   (o usa el metodo nativo con curl, arriba)"
    fi
fi

# --- 4. dejar el PATH persistente ------------------------------------
if ! grep -q 'HOME/.local/bin' "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo
    echo ">> PATH agregado a ~/.bashrc"
fi

# --- 5. resultado -----------------------------------------------------
echo
echo "==================================================================="
if command -v claude >/dev/null 2>&1; then
    echo " LISTO. Claude Code instalado en: $(command -v claude)"
    claude --version 2>/dev/null || true
    echo
    echo " Siguiente paso:"
    echo "   cd \"/foss/designs/100X IMPROVEMENT IN BIOELECTRONIC SIGNAL ACQUISITION\""
    echo "   claude"
    echo
    echo " La primera vez pedira autenticacion. Dos opciones:"
    echo "   a) Sigue el enlace que imprime (abrelo en el Firefox del noVNC"
    echo "      del contenedor, o copialo a tu navegador de Windows)."
    echo "   b) Usa una API key:  export ANTHROPIC_API_KEY=sk-ant-..."
    echo "      (ponla en ~/.bashrc para que quede permanente)"
    echo
    echo " Al arrancar en esta carpeta leera CLAUDE.md automaticamente y"
    echo " tendra todo el contexto del proyecto."
else
    echo " No se pudo instalar automaticamente."
    echo " Revisa la salida de arriba; lo mas probable es que falten"
    echo " curl/Node.js o que no haya salida a internet en el contenedor."
    echo " Prueba a mano:  curl -fsSL https://claude.ai/install.sh | bash"
fi
echo "==================================================================="
