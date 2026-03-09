import math, random, time
import tkinter as tk

def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

# -----------------------------
# Pixel font (same)
# -----------------------------
PIXEL_FONT = {
    "0": ["XXXXX","X   X","X   X","X   X","XXXXX"],
    "1": ["  X  "," XX  ","  X  ","  X  "," XXX "],
    "2": ["XXXXX","    X","XXXXX","X    ","XXXXX"],
    "3": ["XXXXX","    X"," XXX ","    X","XXXXX"],
    "4": ["X   X","X   X","XXXXX","    X","    X"],
    "5": ["XXXXX","X    ","XXXXX","    X","XXXXX"],
    "6": ["XXXXX","X    ","XXXXX","X   X","XXXXX"],
    "7": ["XXXXX","    X","   X ","  X  ","  X  "],
    "8": ["XXXXX","X   X","XXXXX","X   X","XXXXX"],
    "9": ["XXXXX","X   X","XXXXX","    X","XXXXX"],
}

def draw_text(cv, x, y, text, ps, color):
    cx = x
    step = (5 + 1) * ps
    for ch in text:
        if ch == "-":
            cv.create_rectangle(
                (cx + ps) * 2,
                (y + 2 * ps) * 2,
                (cx + 4 * ps) * 2,
                (y + 3 * ps) * 2,
                fill=color, outline=""
            )
            cx += step
            continue

        pat = PIXEL_FONT.get(ch.upper())
        if pat is None:
            cx += step
            continue

        for r, row in enumerate(pat):
            for c, pix in enumerate(row):
                if pix != " ":
                    cv.create_rectangle(
                        (cx + c * ps) * 2,
                        (y + r * ps) * 2,
                        (cx + (c + 1) * ps) * 2,
                        (y + (r + 1) * ps) * 2,
                        fill=color, outline=""
                    )
        cx += step

# -----------------------------
# Ball helpers
# -----------------------------
def spawn_ball():
    ang = random.uniform(-0.55, 0.55)
    serving = random.choice([-1, 1])
    return {
        "x": 400.0, "y": 300.0,
        "vx": serving * 320 * math.cos(ang),
        "vy": 320 * math.sin(ang),
        "r": 8,
        "alive": True,
        "spin": 0.0,
        "curve": False,
        "ability_curve": False,
    }

def apply_curve_shot(b, paddle_vy):
    b["curve"] = True
    b["ability_curve"] = True
    pn = clamp(paddle_vy / 420, -1.0, 1.0)
    b["spin"] = clamp(pn * 3.2, -5.0, 5.0)
    b["vy"] += pn * 260.0
    b["vx"] *= 1.5
    b["vy"] *= 1.5

def paddle_hit(b, px, py, ph, pvy, is_left, st):
    x1 = px - 7 - b["r"]
    x2 = px + 7 + b["r"]
    y1 = py - ph/2 - b["r"]
    y2 = py + ph/2 + b["r"]

    if not (x1 <= b["x"] <= x2 and y1 <= b["y"] <= y2):
        return

    if is_left and b["vx"] >= 0:
        return
    if (not is_left) and b["vx"] <= 0:
        return

    b["curve"] = False
    b["spin"] = 0.0

    if is_left:
        b["x"] = px + 7 + b["r"] + 0.5
    else:
        b["x"] = px - 7 - b["r"] - 0.5

    b["vx"] = -b["vx"] * 1.04

    if is_left:
        if not st["charge_l"]:
            st["meter_l"] += 1
            if st["meter_l"] >= 5:
                st["meter_l"] = 0
                st["charge_l"] = True
    else:
        if not st["charge_r"]:
            st["meter_r"] += 1
            if st["meter_r"] >= 5:
                st["meter_r"] = 0
                st["charge_r"] = True

    off = clamp((b["y"] - py) / (ph / 2), -1.0, 1.0)
    speed = clamp(math.hypot(b["vx"], b["vy"]), 240.0, 900.0)

    new_vy = clamp(off * speed * 0.85, -speed * 0.95, speed * 0.95)
    b["vx"] = (1.0 if b["vx"] >= 0 else -1.0) * math.sqrt(max(speed*speed - new_vy*new_vy, 1.0))
    b["vy"] = new_vy

    if is_left and st["curve_ready_L"]:
        st["curve_ready_L"] = False
        apply_curve_shot(b, pvy)
    elif (not is_left) and st["curve_ready_R"]:
        st["curve_ready_R"] = False
        apply_curve_shot(b, pvy)
    else:
        pn = clamp(pvy / 420, -1.0, 1.0)
        b["curve"] = True
        b["spin"] = clamp(pn * 3.2 * 0.35, -5.0, 5.0)
        b["vy"] += pn * 120.0 * 0.35

    speed = math.hypot(b["vx"], b["vy"])
    if speed > 900.0:
        s = 900.0 / speed
        b["vx"] *= s; b["vy"] *= s
    elif speed < 240.0:
        s = 240.0 / max(speed, 1e-6)
        b["vx"] *= s; b["vy"] *= s

    st["rally"] += 1

def main():
    root = tk.Tk()
    root.title("Ultimate Pong")
    root.resizable(False, False)
    cv = tk.Canvas(root, width=1600, height=1200, bg="#0b0f17", highlightthickness=0)
    cv.pack()

    st = {
        "mouse_y": 300.0,
        "last": time.perf_counter(),
        "accum": 0.0,

        "left_x": 60.0,
        "left_y": 300.0,
        "left_vy": 0.0,
        "left_h": 90.0,

        "right_x": 740.0,
        "right_y": 300.0,
        "right_vy": 0.0,
        "right_h": 90.0,

        "balls": [spawn_ball()],
        "score_l": 0,
        "score_r": 0,
        "rally": 0,

        "meter_l": 0,
        "meter_r": 0,
        "charge_l": False,
        "charge_r": False,
        "curve_ready_L": False,
        "curve_ready_R": False,
    }

    def on_motion(e):
        st["mouse_y"] = e.y / 2

    def on_key(e):
        if e.keysym.lower() == "space" and st["charge_l"] and (not st["curve_ready_L"]):
            st["charge_l"] = False
            st["curve_ready_L"] = True

    cv.bind("<Motion>", on_motion)
    root.bind("<KeyPress>", on_key)

    def ai_update(dt):
        bs = st["balls"]
        if not bs: return
        cands = [b for b in bs if b["vx"] > 0]
        if not cands: cands = bs
        target = min(cands, key=lambda b: abs(st["right_x"] - b["x"]))

        aim_y = target["y"] + random.uniform(-35, 35) * 0.12
        err = aim_y - st["right_y"]
        move_dir = 0 if abs(err) < 10 else (1 if err > 0 else -1)

        st["right_vy"] = move_dir * 380.0
        st["right_y"] += st["right_vy"] * dt
        st["right_y"] = clamp(st["right_y"], st["right_h"]/2 + 10, 600 - st["right_h"]/2 - 10)

        if st["charge_r"] and (not st["curve_ready_R"]) and target["vx"] > 0 and target["x"] > 440 and random.random() < 0.55:
            st["charge_r"] = False
            st["curve_ready_R"] = True

    def step(dt):
        old = st["left_y"]
        st["left_y"] = clamp(st["mouse_y"], st["left_h"]/2 + 10, 600 - st["left_h"]/2 - 10)
        vy = (st["left_y"] - old) / max(dt, 1e-6)
        st["left_vy"] = clamp(vy, -1100.0, 1100.0)

        ai_update(dt)

        for b in st["balls"]:
            b["x"] += b["vx"] * dt
            b["y"] += b["vy"] * dt

            if b["curve"]:
                vx_sign = 1.0 if b["vx"] >= 0 else -1.0
                b["vy"] += (b["spin"] * 720.0) * dt * vx_sign
                b["spin"] *= max(0.0, 1.0 - 0.85 * dt)
                if abs(b["spin"]) < 0.02:
                    b["spin"] = 0.0
                    b["curve"] = False

            top = 12 + b["r"]
            bot = 588 - b["r"]
            if b["y"] < top:
                b["y"] = top
                b["vy"] = -b["vy"]
                if b["curve"]: b["spin"] *= 0.88
            elif b["y"] > bot:
                b["y"] = bot
                b["vy"] = -b["vy"]
                if b["curve"]: b["spin"] *= 0.88

            paddle_hit(b, st["left_x"],  st["left_y"],  st["left_h"],  st["left_vy"],  True,  st)
            paddle_hit(b, st["right_x"], st["right_y"], st["right_h"], st["right_vy"], False, st)

            if b["x"] < -50:
                b["alive"] = False
                st["score_r"] += 1
                st["rally"] = 0
                st["curve_ready_L"] = False
                break
            if b["x"] > 850:
                b["alive"] = False
                st["score_l"] += 1
                st["rally"] = 0
                st["curve_ready_R"] = False
                break

        st["balls"] = [b for b in st["balls"] if b["alive"]]

        if not st["balls"]:
            serving = -1 if ((st["score_l"] + st["score_r"]) % 2 == 0) else 1
            ang = random.uniform(-0.55, 0.55)
            st["balls"].append({
                "x": 400.0, "y": 300.0,
                "vx": serving * 320 * math.cos(ang),
                "vy": 320 * math.sin(ang),
                "r": 8,
                "alive": True,
                "spin": 0.0,
                "curve": False,
                "ability_curve": False,
            })

        max_balls = 1
        if st["rally"] >= 6:  max_balls = 2
        if st["rally"] >= 12: max_balls = 3
        if len(st["balls"]) < max_balls and st["rally"] in (6, 12):
            serving = random.choice([-1, 1])
            ang = random.uniform(-0.9, 0.9)
            st["balls"].append({
                "x": 400.0, "y": 300.0,
                "vx": serving * (320 * 0.95) * math.cos(ang),
                "vy": (320 * 0.95) * math.sin(ang),
                "r": 8,
                "alive": True,
                "spin": 0.0,
                "curve": False,
                "ability_curve": False,
            })

    def draw():
        cv.delete("all")

        for y in range(0, 600, 22):
            cv.create_rectangle((398) * 2, (y + 4) * 2, (402) * 2, (y + 14) * 2, fill="#2b3445", outline="")

        ls = str(st["score_l"])
        draw_text(cv, 336 - len(ls) * 24, 64, ls, 8, "#e6edf3")
        draw_text(cv, 464, 64, str(st["score_r"]), 8, "#e6edf3")

        cv.create_rectangle(
            (st["left_x"] - 7) * 2, (st["left_y"] - st["left_h"]/2) * 2,
            (st["left_x"] + 7) * 2, (st["left_y"] + st["left_h"]/2) * 2,
            fill="#e6edf3", outline=""
        )
        cv.create_rectangle(
            (st["right_x"] - 7) * 2, (st["right_y"] - st["right_h"]/2) * 2,
            (st["right_x"] + 7) * 2, (st["right_y"] + st["right_h"]/2) * 2,
            fill="#e6edf3", outline=""
        )

        tnow = time.perf_counter()
        for b in st["balls"]:
            spin_norm = min(abs(b["spin"]) / 5.0, 1.0)
            base = b["r"] + 2
            ww = base * (1.0 + 0.8 * spin_norm)
            hh = base * (1.0 - 0.6 * spin_norm)

            if b["ability_curve"]:
                t = (math.sin(tnow * 6 * math.pi) + 1) / 2
                c1 = "ffb000"
                r1, g1, b1 = (int(c1[i:i+2], 16) for i in (0,2,4))
                rr = r1 + (255 - r1) * t
                gg = g1 * (1 - t)
                bb = b1 * (1 - t)
                col = "#{:02x}{:02x}{:02x}".format(int(rr), int(gg), int(bb))
            else:
                col = "#ffb000"

            cv.create_rectangle((b["x"] - ww) * 2, (b["y"] - hh) * 2,
                                (b["x"] + ww) * 2, (b["y"] + hh) * 2,
                                fill=col, outline="")

        l_bar = "-----" if st["charge_l"] else ("-" * st["meter_l"]) + (" " * (5 - st["meter_l"]))
        r_bar = "-----" if st["charge_r"] else (" " * (5 - st["meter_r"])) + ("-" * st["meter_r"])

        draw_text(cv, 28, 568, l_bar, 4, "#66ff99" if (st["charge_l"] or st["curve_ready_L"]) else "#e6edf3")
        draw_text(
            cv,
            772 - len(r_bar) * 24,
            568,
            r_bar,
            4,
            "#66ff99" if (st["charge_r"] or st["curve_ready_R"]) else "#e6edf3"
        )

    def loop():
        now = time.perf_counter()
        frame_dt = min(0.05, now - st["last"])
        st["last"] = now
        st["accum"] += frame_dt

        while st["accum"] >= (1.0 / 60):
            step(1.0 / 60)
            st["accum"] -= (1.0 / 60)

        draw()
        root.after(16, loop)

    loop()
    root.mainloop()

if __name__ == "__main__":
    main()
