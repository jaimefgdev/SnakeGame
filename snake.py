"""
SnakeGame — Desktop edition  (pygame)
by jaimefgdev

Feature-parity with the HTML/Web edition:
  · Bilingual UI  (ES / EN)  selectable from the main menu
  · Top-10 ranking per speed level, persisted to ranking.json
  · Visual details: gradient body, rounded segments, directional eyes on the
    head, and a round glow-highlight food apple — all matching the Canvas style
  · Touch / swipe support via FINGERDOWN / FINGERUP and mouse-drag events
  · FPS-independent tick timing: speed → ms/tick using the exact HTML formula
"""

import sys
import json
import random
import datetime
from pathlib import Path

import pygame

# ═══════════════════════════════════════════════════════════════════
#  CONSTANTS & PALETTE
# ═══════════════════════════════════════════════════════════════════

GRID         = 20           # cells per side
CELL         = 24           # pixels per cell
BOARD        = GRID * CELL  # 480 px square board
INFO_H       = 44           # top info-bar height in pixels
SCREEN_W     = BOARD
SCREEN_H     = BOARD + INFO_H
SWIPE_MIN    = 40           # minimum pixel distance to count as a swipe

RANKING_FILE = Path(__file__).parent / "ranking.json"

# Colour palette — mirrors the CSS custom-property values in the HTML version
C_BG         = ( 13,  13,  13)
C_SURFACE    = ( 17,  17,  22)
C_BORDER     = ( 30,  30,  46)
C_ACCENT     = (  0, 255, 136)
C_ACCENT_DIM = (  0, 120,  70)
C_DANGER     = (255,  51,  85)
C_YELLOW     = (255, 215,   0)
C_TEXT       = (170, 170, 204)
C_BRIGHT     = (238, 238, 255)
C_BLACK      = (  0,   0,   0)


# ═══════════════════════════════════════════════════════════════════
#  I18N  — bilingual string table
# ═══════════════════════════════════════════════════════════════════

LANGS = {
    "es": {
        "title":        "SNAKE",
        "by":           "by jaimefgdev",
        "speed_lbl":    "VELOCIDAD",
        "walls_lbl":    "BORDES",
        "yes":          "SÍ",
        "no":           "NO",
        "start":        "▶  COMENZAR",
        "quit":         "✕  SALIR",
        "ranking_btn":  "🏆 RANKING",
        "paused":       "⏸  PAUSA",
        "resume":       "▶  CONTINUAR",
        "restart":      "↺  REINICIAR",
        "main_menu":    "MENÚ PRINCIPAL",
        "game_over":    "GAME OVER",
        "play_again":   "▶  JUGAR DE NUEVO",
        "top10_title":  "🏆 TOP 10",
        "name_prompt":  "¡Entraste al ranking!",
        "name_prompt2": "Introduce tu nombre:",
        "name_ph":      "NOMBRE",
        "save":         "💾 GUARDAR",
        "level":        "NIVEL",
        "player":       "JUGADOR",
        "score_col":    "PTS",
        "date_col":     "FECHA",
        "no_scores":    "Sin puntuaciones aún.",
        "score_lbl":    "PUNTOS",
        "time_lbl":     "TIEMPO",
        "close":        "✕  CERRAR",
        "ranking_title":"RANKING",
    },
    "en": {
        "title":        "SNAKE",
        "by":           "by jaimefgdev",
        "speed_lbl":    "SPEED",
        "walls_lbl":    "WALLS",
        "yes":          "YES",
        "no":           "NO",
        "start":        "▶  START",
        "quit":         "✕  QUIT",
        "ranking_btn":  "🏆 RANKING",
        "paused":       "⏸  PAUSED",
        "resume":       "▶  RESUME",
        "restart":      "↺  RESTART",
        "main_menu":    "MAIN MENU",
        "game_over":    "GAME OVER",
        "play_again":   "▶  PLAY AGAIN",
        "top10_title":  "🏆 TOP 10",
        "name_prompt":  "You made the ranking!",
        "name_prompt2": "Enter your name:",
        "name_ph":      "NAME",
        "save":         "💾 SAVE",
        "level":        "LEVEL",
        "player":       "PLAYER",
        "score_col":    "PTS",
        "date_col":     "DATE",
        "no_scores":    "No scores yet.",
        "score_lbl":    "SCORE",
        "time_lbl":     "TIME",
        "close":        "✕  CLOSE",
        "ranking_title":"RANKING",
    },
}

_lang = "es"


def t(key: str) -> str:
    """Returns the localised string for *key* in the active language."""
    return LANGS[_lang].get(key, key)


def set_lang(code: str) -> None:
    global _lang
    _lang = code


# ═══════════════════════════════════════════════════════════════════
#  RANKING  — JSON persistence, one list per speed level
# ═══════════════════════════════════════════════════════════════════

def load_ranking() -> dict:
    """Reads ranking.json from disk. Returns an empty dict on any error."""
    try:
        return json.loads(RANKING_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_ranking(data: dict) -> None:
    """Writes the ranking dict to ranking.json (pretty-printed)."""
    RANKING_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_level_entries(data: dict, level: int) -> list:
    """Returns the sorted Top-10 list for *level* (may be empty)."""
    return data.get(str(level), [])


def is_top10(data: dict, level: int, score: int) -> bool:
    """Returns True if *score* qualifies for the Top-10 of *level*."""
    entries = get_level_entries(data, level)
    return len(entries) < 10 or score > (entries[-1]["score"] if entries else -1)


def add_score(data: dict, level: int, name: str, score: int, elapsed: float) -> None:
    """Inserts a new entry into the ranking and trims to Top-10."""
    key     = str(level)
    entries = data.get(key, [])
    entries.append({
        "name":  (name.strip().upper() or "???")[:12],
        "score": score,
        "time":  round(elapsed),
        "date":  datetime.date.today().strftime("%d/%m/%Y"),
    })
    entries.sort(key=lambda e: (-e["score"], e["time"]))
    data[key] = entries[:10]


# ═══════════════════════════════════════════════════════════════════
#  UTILITIES
# ═══════════════════════════════════════════════════════════════════

def speed_to_ms(speed: int) -> int:
    """Converts a speed level (1–10) to milliseconds per game tick.
    Formula is identical to the HTML version: round(540 / (s*0.88 + 0.4))."""
    return round(540 / (speed * 0.88 + 0.4))


def fmt_time(seconds: float) -> str:
    """Formats seconds as M:SS."""
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"


def load_fonts() -> dict:
    """Tries to find a monospaced system font; falls back to pygame default."""
    try:
        mono_path = pygame.font.match_font(
            "couriernew,courier,dejavusansmono,lucidaconsole,monospace"
        ) or ""
        ui_path = pygame.font.match_font(
            "rajdhani,segoeui,arialrounded,arial,helvetica"
        ) or ""
    except Exception:
        mono_path, ui_path = "", ""

    def _font(path, size):
        try:
            return pygame.font.Font(path or None, size)
        except Exception:
            return pygame.font.Font(None, size)

    return {
        "title": _font(mono_path, 68),
        "large": _font(mono_path, 42),
        "btn":   _font(mono_path, 18),
        "ui":    _font(ui_path,   21),
        "small": _font(ui_path,   19),
        "tiny":  _font(mono_path, 14),
    }


# ═══════════════════════════════════════════════════════════════════
#  RENDERING PRIMITIVES
# ═══════════════════════════════════════════════════════════════════

def draw_food(surf: pygame.Surface, gx: int, gy: int) -> None:
    """Renders a round, glowing food item with a specular highlight.
    Mirrors the HTML drawFood() approach: glow gradient → solid circle → highlight."""
    cx = gx * CELL + CELL // 2
    cy = gy * CELL + CELL // 2 + INFO_H
    fr = max(4, int(CELL * 0.38))

    # radial glow — concentric translucent circles from faint outer to brighter inner
    for step in range(9, 0, -1):
        r     = int(fr * (1.0 + step * 0.24))
        alpha = int(15 * step)
        glow  = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*C_DANGER, alpha), (r + 1, r + 1), r)
        surf.blit(glow, (cx - r - 1, cy - r - 1))

    # solid red body
    pygame.draw.circle(surf, C_DANGER, (cx, cy), fr)

    # top-left specular highlight (simulates a 3-D sheen)
    hl_r = max(2, fr // 3)
    hl   = pygame.Surface((hl_r * 2 + 1, hl_r * 2 + 1), pygame.SRCALPHA)
    pygame.draw.circle(hl, (255, 160, 160, 140), (hl_r, hl_r), hl_r)
    surf.blit(hl, (cx - fr // 2, cy - fr // 2))


def draw_snake(surf: pygame.Surface, snake: list, direction: list) -> None:
    """Renders the snake body with a head-to-tail gradient and rounded rectangles.
    Head is drawn last (on top) with the accent colour and directional eyes."""
    n = len(snake)

    # draw tail → head so that the head segment appears on top
    for i in range(n - 1, -1, -1):
        seg     = snake[i]
        is_head = (i == 0)
        sx      = seg[0] * CELL
        sy      = seg[1] * CELL + INFO_H
        pad     = 2

        if is_head:
            color = C_ACCENT
        else:
            # HTML gradient formula: alpha = max(0.22, 1 - (i/len)*0.78)
            alpha_f = max(0.22, 1.0 - (i / n) * 0.78)
            g_val   = int(140 + 115 * alpha_f)
            b_val   = int(70  * alpha_f)
            color   = (0, g_val, b_val)

        rect   = pygame.Rect(sx + pad, sy + pad, CELL - pad * 2, CELL - pad * 2)
        radius = 4 if is_head else 2
        pygame.draw.rect(surf, color, rect, border_radius=radius)

    # directional eyes on the head
    _draw_eyes(surf, snake[0], direction)


def _draw_eyes(surf: pygame.Surface, head: list, direction: list) -> None:
    """Draws two small eyes on the snake head, offset toward the movement direction.
    Matches the HTML drawEyes() placement logic."""
    dx   = direction[0]
    dy   = direction[1]
    cx   = head[0] * CELL + CELL // 2
    cy   = head[1] * CELL + CELL // 2 + INFO_H
    er   = max(2, int(CELL * 0.11))
    off  = int(CELL * 0.22)   # forward offset
    perp = int(CELL * 0.20)   # perpendicular offset

    if dx != 0:
        e1 = (cx + dx * off, cy - perp)
        e2 = (cx + dx * off, cy + perp)
    else:
        e1 = (cx - perp, cy + dy * off)
        e2 = (cx + perp, cy + dy * off)

    for ex, ey in (e1, e2):
        # dark pupil
        pygame.draw.circle(surf, (0, 26, 13), (ex, ey), er)
        # white specular dot
        hl = pygame.Surface((er * 2, er * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            hl, (255, 255, 255, 140),
            (max(1, er // 2), max(1, er // 2)),
            max(1, er // 3),
        )
        surf.blit(hl, (ex - er // 2, ey - er // 2))


def draw_grid_lines(surf: pygame.Surface) -> None:
    """Subtle dark-green grid lines matching the HTML CSS background pattern."""
    for col in range(GRID + 1):
        pygame.draw.line(surf, (0, 38, 18), (col * CELL, INFO_H), (col * CELL, SCREEN_H))
    for row in range(GRID + 1):
        y = row * CELL + INFO_H
        pygame.draw.line(surf, (0, 38, 18), (0, y), (SCREEN_W, y))


def draw_board_border(surf: pygame.Surface, walls: bool) -> None:
    """Red border when walls are ON (deadly), faint green when OFF (wrap-around)."""
    rect = pygame.Rect(0, INFO_H, BOARD, BOARD)
    if walls:
        pygame.draw.rect(surf, C_DANGER, rect, 3)
    else:
        pygame.draw.rect(surf, (0, 60, 30), rect, 1)


def draw_info_bar(surf: pygame.Surface, fonts: dict, score: int, elapsed: float) -> None:
    """Top info bar showing the live score and elapsed time."""
    pygame.draw.rect(surf, C_SURFACE, (0, 0, SCREEN_W, INFO_H))
    pygame.draw.line(surf, C_BORDER,  (0, INFO_H - 1), (SCREEN_W, INFO_H - 1), 1)

    s_surf = fonts["small"].render(f"{t('score_lbl')}: {score}", True, C_BRIGHT)
    t_surf = fonts["small"].render(f"{t('time_lbl')}: {fmt_time(elapsed)}", True, C_BRIGHT)
    mid_y  = (INFO_H - s_surf.get_height()) // 2

    surf.blit(s_surf, (14, mid_y))
    surf.blit(t_surf, (SCREEN_W - t_surf.get_width() - 14, mid_y))


def draw_pause_button(surf: pygame.Surface) -> pygame.Rect:
    """Draws the pause icon in the center of the info bar. Returns the Rect."""
    r   = pygame.Rect(SCREEN_W // 2 - 22, 8, 44, 28)
    col = C_YELLOW if r.collidepoint(pygame.mouse.get_pos()) else C_BORDER
    pygame.draw.rect(surf, col, r, 1, border_radius=3)
    bw, bh, gap = 5, 12, 3
    cx, cy = r.center
    pygame.draw.rect(surf, col, (cx - gap - bw, cy - bh // 2, bw, bh))
    pygame.draw.rect(surf, col, (cx + gap,       cy - bh // 2, bw, bh))
    return r


def draw_overlay(surf: pygame.Surface, alpha: int = 210) -> None:
    """Dims the entire screen with a translucent dark veil (for menus/pause)."""
    veil = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    veil.fill((8, 8, 14, alpha))
    surf.blit(veil, (0, 0))


# ═══════════════════════════════════════════════════════════════════
#  UI COMPONENTS
# ═══════════════════════════════════════════════════════════════════

class Button:
    """Pixel-style outlined button with hover and keyboard-selection highlight."""

    def __init__(self, cx: int, cy: int, label: str,
                 color: tuple = None, width: int = None, height: int = 36):
        self.label    = label
        self.color    = color or C_ACCENT
        self.selected = False
        self._cx      = cx
        self._cy      = cy
        self._width   = width
        self._height  = height
        self.rect     = pygame.Rect(0, 0, 0, 0)

    def draw(self, surf: pygame.Surface, font: pygame.font.Font) -> None:
        rendered = font.render(self.label, True, self.color)
        w        = self._width or rendered.get_width() + 32
        self.rect = pygame.Rect(
            self._cx - w // 2, self._cy - self._height // 2, w, self._height
        )
        hovering   = self.rect.collidepoint(pygame.mouse.get_pos()) or self.selected
        border_col = C_YELLOW if hovering else self.color

        if hovering:
            fill = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            fill.fill((*border_col, 28))
            surf.blit(fill, self.rect.topleft)

        pygame.draw.rect(surf, border_col, self.rect, 2, border_radius=2)
        txt = font.render(self.label, True, border_col)
        surf.blit(txt, txt.get_rect(center=self.rect.center))

    def hit(self, pos) -> bool:
        return self.rect.collidepoint(pos)


class SpeedSelector:
    """Row of 10 clickable squares representing the speed level (1–10)."""

    BOX   = 22
    GAP   = 5

    def __init__(self, cx: int, cy: int, initial: int = 5):
        self.value  = initial
        self._cy    = cy
        total_w     = 10 * self.BOX + 9 * self.GAP
        start_x     = cx - total_w // 2
        self.boxes  = [
            pygame.Rect(start_x + i * (self.BOX + self.GAP),
                        cy - self.BOX // 2, self.BOX, self.BOX)
            for i in range(10)
        ]

    def draw(self, surf: pygame.Surface) -> None:
        mouse = pygame.mouse.get_pos()
        for i, rect in enumerate(self.boxes):
            active  = (i + 1 == self.value)
            hovered = rect.collidepoint(mouse)
            if active:
                color = C_ACCENT
            elif hovered:
                color = tuple(min(255, c + 50) for c in C_BORDER)
            else:
                color = C_BORDER
            pygame.draw.rect(surf, color, rect, border_radius=2)

    def click(self, pos) -> bool:
        for i, rect in enumerate(self.boxes):
            if rect.collidepoint(pos):
                self.value = i + 1
                return True
        return False

    def shift(self, delta: int) -> None:
        self.value = max(1, min(10, self.value + delta))


class WallsToggle:
    """Two-button ON/OFF toggle for the walls/border option."""

    BTN_W = 56
    BTN_H = 30

    def __init__(self, cx: int, cy: int, initial: bool = True):
        self.value    = initial
        self._cx      = cx
        self._cy      = cy
        self.rect_on  = pygame.Rect(cx - self.BTN_W - 2, cy - self.BTN_H // 2,
                                    self.BTN_W, self.BTN_H)
        self.rect_off = pygame.Rect(cx + 2,               cy - self.BTN_H // 2,
                                    self.BTN_W, self.BTN_H)

    def draw(self, surf: pygame.Surface, font: pygame.font.Font) -> None:
        for rect, label, active in (
            (self.rect_on,  t("yes"), self.value),
            (self.rect_off, t("no"),  not self.value),
        ):
            bg_col  = C_ACCENT  if active else C_BORDER
            txt_col = C_BLACK   if active else C_TEXT
            pygame.draw.rect(surf, bg_col, rect, border_radius=2)
            lbl = font.render(label, True, txt_col)
            surf.blit(lbl, lbl.get_rect(center=rect.center))

    def click(self, pos) -> bool:
        if self.rect_on.collidepoint(pos):
            self.value = True
            return True
        if self.rect_off.collidepoint(pos):
            self.value = False
            return True
        return False

    def toggle(self) -> None:
        self.value = not self.value


# ═══════════════════════════════════════════════════════════════════
#  GESTURE / SWIPE TRACKER
# ═══════════════════════════════════════════════════════════════════

class GestureTracker:
    """Records the touch-start position and computes a swipe direction on release.
    Handles both mouse events (desktop) and FINGERDOWN/FINGERUP (touchscreen)."""

    def __init__(self):
        self._start = None

    def start(self, pos: tuple) -> None:
        self._start = pos

    def detect(self, pos: tuple):
        """Returns [dx, dy] cell-delta on a valid swipe, or None otherwise."""
        if self._start is None:
            return None
        dx = pos[0] - self._start[0]
        dy = pos[1] - self._start[1]
        self._start = None
        if abs(dx) < SWIPE_MIN and abs(dy) < SWIPE_MIN:
            return None
        if abs(dx) > abs(dy):
            return [1, 0] if dx > 0 else [-1, 0]
        return [0, 1] if dy > 0 else [0, -1]


# ═══════════════════════════════════════════════════════════════════
#  SCREENS
# ═══════════════════════════════════════════════════════════════════

def screen_main_menu(screen: pygame.Surface, fonts: dict,
                     saved_speed: int = 5, saved_walls: bool = True) -> tuple:
    """Main / start menu.
    Returns (speed: int, walls: bool, action: str)
    where action ∈ {'start', 'ranking', 'quit'}."""

    speed_sel = SpeedSelector(SCREEN_W // 2, 238, saved_speed)
    walls_sel = WallsToggle(SCREEN_W // 2 + 28, 312, saved_walls)

    # focus order: 0=speed, 1=walls, 2=start, 3=ranking, 4=quit
    focus = 2
    clock = pygame.time.Clock()

    # language button rects (top-left corner)
    r_es = pygame.Rect(12, 12, 46, 24)
    r_en = pygame.Rect(62, 12, 46, 24)

    while True:
        # rebuild buttons with current language text
        btn_start   = Button(SCREEN_W // 2, 390, t("start"),       C_ACCENT,  200)
        btn_ranking = Button(SCREEN_W // 2, 438, t("ranking_btn"), C_YELLOW,  200)
        btn_quit    = Button(SCREEN_W // 2, 486, t("quit"),        C_DANGER,  200)

        screen.fill(C_BG)

        # title with subtle shadow
        t_shadow = fonts["title"].render(t("title"), True, (0, 80, 38))
        t_title  = fonts["title"].render(t("title"), True, C_ACCENT)
        screen.blit(t_shadow, t_shadow.get_rect(center=(SCREEN_W // 2 + 3, 83)))
        screen.blit(t_title,  t_title.get_rect(center=(SCREEN_W // 2,     80)))

        byline = fonts["tiny"].render(t("by"), True, C_BORDER)
        screen.blit(byline, byline.get_rect(center=(SCREEN_W // 2, 114)))

        # speed selector
        spd_lbl = fonts["ui"].render(t("speed_lbl"), True, C_TEXT)
        screen.blit(spd_lbl, spd_lbl.get_rect(center=(SCREEN_W // 2, 208)))
        speed_sel.draw(screen)

        # walls toggle
        w_lbl = fonts["ui"].render(t("walls_lbl"), True, C_TEXT)
        screen.blit(w_lbl, w_lbl.get_rect(midright=(SCREEN_W // 2 - 38, walls_sel._cy)))
        walls_sel.draw(screen, fonts["ui"])

        # menu buttons
        btn_start.selected   = (focus == 2)
        btn_ranking.selected = (focus == 3)
        btn_quit.selected    = (focus == 4)
        btn_start.draw(screen,   fonts["btn"])
        btn_ranking.draw(screen, fonts["btn"])
        btn_quit.draw(screen,    fonts["btn"])

        # language switcher
        for r, code, lbl in ((r_es, "es", "ES"), (r_en, "en", "EN")):
            col = C_ACCENT if _lang == code else C_BORDER
            pygame.draw.rect(screen, col, r, 1, border_radius=2)
            lt  = fonts["tiny"].render(lbl, True, col)
            screen.blit(lt, lt.get_rect(center=r.center))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return speed_sel.value, walls_sel.value, "quit"

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if r_es.collidepoint(pos): set_lang("es")
                if r_en.collidepoint(pos): set_lang("en")
                speed_sel.click(pos)
                walls_sel.click(pos)
                if btn_start.hit(pos):   return speed_sel.value, walls_sel.value, "start"
                if btn_ranking.hit(pos): return speed_sel.value, walls_sel.value, "ranking"
                if btn_quit.hit(pos):    return speed_sel.value, walls_sel.value, "quit"

            elif event.type == pygame.KEYDOWN:
                key = event.key
                if key in (pygame.K_DOWN, pygame.K_TAB):
                    focus = (focus + 1) % 5
                elif key == pygame.K_UP:
                    focus = (focus - 1) % 5
                elif key in (pygame.K_LEFT, pygame.K_RIGHT):
                    delta = -1 if key == pygame.K_LEFT else 1
                    if focus == 0:
                        speed_sel.shift(delta)
                    elif focus == 1:
                        walls_sel.toggle()
                elif key == pygame.K_RETURN:
                    if focus == 0:    pass
                    elif focus == 1:  walls_sel.toggle()
                    elif focus == 2:  return speed_sel.value, walls_sel.value, "start"
                    elif focus == 3:  return speed_sel.value, walls_sel.value, "ranking"
                    elif focus == 4:  return speed_sel.value, walls_sel.value, "quit"
                elif key == pygame.K_ESCAPE:
                    return speed_sel.value, walls_sel.value, "quit"


def screen_pause(screen: pygame.Surface, fonts: dict,
                 score: int, elapsed: float) -> str:
    """Pause overlay drawn on top of the frozen game frame.
    Returns 'resume', 'restart', or 'menu'."""
    saved   = screen.copy()  # freeze the current game frame
    buttons = [
        Button(SCREEN_W // 2, 270, t("resume"),    C_ACCENT, 220),
        Button(SCREEN_W // 2, 326, t("restart"),   C_BRIGHT, 220),
        Button(SCREEN_W // 2, 382, t("main_menu"), C_DANGER, 220),
    ]
    results = ["resume", "restart", "menu"]
    focus   = 0
    clock   = pygame.time.Clock()

    while True:
        screen.blit(saved, (0, 0))
        draw_overlay(screen, 200)

        title = fonts["large"].render(t("paused"), True, C_YELLOW)
        screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 170)))

        info = fonts["ui"].render(
            f"{t('score_lbl')}: {score}   {t('time_lbl')}: {fmt_time(elapsed)}",
            True, C_BRIGHT,
        )
        screen.blit(info, info.get_rect(center=(SCREEN_W // 2, 216)))

        for i, btn in enumerate(buttons):
            btn.selected = (i == focus)
            btn.draw(screen, fonts["btn"])

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, btn in enumerate(buttons):
                    if btn.hit(event.pos): return results[i]
            elif event.type == pygame.KEYDOWN:
                k = event.key
                if k in (pygame.K_ESCAPE, pygame.K_SPACE): return "resume"
                elif k == pygame.K_UP:                     focus = (focus - 1) % 3
                elif k == pygame.K_DOWN:                   focus = (focus + 1) % 3
                elif k == pygame.K_RETURN:                 return results[focus]


def screen_enter_name(screen: pygame.Surface, fonts: dict,
                      score: int, elapsed: float) -> str:
    """Name-entry dialog shown when the player achieves a Top-10 score.
    Returns the entered name (uppercase, max 12 chars)."""
    saved        = screen.copy()
    name         = ""
    cursor_vis   = True
    cursor_timer = 0
    clock        = pygame.time.Clock()

    while True:
        screen.blit(saved, (0, 0))
        draw_overlay(screen, 235)

        title = fonts["large"].render(t("top10_title"), True, C_YELLOW)
        screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 158)))

        p1 = fonts["ui"].render(t("name_prompt"),  True, C_YELLOW)
        p2 = fonts["ui"].render(t("name_prompt2"), True, C_TEXT)
        screen.blit(p1, p1.get_rect(center=(SCREEN_W // 2, 208)))
        screen.blit(p2, p2.get_rect(center=(SCREEN_W // 2, 236)))

        # input box
        box = pygame.Rect(SCREEN_W // 2 - 118, 262, 236, 40)
        pygame.draw.rect(screen, C_SURFACE, box, border_radius=2)
        pygame.draw.rect(screen, C_ACCENT,  box, 2, border_radius=2)

        display = (name + ("|" if cursor_vis else " "))
        inp_txt = fonts["btn"].render(display, True, C_ACCENT)
        screen.blit(inp_txt, inp_txt.get_rect(center=box.center))

        # save button
        btn_save = Button(SCREEN_W // 2, 334, t("save"), C_ACCENT, 200)
        btn_save.draw(screen, fonts["btn"])

        pygame.display.flip()
        dt            = clock.tick(60)
        cursor_timer += dt
        if cursor_timer >= 530:
            cursor_vis   = not cursor_vis
            cursor_timer = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_save.hit(event.pos):
                    return name.strip() or "???"
            elif event.type == pygame.KEYDOWN:
                k = event.key
                if k == pygame.K_RETURN:
                    return name.strip() or "???"
                elif k == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif len(name) < 12 and event.unicode.isprintable() and event.unicode:
                    name += event.unicode.upper()


def screen_game_over(screen: pygame.Surface, fonts: dict,
                     score: int, elapsed: float) -> str:
    """Game-over overlay shown after the player dies.
    Returns 'restart', 'ranking', or 'menu'."""
    saved   = screen.copy()
    buttons = [
        Button(SCREEN_W // 2, 300, t("play_again"),  C_ACCENT,  220),
        Button(SCREEN_W // 2, 354, t("ranking_btn"), C_YELLOW,  220),
        Button(SCREEN_W // 2, 408, t("main_menu"),   C_DANGER,  220),
    ]
    results = ["restart", "ranking", "menu"]
    focus   = 0
    clock   = pygame.time.Clock()

    while True:
        screen.blit(saved, (0, 0))
        draw_overlay(screen, 235)

        title = fonts["large"].render(t("game_over"), True, C_DANGER)
        screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 172)))

        info = fonts["ui"].render(
            f"{t('score_lbl')}: {score}   {t('time_lbl')}: {fmt_time(elapsed)}",
            True, C_BRIGHT,
        )
        screen.blit(info, info.get_rect(center=(SCREEN_W // 2, 222)))

        for i, btn in enumerate(buttons):
            btn.selected = (i == focus)
            btn.draw(screen, fonts["btn"])

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, btn in enumerate(buttons):
                    if btn.hit(event.pos): return results[i]
            elif event.type == pygame.KEYDOWN:
                k = event.key
                if k == pygame.K_ESCAPE:  return "menu"
                elif k == pygame.K_UP:    focus = (focus - 1) % 3
                elif k == pygame.K_DOWN:  focus = (focus + 1) % 3
                elif k == pygame.K_RETURN: return results[focus]


def screen_ranking(screen: pygame.Surface, fonts: dict,
                   ranking_data: dict, initial_level: int) -> None:
    """Full-screen ranking browser with level tabs (1–10).
    Uses ◀ / ▶ buttons and arrow-key navigation."""
    level = initial_level
    clock = pygame.time.Clock()

    TAB_W, TAB_H, TAB_GAP = 36, 22, 4
    TABS_TOTAL = 10 * TAB_W + 9 * TAB_GAP
    TAB_X0     = (SCREEN_W - TABS_TOTAL) // 2
    TAB_Y      = 112

    while True:
        screen.fill(C_BG)
        draw_overlay(screen, 245)

        # title
        title = fonts["large"].render(t("ranking_title"), True, C_YELLOW)
        screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 50)))

        # active level label
        lv_txt = fonts["ui"].render(f"{t('level')} {level}", True, C_YELLOW)
        screen.blit(lv_txt, lv_txt.get_rect(center=(SCREEN_W // 2, 86)))

        # tab row
        tab_rects = []
        for i in range(10):
            r = pygame.Rect(TAB_X0 + i * (TAB_W + TAB_GAP), TAB_Y, TAB_W, TAB_H)
            tab_rects.append(r)
            active = (i + 1 == level)
            bc     = C_YELLOW if active else C_BORDER
            tc     = C_YELLOW if active else C_TEXT
            pygame.draw.rect(screen, bc, r, 1, border_radius=2)
            lt = fonts["tiny"].render(str(i + 1), True, tc)
            screen.blit(lt, lt.get_rect(center=r.center))

        # table
        entries = get_level_entries(ranking_data, level)
        row_y   = TAB_Y + TAB_H + 18

        if not entries:
            no_txt = fonts["ui"].render(t("no_scores"), True, C_BORDER)
            screen.blit(no_txt, no_txt.get_rect(center=(SCREEN_W // 2, row_y + 44)))
        else:
            # header row
            COL_X = [24, 68, 286, 376]
            for cx, hdr in zip(COL_X, ("#", t("player"), t("score_col"), t("date_col"))):
                h_surf = fonts["tiny"].render(hdr, True, C_TEXT)
                screen.blit(h_surf, (cx, row_y))
            pygame.draw.line(screen, C_BORDER,
                             (14, row_y + 17), (SCREEN_W - 14, row_y + 17))
            row_y += 22

            MEDALS = ["🥇", "🥈", "🥉"]
            for idx, entry in enumerate(entries):
                if row_y > SCREEN_H - 72:
                    break
                if   idx == 0: row_col = C_YELLOW
                elif idx == 1: row_col = (187, 187, 187)
                elif idx == 2: row_col = (205, 127, 50)
                else:          row_col = C_TEXT

                rank_str = MEDALS[idx] if idx < 3 else str(idx + 1)
                cells    = [rank_str, entry["name"],
                            str(entry["score"]), entry.get("date", "-")]
                for cx, cell in zip(COL_X, cells):
                    c_surf = fonts["tiny"].render(cell, True, row_col)
                    screen.blit(c_surf, (cx, row_y))
                row_y += 22

        # navigation buttons
        btn_prev  = Button(54,           SCREEN_H - 32, "◀", C_TEXT, 44, 26)
        btn_next  = Button(SCREEN_W - 54, SCREEN_H - 32, "▶", C_TEXT, 44, 26)
        btn_close = Button(SCREEN_W // 2, SCREEN_H - 32, t("close"), C_TEXT, 180, 26)
        btn_prev.draw(screen,  fonts["btn"])
        btn_next.draw(screen,  fonts["btn"])
        btn_close.draw(screen, fonts["btn"])

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                for i, tr in enumerate(tab_rects):
                    if tr.collidepoint(pos):
                        level = i + 1
                if btn_prev.hit(pos):  level = max(1,  level - 1)
                if btn_next.hit(pos):  level = min(10, level + 1)
                if btn_close.hit(pos): return
            elif event.type == pygame.KEYDOWN:
                k = event.key
                if k == pygame.K_ESCAPE:          return
                elif k == pygame.K_LEFT:  level = max(1,  level - 1)
                elif k == pygame.K_RIGHT: level = min(10, level + 1)


# ═══════════════════════════════════════════════════════════════════
#  GAME LOOP
# ═══════════════════════════════════════════════════════════════════

def run_game(screen: pygame.Surface, fonts: dict,
             speed: int, walls: bool) -> tuple:
    """Runs one game session.
    Returns (result: str, score: int, elapsed: float)
    where result ∈ {'gameover', 'restart', 'menu'}.

    Timing: the snake advances every speed_to_ms(speed) milliseconds,
    independent of the render framerate (capped at 120 fps)."""

    mid    = GRID // 2
    snake  = [[mid, mid], [mid - 1, mid], [mid - 2, mid]]
    direc  = [1, 0]   # current direction [dx, dy] in grid cells
    d_buf  = []       # input queue — max 2 pending turns (prevents missed inputs)

    def spawn_food():
        while True:
            pos = [random.randint(0, GRID - 1), random.randint(0, GRID - 1)]
            if pos not in snake:
                return pos

    food        = spawn_food()
    score       = 0
    tick_ms     = speed_to_ms(speed)
    last_tick   = pygame.time.get_ticks()
    start_ms    = pygame.time.get_ticks()
    pause_total = 0   # cumulative paused milliseconds (excluded from elapsed)
    gestures    = GestureTracker()
    clock       = pygame.time.Clock()

    def change_dir(dx, dy):
        """Queues a direction change, rejecting 180° reversals and duplicates."""
        ref = d_buf[-1] if d_buf else direc
        if [dx, dy] == [-ref[0], -ref[1]]: return
        if [dx, dy] == ref:                return
        if len(d_buf) < 2:
            d_buf.append([dx, dy])

    while True:
        now     = pygame.time.get_ticks()
        elapsed = (now - start_ms - pause_total) / 1000

        # ── event handling ─────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pause_rect = pygame.Rect(SCREEN_W // 2 - 22, 8, 44, 28)
                if pause_rect.collidepoint(event.pos):
                    pause_start = pygame.time.get_ticks()
                    result = screen_pause(screen, fonts, score, elapsed)
                    pause_total += pygame.time.get_ticks() - pause_start
                    last_tick    = pygame.time.get_ticks()
                    if result != "resume":
                        return result, score, elapsed
                else:
                    gestures.start(event.pos)

            elif event.type == pygame.MOUSEBUTTONUP:
                swipe = gestures.detect(event.pos)
                if swipe:
                    change_dir(*swipe)

            # native touch events (tablet / mobile / touch-enabled displays)
            elif event.type == pygame.FINGERDOWN:
                gestures.start((int(event.x * SCREEN_W), int(event.y * SCREEN_H)))
            elif event.type == pygame.FINGERUP:
                swipe = gestures.detect((int(event.x * SCREEN_W), int(event.y * SCREEN_H)))
                if swipe:
                    change_dir(*swipe)

            elif event.type == pygame.KEYDOWN:
                k = event.key
                if k == pygame.K_SPACE:
                    pause_start = pygame.time.get_ticks()
                    result = screen_pause(screen, fonts, score, elapsed)
                    pause_total += pygame.time.get_ticks() - pause_start
                    last_tick    = pygame.time.get_ticks()
                    if result != "resume":
                        return result, score, elapsed
                elif k in (pygame.K_UP,    pygame.K_w): change_dir( 0, -1)
                elif k in (pygame.K_DOWN,  pygame.K_s): change_dir( 0,  1)
                elif k in (pygame.K_LEFT,  pygame.K_a): change_dir(-1,  0)
                elif k in (pygame.K_RIGHT, pygame.K_d): change_dir( 1,  0)

        # ── game tick (speed-controlled) ────────────────────────────
        if pygame.time.get_ticks() - last_tick >= tick_ms:
            last_tick = pygame.time.get_ticks()

            if d_buf:
                direc = d_buf.pop(0)

            head = [snake[0][0] + direc[0], snake[0][1] + direc[1]]

            if walls:
                if not (0 <= head[0] < GRID and 0 <= head[1] < GRID):
                    return "gameover", score, elapsed
            else:
                head[0] %= GRID
                head[1] %= GRID

            if head in snake:
                return "gameover", score, elapsed

            snake.insert(0, head)
            if head == food:
                score += 1
                food   = spawn_food()
            else:
                snake.pop()

        # ── render ─────────────────────────────────────────────────
        screen.fill(C_BG)
        draw_grid_lines(screen)
        draw_food(screen, food[0], food[1])
        draw_snake(screen, snake, direc)
        draw_board_border(screen, walls)
        draw_info_bar(screen, fonts, score, elapsed)
        draw_pause_button(screen)
        pygame.display.flip()
        clock.tick(120)  # high framerate for responsive input; tick logic is time-based


# ═══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("SnakeGame by jaimefgdev")
    fonts        = load_fonts()
    ranking_data = load_ranking()

    speed = 5
    walls = True

    while True:
        # ── main menu ──────────────────────────────────────────────
        speed, walls, action = screen_main_menu(screen, fonts, speed, walls)

        if action == "quit":
            break

        if action == "ranking":
            screen_ranking(screen, fonts, ranking_data, speed)
            continue

        # ── game session loop (restart keeps the same settings) ────
        keep_playing = True
        while keep_playing:
            result, score, elapsed = run_game(screen, fonts, speed, walls)

            if result == "restart":
                continue   # play again with same settings

            if result == "menu":
                keep_playing = False
                break

            if result == "gameover":
                # check for Top-10 entry
                if is_top10(ranking_data, speed, score):
                    name = screen_enter_name(screen, fonts, score, elapsed)
                    add_score(ranking_data, speed, name, score, elapsed)
                    save_ranking(ranking_data)

                # game-over screen with optional ranking detour
                show_go = True
                while show_go:
                    go_action = screen_game_over(screen, fonts, score, elapsed)
                    if go_action == "ranking":
                        screen_ranking(screen, fonts, ranking_data, speed)
                        # return to game-over screen after viewing ranking
                    else:
                        show_go = False
                        if go_action == "menu":
                            keep_playing = False
                        # else go_action == "restart" → keep_playing remains True

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
