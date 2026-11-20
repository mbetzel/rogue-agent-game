"""Exact per-die math for the Gray ⚠ probe (docs/plans/gray_vulnerability_gd_plan.md §2).

Value scale (assumption, stated in the plan): $1 = 1 🔬 = 1, Market Share = 1.5, Corporate Secret = 2, ★ = 2.5,
R&D face = its Secret yield (Green R&D also refunds 2 Vulnerability, counted separately).
Lock rule (v0.49): a die showing ⚠ can't be rerolled. 3 rolls = 1 roll + 2 rerolls per die.
Policies: KEEP = never reroll; WEAK = reroll a clean face worth <= 1 while rerolls remain; ANY = reroll every clean face < 2.
"""
from fractions import Fraction as F

# (value, vuln) per face
DICE = {
    "Red":    [(2.5, 1), (2, 0), (2, 0), (2, 0), (4, 1), (2.5, 0)],
    "Blue":   [(2, 0), (2, 0), (3, 1), (1, 0), (4, 1), (2.5, 0)],
    "Green":  [(3, 1), (1, 0), (2, 0), (1, 0), (4, 1), (2.5, 0)],
    "Yellow": [(3, 1), (1.5, 0), (2.5, 0), (2, 0), (3, 1), (2.5, 0)],
    "Purple": [(1, 0), (1, 0), (2, 0), (3, 1), (2, 1), (2.5, 0)],
}
GRAY_VAL = [2, 2, 2, 1, 1, 1]
GRAY = {"G1 {F3}": (3,), "A13 {F1,F3}": (1, 3), "B23 {F2,F3}": (2, 3), "C35 {F3,F5}": (3, 5), "C36 {F3,F6}": (3, 6),
        "D123 {F1,F2,F3}": (1, 2, 3), "E356 {F3,F5,F6}": (3, 5, 6), "E345 {F3,F4,F5}": (3, 4, 5)}
for k, vs in GRAY.items():
    DICE["Gray " + k] = [(GRAY_VAL[i], 1 if i + 1 in vs else 0) for i in range(6)]


def final(faces, thresh, rerolls=2):
    """Distribution over face index after rerolling clean faces with value <= thresh (locked ⚠ faces stay)."""
    dist = [F(1, 6)] * 6
    for _ in range(rerolls):
        nd = [F(0)] * 6
        for i, p in enumerate(dist):
            v, w = faces[i]
            if w == 0 and v <= thresh:
                for j in range(6):
                    nd[j] += p / 6
            else:
                nd[i] += p
        dist = nd
    return dist


def row(name, faces):
    out = [name]
    for th in (-1, 1, 1.5):
        d = final(faces, th)
        pv = float(sum(p for p, (v, w) in zip(d, faces) if w))
        ev = float(sum(p * v for p, (v, w) in zip(d, faces)))
        out += [pv, ev]
    ev0 = sum(v for v, _ in faces) / 6
    pw = sum(w for _, w in faces) / 6
    out += [pw / ev0]
    return out


if __name__ == "__main__":
    print(f"{'die':22s} {'P⚠ keep':>8} {'EV':>5} {'P⚠ weak':>8} {'EV':>5} {'P⚠ any':>8} {'EV':>5} {'⚠/unit':>7}")
    for k, f in DICE.items():
        r = row(k, f)
        print(f"{r[0]:22s} {r[1]:8.3f} {r[2]:5.2f} {r[3]:8.3f} {r[4]:5.2f} {r[5]:8.3f} {r[6]:5.2f} {r[7]:7.3f}")
    # rounds-to-first-Green-eligibility (Vulnerability >= 5 from 0), no Pen Test, per-round ⚠ from G Gray + C colored dice
    import itertools

    def conv(ps):
        dist = [1.0]
        for p in ps:
            nd = [0.0] * (len(dist) + 1)
            for i, x in enumerate(dist):
                nd[i] += x * (1 - p)
                nd[i + 1] += x * p
            dist = nd
        return dist

    print("\nP(Vulnerability >= 5 after N rounds from 0, no Pen Test); colored P⚠ = 0.33 each")
    pools = {"opening 3G+2C": (3, 2), "mid 2G+4C": (2, 4), "late 1G+5C": (1, 5)}
    for pn, (g, c) in pools.items():
        for gk, pg in (("G1", 1 / 6), ("2⚠", 1 / 3), ("3⚠", 1 / 2)):
            d1 = conv([pg] * g + [1 / 3] * c)
            ev = sum(i * x for i, x in enumerate(d1))
            cur = [1.0]
            res = []
            for n in range(1, 5):
                nd = [0.0] * (len(cur) + len(d1))
                for i, x in enumerate(cur):
                    for j, y in enumerate(d1):
                        nd[i + j] += x * y
                cur = nd
                res.append(sum(x for i, x in enumerate(cur) if i >= 5))
            print(f"  {pn:15s} {gk:3s} E⚠/round={ev:4.2f} (Gray {g * pg:4.2f})  P>=5 after 1..4 rounds: " + " ".join(f"{x:.2f}" for x in res))
