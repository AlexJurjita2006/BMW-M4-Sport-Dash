import math
import sys
import socket
import json
import os
import time
import pygame

# --- LOAD CONFIGURATION ---
config_path = os.path.join(os.path.dirname(__file__), "config.json")
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)
    WIDTH, HEIGHT = config.get("sport_width", 1000), config.get("sport_height", 700)
else:
    WIDTH, HEIGHT = 1000, 700

# ─── DRIVE MODES ────────────────────────────────────────────────────────────
DRIVE_MODES = ["ECO PRO", "COMFORT", "SPORT", "SPORT +", "M TRACK"]

MODE_COLORS = {
    "ECO PRO":  (0,   210, 100),
    "COMFORT":  (80,  150, 255),
    "SPORT":    (0,   210, 255),
    "SPORT +":  (255, 140,  30),
    "M TRACK":  (220,  50,  50),
}

MODE_TRAIL = {                          # (dark_end, light_end)
    "ECO PRO":  ((0,  100,  50), (0,  210, 100)),
    "COMFORT":  ((30,  60, 140), (80, 150, 255)),
    "SPORT":    ((0,   90, 140), (0,  210, 255)),
    "SPORT +":  ((140, 70,   0), (255,150,  30)),
    "M TRACK":  ((140, 20,  20), (220, 50,  50)),
}

MODE_FUEL_MULT = {
    "ECO PRO": 0.72,
    "COMFORT": 0.88,
    "SPORT":   1.00,
    "SPORT +": 1.18,
    "M TRACK": 1.35,
}

# ─── COLORS ─────────────────────────────────────────────────────────────────
BG         = (2,   2,   4)
WHITE      = (244, 246, 250)
SOFT_WHITE = (200, 208, 220)
TICK_DARK  = (55,  60,  72)
RIM_DARK   = (12,  14,  18)
RIM_MID    = (42,  46,  54)
RIM_LIGHT  = (95, 100, 115)
FACE_DARK  = (3,   4,   6)
NEEDLE_TIP = (230, 55,  45)

# ─── INIT ────────────────────────────────────────────────────────────────────
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("BMW M4 — Sport Display")

# ─── UDP ─────────────────────────────────────────────────────────────────────
udp_ip   = "127.0.0.1"
udp_port = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((udp_ip, udp_port))
sock.setblocking(False)


def sf(base):
    return max(8, int(base * min(WIDTH / 1000, HEIGHT / 700)))


font_num      = pygame.font.SysFont("segoeui",  sf(30), bold=True)
font_unit     = pygame.font.SysFont("segoeui",  sf(44), bold=True)
font_title    = pygame.font.SysFont("segoeui",  sf(38), bold=True)
font_mode_lg  = pygame.font.SysFont("segoeui",  sf(28), bold=True)
font_small    = pygame.font.SysFont("segoeui",  sf(16))
font_fuel     = pygame.font.SysFont("consolas", sf(42), bold=True)
font_fuel_un  = pygame.font.SysFont("segoeui",  sf(15))
font_rpm      = pygame.font.SysFont("consolas", sf(26), bold=True)
font_cap      = pygame.font.SysFont("segoeui",  sf(9),  bold=True)

START_DEG = 220
END_DEG   = -40
SWEEP     = START_DEG - END_DEG

# ─── cached background surface ───────────────────────────────────────────────
_grid_surf = None


def get_grid_surface():
    """Returns a pre-computed vignette (dark edges, clean center) — no grid lines."""
    global _grid_surf
    if _grid_surf is not None:
        return _grid_surf
    s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    cx, cy = WIDTH // 2, HEIGHT // 2
    max_r  = int(math.hypot(cx, cy))
    for r in range(max_r, 0, -4):
        t = r / max_r
        a = int((1.0 - t) * 0)   # no vignette darkening — just clean black
        # intentionally empty: we keep surface transparent for pure-black BG
    _grid_surf = s
    return s


def draw_vignette():
    """Soft radial vignette — darkens screen edges like a real cluster."""
    v = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    cx, cy   = WIDTH // 2, HEIGHT // 2
    max_r    = int(math.hypot(cx, cy))
    for r in range(max_r, max_r - 140, -4):
        t = (max_r - r) / 140.0
        a = int(t * 90)
        pygame.draw.circle(v, (0, 0, 0, a), (cx, cy), r, 4)
    screen.blit(v, (0, 0))


def draw_ambient_glow(cx, cy, radius, color):
    pass  # disabled — no color ring around gauges


def value_to_angle(value, max_value):
    ratio = max(0.0, min(value / max(max_value, 1), 1.0))
    return math.radians(START_DEG - ratio * SWEEP)


# ─── SCANLINES (F10: disabled — clean LCD look) ─────────────────────────────
def draw_scanlines():
    pass  # BMW F10 cluster has no scanlines


# ─── HUD CORNER BRACKETS (F10: bottom thin accent line only) ────────────────
def draw_corner_hud(color):
    """F10-style: single thin colored accent line at bottom of screen."""
    pygame.draw.line(screen, color,           (0, HEIGHT - 2), (WIDTH, HEIGHT - 2), 2)
    gw = pygame.Surface((WIDTH, 2), pygame.SRCALPHA)
    pygame.draw.rect(gw, (*color, 60), (0, 0, WIDTH, 2))
    screen.blit(gw, (0, HEIGHT - 4))


# ─── TOP INFO BAR (F10: clean minimal band) ──────────────────────────────────
def draw_top_bar(mode):
    mc       = MODE_COLORS[mode]
    bar_h    = sf(32)
    # very dark translucent band
    band = pygame.Surface((WIDTH, bar_h), pygame.SRCALPHA)
    pygame.draw.rect(band, (4, 4, 8, 210), (0, 0, WIDTH, bar_h))
    screen.blit(band, (0, 0))
    # thin bottom border in mode color
    pygame.draw.line(screen, mc, (0, bar_h), (WIDTH, bar_h), 1)
    gline = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
    pygame.draw.rect(gline, (*mc, 40), (0, 0, WIDTH, 1))
    screen.blit(gline, (0, bar_h + 1))

    title_fnt = pygame.font.SysFont("segoeui", sf(13))
    title_s   = title_fnt.render("B M W   M 4   ·   S 5 8   ·   3 . 0 T   B I T U R B O", True, (42, 50, 65))
    screen.blit(title_s, (WIDTH // 2 - title_s.get_width() // 2, sf(9)))

    odo_fnt = pygame.font.SysFont("consolas", sf(12))
    odo_s   = odo_fnt.render("ODO  24 318 km", True, (38, 46, 60))
    screen.blit(odo_s, (sf(14), sf(10)))

    trip_s = odo_fnt.render(time.strftime("%H : %M"), True, (52, 62, 78))
    screen.blit(trip_s, (WIDTH - trip_s.get_width() - sf(14), sf(10)))


# ─── BEZEL (invisible: just black face + faint shadow) ───────────────────────
def draw_bezel(cx, cy, radius, glow_color):
    # Faint drop-shadow only — no visible ring
    shd = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(4, 0, -1):
        pygame.draw.circle(shd, (0, 0, 0, 8), (cx + 2, cy + 3), radius + i, 1)
    screen.blit(shd, (0, 0))
    # Pure black face
    pygame.draw.circle(screen, FACE_DARK, (cx, cy), radius)


# ─── TRAIL (digital LED segments) ───────────────────────────────────────────
def draw_trail(cx, cy, radius, value, max_value, trail_dark, trail_light):
    """Discrete LED-bar segments — digital look, red fill that grows with the needle."""
    ratio       = max(0.0, min(value / max(max_value, 1), 1.0))
    current_deg = START_DEG - ratio * SWEEP   # float for smooth threshold

    SEG_SPAN  = 4.0   # degrees each lit segment occupies
    GAP_SPAN  = 1.5   # degrees gap between segments
    STEP      = SEG_SPAN + GAP_SPAN

    arc_r   = radius - 13   # centre radius of the band
    seg_w   = sf(7)         # radial width of each segment block
    r_inner = arc_r - seg_w // 2
    r_outer = arc_r + seg_w // 2

    # Dim (unlit) segment color
    DIM_COL  = (22, 10, 8)
    DIM_EDGE = (30, 14, 12)

    # Lit segment colors
    RED_START = (160, 20, 12)   # dim end (right / high value end)
    RED_END   = (255, 50, 38)   # bright end (left / low value start)

    glow_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    deg = float(END_DEG)
    while deg < START_DEG:
        seg_end = deg + SEG_SPAN
        seg_mid = deg + SEG_SPAN / 2.0

        # Is this segment lit? (its midpoint is "behind" the needle)
        lit = seg_mid >= current_deg

        # Position ratio along full sweep for color gradient
        t = (seg_mid - END_DEG) / SWEEP   # 0 = right/high, 1 = left/low

        if lit:
            rc = int(RED_START[0] + (RED_END[0] - RED_START[0]) * t)
            gc = int(RED_START[1] + (RED_END[1] - RED_START[1]) * t)
            bc = int(RED_START[2] + (RED_END[2] - RED_START[2]) * t)
            col = (rc, gc, bc)
        else:
            col = DIM_COL

        # Build a tiny quadrilateral for the segment
        a0 = math.radians(deg + 0.3)
        a1 = math.radians(min(seg_end - 0.3, seg_end))
        pts = [
            (cx + r_inner * math.cos(a0), cy - r_inner * math.sin(a0)),
            (cx + r_outer * math.cos(a0), cy - r_outer * math.sin(a0)),
            (cx + r_outer * math.cos(a1), cy - r_outer * math.sin(a1)),
            (cx + r_inner * math.cos(a1), cy - r_inner * math.sin(a1)),
        ]

        pygame.draw.polygon(screen, col, pts)

        # Thin bright edge on lit segments
        if lit:
            pygame.draw.polygon(screen, (min(255, rc + 60), min(255, gc + 25), min(255, bc + 25)), pts, 1)
            # Glow halo
            a_mid = math.radians(seg_mid)
            ca_m, sa_m = math.cos(a_mid), math.sin(a_mid)
            for g in range(5, 0, -1):
                ga = int(38 * (g / 5))
                x_g = int(cx + arc_r * ca_m)
                y_g = int(cy - arc_r * sa_m)
                pygame.draw.circle(glow_surf, (rc, gc // 2, bc // 2, ga), (x_g, y_g), g + 2)
        else:
            # thin dim border
            pygame.draw.polygon(screen, DIM_EDGE, pts, 1)

        deg += STEP

    screen.blit(glow_surf, (0, 0))


# ─── TICKS & NUMBERS (F10: precise, clean, thin) ────────────────────────────
def draw_ticks_and_numbers(cx, cy, radius, max_value, major_step):
    """F10-style ticks: long thin majors, very short minors, clean white nums."""
    minor_step  = major_step // 4
    # intermediate half-step
    half_step   = major_step // 2
    tick_outer  = radius - 26        # ticks start just inside the arc band
    for v in range(0, int(max_value) + 1, minor_step):
        a   = value_to_angle(v, max_value)
        ca  = math.cos(a)
        sa  = math.sin(a)
        major = (v % major_step == 0)
        half  = (not major) and (v % half_step == 0)

        if major:
            length, thick, col = sf(22), 2, (230, 232, 238)
        elif half:
            length, thick, col = sf(14), 1, (90, 96, 110)
        else:
            length, thick, col = sf(8),  1, TICK_DARK

        inner = tick_outer - length
        pygame.draw.line(screen, col,
                         (int(cx + inner    * ca), int(cy - inner    * sa)),
                         (int(cx + tick_outer * ca), int(cy - tick_outer * sa)), thick)

        if major:
            num_fnt = pygame.font.SysFont("segoeui", sf(26), bold=False)
            txt = num_fnt.render(str(int(v)), True, (215, 218, 228))
            lr  = radius - 72
            screen.blit(txt, (int(cx + lr * ca - txt.get_width()  // 2),
                               int(cy - lr * sa - txt.get_height() // 2)))


# ─── BAR NEEDLE — mini arrow marker sitting inside the LED arc band ──────────
def draw_bar_needle(cx, cy, radius, value, max_value, tip_color=None):
    """Draws a small arrow/chevron marker directly on the arc bar at the current value."""
    if tip_color is None:
        tip_color = NEEDLE_TIP

    a    = value_to_angle(value, max_value)
    ca   = math.cos(a)
    sa   = math.sin(a)
    # perpendicular direction along the arc (tangent)
    pa   = a + math.pi / 2
    cpa  = math.cos(pa)
    spa  = math.sin(pa)

    # Bar geometry matches draw_trail
    arc_r   = radius - 13
    seg_w   = sf(7)
    r_inner = arc_r - seg_w // 2 - sf(3)
    r_outer = arc_r + seg_w // 2 + sf(3)

    # Arrow tip points outward (toward outer edge), base at inner edge
    tip_x   = cx + r_outer * ca;   tip_y  = cy - r_outer * sa
    base_cx = cx + r_inner * ca;   base_cy = cy - r_inner * sa

    wing = sf(5)   # half-width of the arrow base
    bl_x = base_cx + cpa * wing;   bl_y = base_cy - spa * wing
    br_x = base_cx - cpa * wing;   br_y = base_cy + spa * wing

    arrow_pts = [(tip_x, tip_y), (bl_x, bl_y), (br_x, br_y)]

    # Glow halo
    g_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for g in range(6, 0, -1):
        ag = int(50 * (g / 6))
        pts_i = [(int(tip_x), int(tip_y)), (int(bl_x), int(bl_y)), (int(br_x), int(br_y))]
        pygame.draw.polygon(g_surf, (*tip_color, ag), pts_i, g + 1)
    screen.blit(g_surf, (0, 0))

    # Filled white arrow
    pygame.draw.polygon(screen, (255, 255, 255),
                        [(int(tip_x), int(tip_y)), (int(bl_x), int(bl_y)), (int(br_x), int(br_y))])
    # Colored outline
    pygame.draw.polygon(screen, tip_color,
                        [(int(tip_x), int(tip_y)), (int(bl_x), int(bl_y)), (int(br_x), int(br_y))], 1)


# ─── FULL GAUGE (F10: ambient + bezel + arc + ticks + slim needle) ───────────
def draw_gauge(cx, cy, radius, value, max_value, unit, title, major_step, mode):
    td, tl   = MODE_TRAIL[mode]
    gc       = MODE_COLORS[mode]
    draw_ambient_glow(cx, cy, radius, gc)
    draw_bezel(cx, cy, radius, gc)
    draw_trail(cx, cy, radius, value, max_value, td, tl)
    draw_ticks_and_numbers(cx, cy, radius, max_value, major_step)
    draw_bar_needle(cx, cy, radius, value, max_value, tip_color=(225, 38, 30))

    # Unit label — small, clean, below centre
    u_fnt = pygame.font.SysFont("segoeui", sf(16), bold=False)
    u = u_fnt.render(unit, True, (90, 96, 110))
    screen.blit(u, (cx - u.get_width() // 2, cy + sf(44)))

    # Title label below gauge
    t_fnt = pygame.font.SysFont("segoeui", sf(14))
    t = t_fnt.render(title.upper(), True, (48, 54, 68))
    screen.blit(t, (cx - t.get_width() // 2, cy + radius + sf(18)))


# ─── SEPARATOR LINE helper ────────────────────────────────────────────────────
def _sep(px, pw, y, col=(22, 26, 36)):
    pygame.draw.line(screen, col, (px + sf(10), y), (px + pw - sf(10), y), 1)


# ─── CENTER PANEL (F10 iDrive LCD style) ─────────────────────────────────────
def draw_center_panel(cx, cy, mode, fuel_l100, rpm, speed):
    pw = sf(172)
    ph = sf(310)
    px = cx - pw // 2
    py = cy - ph // 2 - sf(10)
    mc = MODE_COLORS[mode]

    # ── Panel body ────────────────────────────────────────────────────────
    ps = pygame.Surface((pw, ph), pygame.SRCALPHA)
    pygame.draw.rect(ps, (5, 6, 10, 230), (0, 0, pw, ph), border_radius=sf(10))
    screen.blit(ps, (px, py))
    # thin top bar in mode color
    pygame.draw.rect(screen, mc, (px, py, pw, sf(3)), border_radius=sf(3))
    # thin border
    brd = pygame.Surface((pw, ph), pygame.SRCALPHA)
    pygame.draw.rect(brd, (*mc, 55), (0, 0, pw, ph), 1, border_radius=sf(10))
    screen.blit(brd, (px, py))

    cursor_y = py + sf(10)

    # ── Clock ────────────────────────────────────────────────────────────
    clk_fnt  = pygame.font.SysFont("consolas", sf(20), bold=True)
    clk_surf = clk_fnt.render(time.strftime("%H:%M:%S"), True, (68, 80, 100))
    screen.blit(clk_surf, (cx - clk_surf.get_width() // 2, cursor_y))
    cursor_y += clk_surf.get_height() + sf(6)

    # ── SPORT + badge ─────────────────────────────────────────────────────
    _sep(px, pw, cursor_y, (18, 22, 32))
    cursor_y += sf(5)

    drv_lbl_fnt  = pygame.font.SysFont("segoeui", sf(9))
    drv_mode_fnt = pygame.font.SysFont("segoeui", sf(24), bold=True)
    drv_lbl_surf  = drv_lbl_fnt.render("DRIVE MODE", True, (55, 65, 82))
    drv_mode_surf = drv_mode_fnt.render(mode, True, mc)

    badge_pad = sf(8)
    badge_w   = max(drv_mode_surf.get_width(), drv_lbl_surf.get_width()) + badge_pad * 2
    badge_h   = drv_lbl_surf.get_height() + drv_mode_surf.get_height() + sf(8)
    badge_x   = cx - badge_w // 2

    bdg = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
    pygame.draw.rect(bdg, (*mc, 14),  (0, 0, badge_w, badge_h), border_radius=sf(5))
    pygame.draw.rect(bdg, (*mc, 100), (0, 0, badge_w, badge_h), 1, border_radius=sf(5))
    screen.blit(bdg, (badge_x, cursor_y))
    screen.blit(drv_lbl_surf,
                (cx - drv_lbl_surf.get_width() // 2,  cursor_y + sf(3)))
    screen.blit(drv_mode_surf,
                (cx - drv_mode_surf.get_width() // 2,
                 cursor_y + drv_lbl_surf.get_height() + sf(4)))
    # bottom glow line
    gw = pygame.Surface((badge_w, sf(2)), pygame.SRCALPHA)
    pygame.draw.rect(gw, (*mc, 80), (0, 0, badge_w, sf(2)))
    screen.blit(gw, (badge_x, cursor_y + badge_h - sf(2)))
    cursor_y += badge_h + sf(8)

    # ── Bluetooth device ─────────────────────────────────────────────────
    _sep(px, pw, cursor_y)
    cursor_y += sf(6)
    BT_BLUE  = (30, 180, 255)
    dev_fnt  = pygame.font.SysFont("segoeui", sf(13), bold=True)
    dev_surf = dev_fnt.render("Galaxy S25 Ultra", True, (160, 168, 185))
    bih = dev_surf.get_height() // 2
    total_w  = bih + sf(5) + dev_surf.get_width()
    bix = cx - total_w // 2 + bih // 2
    biy = cursor_y + bih
    def _bt(sx, sy, sh, col):
        pygame.draw.line(screen, col, (sx, sy - sh), (sx, sy + sh), 2)
        pygame.draw.line(screen, col, (sx, sy - sh), (int(sx + sh*0.65), int(sy - sh*0.33)), 2)
        pygame.draw.line(screen, col, (int(sx + sh*0.65), int(sy - sh*0.33)), (sx, sy), 2)
        pygame.draw.line(screen, col, (sx, sy), (int(sx + sh*0.65), int(sy + sh*0.33)), 2)
        pygame.draw.line(screen, col, (int(sx + sh*0.65), int(sy + sh*0.33)), (sx, sy + sh), 2)
    _bt(bix, biy, bih, BT_BLUE)
    screen.blit(dev_surf, (bix + bih // 2 + sf(6), biy - dev_surf.get_height() // 2))
    cursor_y += dev_surf.get_height() + sf(8)

    # ── Instant Fuel ─────────────────────────────────────────────────────
    _sep(px, pw, cursor_y)
    cursor_y += sf(4)
    flbl_fnt = pygame.font.SysFont("segoeui", sf(10))
    flbl = flbl_fnt.render("INSTANT FUEL", True, (50, 60, 78))
    screen.blit(flbl, (cx - flbl.get_width() // 2, cursor_y))
    cursor_y += flbl.get_height() + sf(2)

    if speed > 3:
        fstr, fun = f"{fuel_l100:04.1f}", "L / 100km"
    else:
        fstr, fun = f"{fuel_l100 * 0.08:.1f}", "L / h"
    fval_fnt = pygame.font.SysFont("consolas", sf(34), bold=True)
    fval = fval_fnt.render(fstr, True, mc)
    screen.blit(fval, (cx - fval.get_width() // 2, cursor_y))
    cursor_y += fval.get_height()
    fun_fnt = pygame.font.SysFont("segoeui", sf(12))
    fun_surf = fun_fnt.render(fun, True, (70, 80, 98))
    screen.blit(fun_surf, (cx - fun_surf.get_width() // 2, cursor_y))
    cursor_y += fun_surf.get_height() + sf(6)

    # ── RPM readout ───────────────────────────────────────────────────────
    _sep(px, pw, cursor_y)
    cursor_y += sf(5)
    rpm_fnt = pygame.font.SysFont("consolas", sf(21), bold=True)
    rpm_s   = rpm_fnt.render(f"{int(rpm):,}".replace(",", " ") + "  rpm", True, (100, 108, 125))
    screen.blit(rpm_s, (cx - rpm_s.get_width() // 2, cursor_y))




# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    clock = pygame.time.Clock()
    running = True

    current_hp     = 0.0
    current_torque = 0.0
    current_rpm    = 0.0
    current_speed  = 0.0
    display_hp     = 0.0
    display_torque = 0.0

    max_gauge_val = 480.0

    while running:
        screen.fill(BG)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        try:
            while True:
                data, _ = sock.recvfrom(1024)
                tel = json.loads(data.decode())
                current_hp     = tel.get("hp",    0)
                current_torque = tel.get("torque", 0)
                current_rpm    = tel.get("rpm",    0)
                current_speed  = tel.get("speed",  0)
        except BlockingIOError:
            pass
        except Exception:
            pass

        display_hp     += (current_hp     - display_hp)     * 0.14
        display_torque += (current_torque - display_torque) * 0.14

        mode      = "SPORT +"
        fuel_mult = MODE_FUEL_MULT[mode]
        hp_ratio  = max(0.0, display_hp / 503.0)
        rpm_ratio = max(0.0, min(current_rpm / 7200.0, 1.0))
        instant_fuel = (8.0 + (hp_ratio ** 1.2) * 32.0 + rpm_ratio * 3.5) * fuel_mult

        base_radius  = int(min(WIDTH * 0.145, HEIGHT * 0.22))
        left_radius  = base_radius
        right_radius = int(base_radius * 0.93)
        cy           = int(HEIGHT * 0.46)
        spacing      = int(WIDTH * 0.30)
        left_cx      = WIDTH // 2 - spacing
        right_cx     = WIDTH // 2 + spacing
        center_cx    = WIDTH // 2

        draw_gauge(left_cx,  cy, left_radius,  display_hp,     max_gauge_val, "hp",    "Power",  120, mode)
        draw_gauge(right_cx, cy, right_radius, display_torque, max_gauge_val, "lb-ft", "Torque", 120, mode)
        draw_center_panel(center_cx, cy, mode, instant_fuel, current_rpm, current_speed)
        draw_vignette()
        draw_top_bar(mode)
        draw_corner_hud(MODE_COLORS[mode])

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
