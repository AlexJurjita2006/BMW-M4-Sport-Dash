import pygame
import math
import sys
import random
import socket
import json
import os

# --- LOAD CONFIGURATION ---
config_path = os.path.join(os.path.dirname(__file__), "config.json")
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
    WIDTH, HEIGHT = config.get("redline_width", 1100), config.get("redline_height", 600)
else:
    WIDTH, HEIGHT = 1100, 600

# --- Colors (BMW M4 Digital Cluster) ---
BG_COLOR = (5, 6, 10)
WHITE = (245, 245, 250)
RED = (235, 45, 45)
M_BLUE_L = (0, 155, 220)
M_BLUE_D = (17, 30, 108)
GRAY = (110, 115, 125)
DIM_GRAY = (50, 55, 62)
DARK_GRAY = (18, 20, 26)
PANEL_BG = (10, 12, 18)
PANEL_BORDER = (30, 35, 45)
ACCENT_BLUE = (0, 160, 255)
ACCENT_GREEN = (0, 200, 100)
M_BLUE_TRAIL = (10, 45, 160)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("BMW M4 - Digital Instrument Cluster")

# --- UDP SENDER ---
udp_ip = "127.0.0.1"
udp_port = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- Fonts (scaled) ---
def sf(base):
    return max(10, int(base * min(WIDTH / 1100, HEIGHT / 600)))

font_large = pygame.font.SysFont("consolas", sf(56), bold=True)
font_medium = pygame.font.SysFont("segoeui", sf(20), bold=False)
font_small = pygame.font.SysFont("segoeui", sf(16), bold=True)
font_tiny = pygame.font.SysFont("consolas", sf(12), bold=False)
font_gear_big = pygame.font.SysFont("consolas", sf(72), bold=True)
font_speed_big = pygame.font.SysFont("consolas", sf(48), bold=True)
font_speed_unit = pygame.font.SysFont("segoeui", sf(16), bold=False)
font_m = pygame.font.SysFont("arial", sf(32), bold=True, italic=True)
font_tick = pygame.font.SysFont("consolas", sf(15), bold=True)
font_info_label = pygame.font.SysFont("segoeui", sf(13), bold=False)
font_info_val = pygame.font.SysFont("consolas", sf(18), bold=True)


def draw_rounded_rect(surf, color, rect, radius=8, border=0):
    x, y, w, h = rect
    r = min(radius, w // 2, h // 2)
    if border > 0:
        pygame.draw.rect(surf, color, (x + r, y, w - 2 * r, h), border)
        pygame.draw.rect(surf, color, (x, y + r, w, h - 2 * r), border)
        for cx, cy in [(x + r, y + r), (x + w - r, y + r),
                       (x + r, y + h - r), (x + w - r, y + h - r)]:
            pygame.draw.circle(surf, color, (cx, cy), r, border)
    else:
        pygame.draw.rect(surf, color, (x + r, y, w - 2 * r, h))
        pygame.draw.rect(surf, color, (x, y + r, w, h - 2 * r))
        for cx, cy in [(x + r, y + r), (x + w - r, y + r),
                       (x + r, y + h - r), (x + w - r, y + h - r)]:
            pygame.draw.circle(surf, color, (cx, cy), r)


def draw_m4_logo(surface, center_x, center_y):
    w, h, slant, gap = 10, 20, 6, 3
    start_x = center_x - 48
    pygame.draw.polygon(surface, M_BLUE_L,
                        [(start_x, center_y + h), (start_x + w, center_y + h),
                         (start_x + w + slant, center_y), (start_x + slant, center_y)])
    start_x += w + gap
    pygame.draw.polygon(surface, M_BLUE_D,
                        [(start_x, center_y + h), (start_x + w, center_y + h),
                         (start_x + w + slant, center_y), (start_x + slant, center_y)])
    start_x += w + gap
    pygame.draw.polygon(surface, RED,
                        [(start_x, center_y + h), (start_x + w, center_y + h),
                         (start_x + w + slant, center_y), (start_x + slant, center_y)])
    m4_text = font_m.render("M4", True, WHITE)
    surface.blit(m4_text, (start_x + w + gap + 2, center_y - 6))


def draw_digital_gauge(center, radius, current_val, max_val, unit_text,
                       major_tick, minor_tick, val_divisor=1,
                       redline_val=None, is_tach=False, is_accelerating=False,
                       launch_glow=0.0):
    """Draw a sleek digital-style gauge with segmented arc and glow effects."""
    cx, cy = center
    start_angle_deg = 220
    end_angle_deg = -40
    total_sweep = start_angle_deg - end_angle_deg

    # ── Gauge background panel (subtle) ──
    panel_r = radius + 20
    panel_surf = pygame.Surface((panel_r * 2, panel_r * 2), pygame.SRCALPHA)
    pygame.draw.circle(panel_surf, (8, 10, 16, 200), (panel_r, panel_r), panel_r)
    screen.blit(panel_surf, (cx - panel_r, cy - panel_r))

    # ── Face ──
    pygame.draw.circle(screen, DARK_GRAY, center, radius, 2)
    pygame.draw.circle(screen, (8, 9, 13), center, radius - 2)

    val_clamped = min(max(current_val, 0), max_val)
    current_angle_deg = start_angle_deg - (val_clamped / max_val) * total_sweep

    # ── Outer segmented arc background (dim) ──
    seg_gap = 2
    for a in range(int(end_angle_deg), int(start_angle_deg)):
        if a % seg_gap == 0:
            r_rad = math.radians(a)
            cos_a, sin_a = math.cos(r_rad), math.sin(r_rad)
            x1 = cx + (radius - 2) * cos_a
            y1 = cy - (radius - 2) * sin_a
            x2 = cx + (radius + 4) * cos_a
            y2 = cy - (radius + 4) * sin_a
            pygame.draw.line(screen, (18, 20, 28), (x1, y1), (x2, y2), 2)

    # ── Filled arc (progress) ──
    if not is_tach:
        # speedometer: blue glow fill
        for a in range(int(current_angle_deg), int(start_angle_deg)):
            if a % seg_gap == 0:
                r_rad = math.radians(a)
                cos_a, sin_a = math.cos(r_rad), math.sin(r_rad)
                # intensity ramp
                progress = (start_angle_deg - a) / max(1, start_angle_deg - current_angle_deg)
                r_c = int(M_BLUE_TRAIL[0] + 40 * progress)
                g_c = int(M_BLUE_TRAIL[1] + 50 * progress)
                b_c = min(255, int(M_BLUE_TRAIL[2] + 40 * progress))
                x1 = cx + (radius - 2) * cos_a
                y1 = cy - (radius - 2) * sin_a
                x2 = cx + (radius + 4) * cos_a
                y2 = cy - (radius + 4) * sin_a
                pygame.draw.line(screen, (r_c, g_c, b_c), (x1, y1), (x2, y2), 3)

        # outer glow bar when accelerating
        if is_accelerating and val_clamped > 5:
            for a in range(int(current_angle_deg), int(start_angle_deg)):
                r_rad = math.radians(a)
                cos_a, sin_a = math.cos(r_rad), math.sin(r_rad)
                x1 = cx + (radius + 5) * cos_a
                y1 = cy - (radius + 5) * sin_a
                x2 = cx + (radius + 9) * cos_a
                y2 = cy - (radius + 9) * sin_a
                progress = (start_angle_deg - a) / max(1, start_angle_deg - current_angle_deg)
                alpha_c = int(120 + 80 * progress)
                pygame.draw.line(screen, (0, int(60 * progress), alpha_c),
                                 (x1, y1), (x2, y2), 3)
    else:
        # tachometer: redline zone + dynamic fill
        if redline_val is not None:
            redline_angle = start_angle_deg - (redline_val / max_val) * total_sweep
            # static red zone
            for a in range(int(end_angle_deg), int(redline_angle)):
                if a % seg_gap == 0:
                    r_rad = math.radians(a)
                    cos_a, sin_a = math.cos(r_rad), math.sin(r_rad)
                    x1 = cx + (radius - 2) * cos_a
                    y1 = cy - (radius - 2) * sin_a
                    x2 = cx + (radius + 4) * cos_a
                    y2 = cy - (radius + 4) * sin_a
                    pygame.draw.line(screen, (160, 30, 20), (x1, y1), (x2, y2), 2)

            # glow on redline
            if val_clamped >= redline_val:
                for a in range(int(current_angle_deg), int(redline_angle)):
                    if a % seg_gap == 0:
                        r_rad = math.radians(a)
                        cos_a, sin_a = math.cos(r_rad), math.sin(r_rad)
                        x1 = cx + (radius - 2) * cos_a
                        y1 = cy - (radius - 2) * sin_a
                        x2 = cx + (radius + 6) * cos_a
                        y2 = cy - (radius + 6) * sin_a
                        pygame.draw.line(screen, RED, (x1, y1), (x2, y2), 3)

            # full tach face fills red progressively in redline zone
            if val_clamped >= redline_val:
                red_progress = min((val_clamped - redline_val) / max(max_val - redline_val, 1), 1.0)
                overlay_alpha = 45 + int(150 * red_progress)
                glow_alpha = 18 + int(60 * red_progress)

                red_overlay = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(red_overlay, (180, 20, 20, overlay_alpha), (radius, radius), radius - 4)
                pygame.draw.circle(red_overlay, (220, 35, 25, glow_alpha), (radius, radius), int(radius * 0.72))
                screen.blit(red_overlay, (cx - radius, cy - radius))

        # launch control glow: fills as arc + overlay, turns RED when bar is full
        if launch_glow > 0.0 and val_clamped < (redline_val or max_val):
            # colour: orange at 0→0.9, red at 1.0
            if launch_glow >= 1.0:
                lc_r, lc_g, lc_b = 235, 40, 35
                oc1 = (210, 25, 20)
                oc2 = (235, 45, 35)
            else:
                t    = launch_glow          # 0 → 1
                lc_r = int(210 + 25 * t)
                lc_g = max(0, int(90  * (1.0 - t)))
                lc_b = max(0, int(15  * (1.0 - t)))
                oc1  = (int(200 + 10*t), max(0, int(90*(1-t))), max(0, int(10*(1-t))))
                oc2  = (int(240 - 5*t),  max(0, int(130*(1-t))), max(0, int(20*(1-t))))
            # ── arc segments filling the current RPM region ──
            for a in range(int(current_angle_deg), int(start_angle_deg)):
                if a % seg_gap == 0:
                    r_rad = math.radians(a)
                    cos_a, sin_a = math.cos(r_rad), math.sin(r_rad)
                    progress = (start_angle_deg - a) / max(1, start_angle_deg - current_angle_deg)
                    bright = min(255, int(lc_r * (0.55 + 0.45 * progress)))
                    g_seg  = min(255, int(lc_g * (0.55 + 0.45 * progress)))
                    b_seg  = min(255, int(lc_b * (0.55 + 0.45 * progress)))
                    x1 = cx + (radius - 2) * cos_a
                    y1 = cy - (radius - 2) * sin_a
                    x2 = cx + (radius + 4) * cos_a
                    y2 = cy - (radius + 4) * sin_a
                    pygame.draw.line(screen, (bright, g_seg, b_seg), (x1, y1), (x2, y2), 3)
            # ── face overlay glow ──
            lo_alpha = int(30 + 120 * launch_glow)
            lo_inner = int(20 + 45  * launch_glow)
            launch_overlay = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(launch_overlay, (*oc1, lo_alpha),  (radius, radius), radius - 4)
            pygame.draw.circle(launch_overlay, (*oc2, lo_inner), (radius, radius), int(radius * 0.68))
            screen.blit(launch_overlay, (cx - radius, cy - radius))

    # ── Tick marks ──
    for val in range(0, int(max_val) + 1, int(minor_tick)):
        angle_deg = start_angle_deg - (val / max_val) * total_sweep
        angle_rad = math.radians(angle_deg)
        is_major = (val % major_tick == 0)
        line_len = 18 if is_major else 7
        thickness = 2 if is_major else 1
        cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)

        in_redline = is_tach and redline_val and val >= redline_val
        tick_color = RED if in_redline else (WHITE if is_major else DIM_GRAY)

        r_inner = radius - 14 - line_len
        r_outer = radius - 14
        x1 = cx + r_inner * cos_a
        y1 = cy - r_inner * sin_a
        x2 = cx + r_outer * cos_a
        y2 = cy - r_outer * sin_a
        pygame.draw.line(screen, tick_color, (x1, y1), (x2, y2), thickness)

        if is_major:
            display_val = int(val / val_divisor)
            num_text = font_tick.render(str(display_val), True, WHITE)
            r_lbl = radius - 48
            lx = cx + r_lbl * cos_a - num_text.get_width() // 2
            ly = cy - r_lbl * sin_a - num_text.get_height() // 2
            screen.blit(num_text, (lx, ly))

    # ── Digital needle (thin bright line) ──
    current_angle_rad = math.radians(current_angle_deg)
    cos_n, sin_n = math.cos(current_angle_rad), math.sin(current_angle_rad)
    needle_len = radius - 30
    tip_x = cx + needle_len * cos_n
    tip_y = cy - needle_len * sin_n

    # needle glow
    glow_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.line(glow_surf, (255, 255, 255, 30),
                     (cx, cy), (int(tip_x), int(tip_y)), 6)
    screen.blit(glow_surf, (0, 0))

    # main needle
    pygame.draw.line(screen, WHITE, (cx, cy), (int(tip_x), int(tip_y)), 2)

    # centre dot
    pygame.draw.circle(screen, (20, 22, 28), center, 18)
    pygame.draw.circle(screen, DARK_GRAY, center, 18, 2)
    pygame.draw.circle(screen, (60, 65, 75), center, 6)

    # ── Unit text ──
    unit_surf = font_medium.render(unit_text, True, GRAY)
    screen.blit(unit_surf, (cx - unit_surf.get_width() // 2, cy + 40))

    # ── M4 logo on tachometer ──
    if is_tach:
        draw_m4_logo(screen, cx, cy + 80)


def draw_centre_display(cx, cy, w, h, gear_text, speed):
    """Draw the central mini-screen with only gear and speed."""
    x = cx - w // 2
    y = cy - h // 2

    gear_font = pygame.font.SysFont("consolas", max(30, int(h * 0.34)), bold=True)
    speed_font = pygame.font.SysFont("consolas", max(24, int(h * 0.24)), bold=True)
    unit_font = pygame.font.SysFont("segoeui", max(12, int(h * 0.10)), bold=False)

    # panel
    draw_rounded_rect(screen, PANEL_BG, (x, y, w, h), 10)
    draw_rounded_rect(screen, PANEL_BORDER, (x, y, w, h), 10, 1)

    # subtle inner glow
    glow = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(glow, (0, 120, 255, 8), (2, 2, w - 4, h - 4))
    screen.blit(glow, (x, y))

    # ── GEAR ──
    gear_color = ACCENT_GREEN if gear_text == "N" else WHITE
    g_surf = gear_font.render(gear_text, True, gear_color)
    screen.blit(g_surf, (cx - g_surf.get_width() // 2, y + int(h * 0.10)))

    # separator line
    sep_y = y + int(h * 0.10) + g_surf.get_height() + 4
    pygame.draw.line(screen, PANEL_BORDER, (x + 12, sep_y), (x + w - 12, sep_y), 1)

    # ── SPEED (big digital) ──
    spd_surf = speed_font.render(f"{int(speed)}", True, WHITE)
    screen.blit(spd_surf, (cx - spd_surf.get_width() // 2, sep_y + int(h * 0.07)))

    unit_surf = unit_font.render("km/h", True, GRAY)
    screen.blit(unit_surf, (cx - unit_surf.get_width() // 2,
                            sep_y + int(h * 0.07) + spd_surf.get_height()))

    # bottom M stripes
    stripe_y = y + h - 6
    stripe_w = w // 3
    pygame.draw.rect(screen, M_BLUE_L, (x, stripe_y, stripe_w, 3))
    pygame.draw.rect(screen, M_BLUE_D, (x + stripe_w, stripe_y, stripe_w, 3))
    pygame.draw.rect(screen, RED, (x + 2 * stripe_w, stripe_y, w - 2 * stripe_w, 3))


# Extra color used in centre display
OFF_WHITE = (200, 205, 210)


def main():
    clock = pygame.time.Clock()
    running = True

    # Telemetry file
    telemetry_file = open("telemetry.txt", "w")
    telemetry_file.write("Time(s) | Speed(km/h) | RPM | Gear | Torque(Nm) | Power(HP)\n" + "-" * 70 + "\n")

    # Engine parameters
    rpm, display_rpm, idle_rpm, max_rpm = 800.0, 800.0, 800.0, 8000.0
    speed, max_speed_display = 0.0, 330.0
    gear_max_speeds = [52, 88, 128, 172, 220, 275, 333]
    current_gear, shift_pause, is_in_drive = 1, 0, False
    throttle_load, current_hp, current_torque = 0.0, 0.0, 0.0
    frame_count = 0

    while running:
        screen.fill(BG_COLOR)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            is_in_drive, is_revving, is_accelerating = False, True, False
        elif keys[pygame.K_RETURN]:
            is_in_drive, is_accelerating, is_revving = True, True, False
        else:
            is_accelerating = is_revving = False
        is_braking = keys[pygame.K_LSHIFT]

        # Throttle load
        if is_in_drive and is_accelerating:
            throttle_load = min(throttle_load + 0.08, 1.0)
        elif not is_in_drive and is_revving:
            throttle_load = min(throttle_load + 0.1, 0.3)
        else:
            throttle_load = max(throttle_load - 0.1, 0.0)

        # Speed physics
        if is_in_drive:
            if shift_pause > 0:
                shift_pause -= 1
                speed += 0.02
            elif is_braking:
                speed -= 2.5
            elif is_accelerating:
                speed = min(speed + (random.uniform(-0.5, 0.6) if speed >= 328
                            else max(0.08, 0.7 - (speed / 330.0) * 0.6)), 333.0)
            else:
                speed -= 0.25
        else:
            speed -= 2.5 if is_braking else 0.1
        speed = max(speed, 0)

        # M-DCT gear logic
        if is_in_drive:
            if current_gear < 7 and speed > gear_max_speeds[current_gear - 1] - 2:
                current_gear += 1
                shift_pause, throttle_load = 10, 0.0
            elif current_gear > 1 and (speed / gear_max_speeds[current_gear - 1]) * 7500 < 1800:
                current_gear -= 1
                shift_pause = 6

        # RPM logic
        if not is_in_drive:
            current_gear_text = "N"
            rpm += 160.0 if is_revving else -100.0
        else:
            current_gear_text = "D1" if speed == 0 else f"D{current_gear}"
            if speed == 0:
                rpm -= 100.0
            else:
                rpm = max(idle_rpm,
                          idle_rpm + (speed / 15.0) * 1000
                          if speed < 15 and current_gear == 1
                          else (speed / gear_max_speeds[current_gear - 1]) * 7500)

        rpm = min(max(rpm, idle_rpm), max_rpm - 200 if rpm > max_rpm else max_rpm)
        display_rpm += (rpm - display_rpm) * (0.9 if shift_pause > 0 else 0.3)

        # Torque & HP (S58 engine model)
        if display_rpm < 2750:
            base_torque = 200 + ((display_rpm - 800) / 1950) * 450
        elif display_rpm <= 5500:
            base_torque = 650
        else:
            base_torque = 650 - ((display_rpm - 5500) / 1700) * 120
        current_torque = base_torque * throttle_load
        current_hp = (current_torque * display_rpm) / 7022.0

        # --- SEND UDP TO SPORT SCREEN ---
        telemetry_data = {"hp": current_hp, "torque": current_torque, "rpm": display_rpm, "speed": speed}
        sock.sendto(json.dumps(telemetry_data).encode(), (udp_ip, udp_port))

        # Save telemetry
        frame_count += 1
        if frame_count % 12 == 0:
            telemetry_file.write(
                f"{pygame.time.get_ticks() / 1000.0:06.2f} | {int(speed):03d} km/h | "
                f"{int(display_rpm):04d} RPM | {current_gear_text:>2} | "
                f"{int(current_torque):03d} Nm | {int(current_hp):03d} HP\n")

        # ══════════════════════════════════════════════════
        # ─── LAYOUT ───
        # ══════════════════════════════════════════════════
        gauge_radius = int(min(WIDTH * 0.19, HEIGHT * 0.38))
        gauge_y = int(HEIGHT * 0.48)

        # Gap: gauges pushed to sides, centre display in the gap
        centre_gap = int(WIDTH * 0.17)
        speedo_x = int(WIDTH * 0.24)
        tacho_x = int(WIDTH * 0.76)

        # ── Speedometer (left) ──
        draw_digital_gauge((speedo_x, gauge_y), gauge_radius, speed,
                           max_speed_display, "km/h", 30, 10, 1,
                           None, False, is_accelerating)

        # ── Launch glow: D1/D2/early-D3 + max torque (>=600 Nm) ──
        launch_gear_ok = (
            current_gear <= 2 or
            (current_gear == 3 and speed < gear_max_speeds[1] * 0.75)
        )
        launch_glow_val = 0.0
        if is_in_drive and launch_gear_ok and current_torque >= 600:
            # smoothly scale 600-650 Nm → 0.0-1.0
            launch_glow_val = min((current_torque - 600) / 50.0, 1.0)

        # ── Tachometer (right) ──
        draw_digital_gauge((tacho_x, gauge_y), gauge_radius, display_rpm,
                           max_rpm, "1/min x1000", 1000, 200, 1000,
                           7200, True, is_accelerating, launch_glow_val)

        # ── Centre mini-screen ──
        mini_w = int(centre_gap * 0.74)
        mini_h = int(HEIGHT * 0.42)
        draw_centre_display(WIDTH // 2, gauge_y, mini_w, mini_h,
                    current_gear_text, speed)

        # ── Bottom info bar ──
        bar_h = 32
        bar_y = HEIGHT - bar_h
        pygame.draw.rect(screen, (0, 0, 0), (0, bar_y, WIDTH, bar_h))
        pygame.draw.line(screen, PANEL_BORDER, (0, bar_y), (WIDTH, bar_y), 1)
        info_text = "SPACE: Rev (N)  |  ENTER: Accelerate (D)  |  SHIFT: Brake"
        it = font_small.render(info_text, True, GRAY)
        screen.blit(it, (WIDTH // 2 - it.get_width() // 2, bar_y + 7))

        pygame.display.flip()
        clock.tick(60)

    telemetry_file.close()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()