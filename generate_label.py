"""Generate an A6 shipping label PDF from a JSON payload.

Usage: python generate_label.py payload.json
Writes docs/labels/<tracking>.pdf and docs/labels/latest.pdf
"""
import json, os, re, shutil, sys
from reportlab.lib.pagesizes import A6
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.barcode import code128, qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

BASE_URL = os.environ.get("TRACK_BASE_URL", "https://example.com/track/")
HERE = os.path.dirname(os.path.abspath(__file__))
pdfmetrics.registerFont(TTFont("Geist", f"{HERE}/fonts/Geist-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Geist-SB", f"{HERE}/fonts/Geist-SemiBold.ttf"))
pdfmetrics.registerFont(TTFont("GeistMono", f"{HERE}/fonts/GeistMono-Medium.ttf"))

INK, GREY, KRAFT = HexColor("#14192A"), HexColor("#5A6378"), HexColor("#B78A58")

DEFAULTS = {
    "tracking": "SPY-2026-000000",
    "sender_name": "Acme Store S.r.l.", "sender_street": "Via Roma 10", "sender_city": "20121 Milano (MI), IT",
    "service": "Express, priority", "parcels": "1", "weight": "1.20",
    "name": "Mario Rossi", "street": "Via Garibaldi 25", "city": "00185 Roma (RM)", "country": "Italy",
    "province": "RM", "contents": "Sample goods", "note": "", "eta": "", "eta_time": "",
}

def clean(s, n=40):
    return re.sub(r"\s+", " ", str(s or "")).strip()[:n]

def build(p, out):
    p = {**DEFAULTS, **{k: clean(v, 60) for k, v in p.items() if v not in (None, "")}}
    if not p.get("tracking") or p["tracking"] == DEFAULTS["tracking"]:
        run = os.environ.get("GITHUB_RUN_NUMBER")
        if run and run.isdigit():
            p["tracking"] = "SPY-2026-%06d" % int(run)
    track = re.sub(r"[^A-Za-z0-9\-]", "", p["tracking"])[:24] or DEFAULTS["tracking"]
    url = BASE_URL + track
    c = canvas.Canvas(out, pagesize=A6); c.setTitle(f"Label {track}")
    W, H = A6
    L, T, BW = 7*mm, 140*mm, 88.5*mm
    rows = [19, 34, 19, 28, 30]; BH = sum(rows)*mm; B = T-BH; R = L+BW
    SH, rad, PADX, PADY = 2.1*mm, 1.6*mm, 4*mm, 3*mm
    c.setFillColor(KRAFT); c.roundRect(L+SH, B-SH, BW, BH, rad, stroke=0, fill=1)
    c.setFillColor(HexColor("#FFFFFF")); c.roundRect(L, B, BW, BH, rad, stroke=0, fill=1)
    ys = [T]
    for r in rows: ys.append(ys[-1]-r*mm)
    c.setStrokeColor(INK); c.setLineWidth(1.5)
    for y in ys[1:-1]: c.line(L, y, R, y)
    mid = L+BW/2
    for i in (0, 2): c.line(mid, ys[i], mid, ys[i+1])
    def key(x, yt, t):
        c.setFillColor(GREY); c.setFont("GeistMono", 6.3); c.drawString(x, yt-PADY-1.6*mm, t)
    def val(x, yt, lines, size=8.6, lead=3.9*mm, font="Geist-SB", dy=6.6*mm):
        c.setFillColor(INK); c.setFont(font, size)
        for i, t in enumerate(l for l in lines if l): c.drawString(x, yt-PADY-dy-i*lead, t)
    key(L+PADX, ys[0], "From")
    val(L+PADX, ys[0], [p["sender_name"], p["sender_street"], p["sender_city"]])
    key(mid+PADX, ys[0], "Service")
    plural = "" if p["parcels"] == "1" else "s"
    val(mid+PADX, ys[0], [p["service"], f'{p["parcels"]} parcel{plural}, {p["weight"]} kg'])
    key(L+PADX, ys[1], "Deliver to")
    c.setFillColor(INK); c.setFont("Geist-SB", 17 if len(p["name"]) < 22 else 13)
    c.drawString(L+PADX, ys[1]-PADY-9.6*mm, p["name"])
    c.setStrokeColor(HexColor("#9AA3B5")); c.setLineWidth(1.5); c.setDash(2.2, 1.6)
    c.line(L+PADX, ys[1]-PADY-11.6*mm, R-PADX, ys[1]-PADY-11.6*mm); c.setDash(); c.setStrokeColor(INK)
    val(L+PADX, ys[1], [p["street"], p["city"], p["country"]], size=10, lead=4.6*mm, font="Geist", dy=17.2*mm)
    c.setFont("Geist-SB", 22); c.setFillColor(INK); c.drawRightString(R-PADX, ys[2]+3.4*mm, p["province"][:3].upper())
    key(L+PADX, ys[2], "Contents"); val(L+PADX, ys[2], [p["contents"], p["note"]])
    key(mid+PADX, ys[2], "Estimated delivery"); val(mid+PADX, ys[2], [p["eta"] or "To be confirmed", p["eta_time"]])
    bc = code128.Code128(track, barHeight=14*mm, barWidth=0.42*mm, quiet=False)
    bc.drawOn(c, L+PADX, ys[4]+8.6*mm)
    c.setFillColor(INK); c.setFont("GeistMono", 9); c.drawString(L+PADX, ys[4]+3.6*mm, track)
    qsz = 21*mm; qw = qr.QrCodeWidget(url, barFillColor=INK); b = qw.getBounds()
    d = Drawing(qsz, qsz, transform=[qsz/(b[2]-b[0]), 0, 0, qsz/(b[3]-b[1]), 0, 0]); d.add(qw)
    renderPDF.draw(d, c, L+PADX, B+(rows[4]*mm-qsz)/2)
    tx = L+PADX+qsz+5*mm
    key(tx, ys[4], "Track")
    c.setFillColor(INK); c.setFont("GeistMono", 6.8)
    host = url.split("//")[-1].rsplit("/", 1)[0] + "/"
    c.drawString(tx, ys[4]-PADY-7*mm, host); c.drawString(tx, ys[4]-PADY-10.2*mm, track)
    c.setFont("Geist", 7.6); c.drawString(tx, ys[4]-PADY-15.6*mm, "Scan for live status")
    c.setStrokeColor(INK); c.setLineWidth(2.2); c.roundRect(L, B, BW, BH, rad, stroke=1, fill=0)
    c.setFillColor(GREY); c.setFont("GeistMono", 5.8); c.drawString(L, 4.4*mm, "Sample label, not valid for shipping")
    c.save()
    return track

if __name__ == "__main__":
    payload = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else {}
    os.makedirs("docs/labels", exist_ok=True)
    tmp = "docs/labels/_tmp.pdf"
    track = build(payload, tmp)
    shutil.copy(tmp, f"docs/labels/{track}.pdf")
    shutil.move(tmp, "docs/labels/latest.pdf")
    print("generated", track)
