# 🐍 SnakeGame — by jaimefgdev

> Two versions of the same game, feature-for-feature identical. Pick your platform.

---

## 🇬🇧 English

### Overview

Classic Snake built from scratch, available in two independent editions that share the same feature set:

| | Web edition (`index.html`) | Desktop edition (`snake.py`) |
|---|---|---|
| Runtime | Any modern browser | Python 3.8 + pygame |
| Storage | `localStorage` | `ranking.json` |
| Single file | ✅ | ✅ (+ `ranking.json`) |

### Features

- **10 speed levels** — from relaxed to chaotic.
- **Border mode** — hit the wall and die, or wrap around (your choice).
- **Bilingual UI** — switch between Spanish and English from the main menu.
- **Top-10 ranking per speed level** — your best scores survive between sessions.
- **Pause screen** with a semi-transparent overlay.
- **Polished visuals** — gradient snake body, rounded segments, directional eyes on the head, round glowing food with a specular highlight.
- **Touch support** — swipe gestures and an on-screen D-pad (web) / FINGERDOWN events (desktop).
- **Fully keyboard-navigable** menus on both versions.

### Web version

No installation needed. Just open the file in a browser:

```
# Option A — double-click index.html in your file manager

# Option B — serve locally (avoids potential CORS restrictions)
python -m http.server 8000
# then open http://localhost:8000
```

### Desktop version

Requirements: **Python 3.8+** and **pygame**.

```bash
git clone https://github.com/jaimefgdev/SnakeGame.git
cd SnakeGame
pip install -r requirements.txt
python snake.py
```

A `ranking.json` file is created automatically next to `snake.py` the first time a Top-10 score is registered.

### Controls

| Action | Keyboard | Touch / D-pad |
|---|---|---|
| Move | ↑ ↓ ← → or WASD | Swipe / D-pad buttons |
| Pause | Space | ⏸ button |
| Confirm | Enter | Click / tap |
| Back / quit | Escape | — |

### Project structure

```
index.html       # Web edition — complete single-file application
snake.py         # Desktop edition — complete single-file script
ranking.json     # Auto-generated; stores Top-10 scores (desktop only)
requirements.txt
README.md
```

### License

Personal project — do whatever you want with it.

---

## 🇪🇸 Español

### Descripción

Snake clásico hecho desde cero, disponible en dos ediciones independientes con las mismas funcionalidades:

| | Versión Web (`index.html`) | Versión Escritorio (`snake.py`) |
|---|---|---|
| Entorno | Cualquier navegador moderno | Python 3.8 + pygame |
| Almacenamiento | `localStorage` | `ranking.json` |
| Archivo único | ✅ | ✅ (+ `ranking.json`) |

### Características

- **10 niveles de velocidad** — de tranquilo a caótico.
- **Modo bordes** — chocas con la pared y mueres, o traspasas al otro lado (tú eliges).
- **Interfaz bilingüe** — cambia entre español e inglés desde el menú principal.
- **Ranking Top-10 por nivel de velocidad** — tus mejores puntuaciones persisten entre sesiones.
- **Menú de pausa** con overlay semitransparente.
- **Gráficos cuidados** — cuerpo en degradado, segmentos redondeados, ojos direccionales en la cabeza, comida circular con brillo y destello especular.
- **Soporte táctil** — gestos de deslizamiento y D-pad en pantalla (web) / eventos FINGERDOWN (escritorio).
- **Menús navegables completamente con teclado** en ambas versiones.

### Versión Web

Sin instalación. Ábrela directamente en el navegador:

```
# Opción A — doble clic sobre index.html en el explorador de archivos

# Opción B — servidor local (evita posibles restricciones CORS)
python -m http.server 8000
# luego abre http://localhost:8000
```

### Versión Escritorio

Requisitos: **Python 3.8+** y **pygame**.

```bash
git clone https://github.com/jaimefgdev/SnakeGame.git
cd SnakeGame
pip install -r requirements.txt
python snake.py
```

El archivo `ranking.json` se crea automáticamente junto a `snake.py` la primera vez que se registra una puntuación Top-10.

### Controles

| Acción | Teclado | Táctil / D-pad |
|---|---|---|
| Mover | ↑ ↓ ← → o WASD | Deslizar / botones D-pad |
| Pausar | Espacio | Botón ⏸ |
| Confirmar | Enter | Clic / toque |
| Volver / salir | Escape | — |

### Estructura del proyecto

```
index.html       # Versión Web — aplicación completa en un solo archivo
snake.py         # Versión Escritorio — script completo en un solo archivo
ranking.json     # Generado automáticamente; guarda el Top-10 (solo escritorio)
requirements.txt
README.md
```

### Licencia

Proyecto personal — haz lo que quieras con él.
