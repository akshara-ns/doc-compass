"""Builds the Project 1 check-in figure (one landscape SVG inside an HTML page).

Run:  python3 build_figure.py   -> writes checkin_figure.html next to this file.
"""
from html import escape
from pathlib import Path

W, H = 1900, 1120
out = []

def t(s):
    return escape(s, quote=True)

# ---------- primitives ----------
def text(x, y, s, cls="tx", anchor="start"):
    out.append(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{t(s)}</text>')

def chip(x, y, letter):
    out.append(f'<rect x="{x}" y="{y-11}" width="15" height="14" rx="3" class="chip c{letter}"/>')
    out.append(f'<text x="{x+7.5}" y="{y}" class="chipt" text-anchor="middle">{letter}</text>')

def qbadge(cx, cy, n):
    out.append(f'<circle cx="{cx}" cy="{cy}" r="12" class="qb"/>')
    out.append(f'<text x="{cx}" y="{cy+4}" class="qbt" text-anchor="middle">Q{n}</text>')

KIND = {
    "confirmed": "box",
    "proposed": "box dash",
    "human": "box human",
    "humanp": "box human dash",
    "external": "box ext",
    "emergency": "box emerg",
}

def node(x, y, w, h, title, lines=(), kind="confirmed", q=(), mono=False, subs=()):
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" class="{KIND[kind]}"/>')
    tcls = "ttl mono" if mono else "ttl"
    if kind == "emergency":
        tcls += " em"
    text(x + 12, y + 22, title, tcls)
    ly = y + 41
    for ln in lines:
        if ln == "":
            ly += 7
            continue
        if isinstance(ln, tuple):
            kindl = ln[0]
            if kindl == "chip":
                chip(x + 12, ly, ln[1])
                text(x + 33, ly, ln[2])
            elif kindl == "b":
                text(x + 12, ly, ln[1], "tx b")
            elif kindl == "i":
                text(x + 12, ly, ln[1], "tx muted it")
            elif kindl == "ind":
                text(x + 33, ly, ln[1])
        elif ln.startswith(("in ", "out ")):
            k, v = ln.split(None, 1)
            text(x + 12, ly, k, "tx muted b")
            text(x + 40, ly, v)
        elif ln.startswith("   "):
            text(x + 40, ly, ln.strip())
        else:
            text(x + 12, ly, ln)
        ly += 15.5
    for (oy, sh, slines) in subs:
        out.append(f'<rect x="{x+10}" y="{y+oy}" width="{w-20}" height="{sh}" rx="4" class="sub"/>')
        sy = y + oy + 16
        for s in slines:
            text(x + 20, sy, s, "tx sm")
            sy += 14.5
    for i, n in enumerate(q):
        qbadge(x + w - 4 - i * 28, y + 2, n)

def arrow(pts, cls, dashed=False):
    d = " ".join(f"{px},{py}" for px, py in pts)
    dc = " dash" if dashed else ""
    out.append(f'<polyline points="{d}" class="ar {cls}{dc}" marker-end="url(#m-{cls})"/>')

def label(x, y, s, anchor="start", cls="al"):
    text(x, y, s, cls, anchor)

# ---------- canvas ----------
out.append(f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
           'aria-label="End-to-end system figure for Doc Compass: a student types a health '
           'concern, it is redacted, checked for red flags, routed to a top-3 of specialties and explained; '
           'offline, manual gold data and noisy subreddit data train and evaluate the models.">')
out.append('<defs>')
for c in ["ink", "pred", "train", "emerg", "fb"]:
    out.append(f'<marker id="m-{c}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
               f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="mk {c}"/></marker>')
out.append('</defs>')
out.append(f'<rect x="0" y="0" width="{W}" height="{H}" class="canvas"/>')

# title
text(20, 38, "Doc Compass", "h1")
text(222, 38, "Which doctor do I book?  ·  System check-in figure  ·  Project 1, 24-679  ·  Akshara & Sohum  ·  v2 after feasibility check, 27 Sep 2026", "h1sub")
text(1880, 38, "Routes to a kind of doctor. Never diagnoses.", "h1sub", "end")

# lanes
lanes = [
    (76, 330, "lA", "USER + INTERFACE", "Gradio app on a ZeroGPU HF Space"),
    (342, 612, "lB", "MODELS AT RUN TIME", "inside the Space; no text leaves it"),
    (624, 1108, "lC", "DATA + TRAINING", "offline, Colab or Kaggle"),
]
for (y0, y1, cls, name, sub) in lanes:
    out.append(f'<rect x="20" y="{y0}" width="1460" height="{y1-y0}" rx="8" class="lane {cls}"/>')
    cy = (y0 + y1) / 2
    out.append(f'<text transform="translate(40 {cy}) rotate(-90)" class="lanet" text-anchor="middle">{t(name)}</text>')
    out.append(f'<text transform="translate(54 {cy}) rotate(-90)" class="lanes" text-anchor="middle">{t(sub)}</text>')

# ---------- lane A: user ----------
node(70, 100, 194, 200, "Intended user", [
    "International student, new",
    "to booking US specialists",
    "(we are two of them)",
    "",
    ("b", "Decision to support:"),
    "which kind of doctor",
    "should I book?",
    ("i", "Not: what do I have?"),
], kind="human")
node(300, 100, 190, 125, "Describes the concern", [
    "plain language, free text",
    "“itchy rash on both shins,",
    "3 weeks, 22F, Pittsburgh”",
    ("i", "(contains PII)"),
])
node(510, 100, 200, 92, "Seek emergency care now", [
    "call 911 or go to the ER",
    "nothing else runs",
], kind="emergency")
node(740, 100, 220, 140, "Checks the redaction", [
    "removed spans highlighted",
    "before anything moves on",
    "“… 3 weeks, [AGE/SEX],",
    "[CITY]”",
    ("i", "can undo a redaction? (TBD)"),
])
node(990, 100, 250, 160, "Reads the result", [
    "Top-3 specialties + confidence",
    ("i", "e.g. Dermatology 62% ·"),
    ("i", "Start with a GP 21% · Allergy 9%"),
    "“Start with a GP” always visible",
    "Why, plus questions to bring",
    "Disclaimer: routing, not diagnosis",
])
node(1290, 100, 172, 120, "Books a visit", [
    "outside our system:",
    "insurance directory,",
    "student health center",
], kind="external")
node(1290, 232, 172, 70, "Feedback", [
    "Right door? yes / no",
    "counts only, no text kept",
], kind="proposed")

arrow([(264, 160), (298, 160)], "ink"); label(281, 152, "types", "middle")
arrow([(1240, 160), (1288, 160)], "pred"); label(1264, 152, "decides", "middle")
arrow([(1375, 220), (1375, 230)], "fb", dashed=True)

# ---------- lane B: models ----------
node(300, 368, 225, 224, "1  Red-flag check", [
    ("chip", "R", "written rules"),
    "runs first, on the raw text,",
    "inside the Space",
    "chest pain · stroke signs",
    "anaphylaxis · heavy bleeding",
    "head injury · suicidal ideation",
    "each rule cites a source",
    "",
    "out  emergency yes / no",
    ("i", "never learned from data"),
])
node(560, 368, 240, 224, "2  Redact", [
    "in   raw concern text",
    "out  redacted text + PII spans",
    "",
    ("chip", "O", "Presidio (en_core_web_sm)"),
    ("chip", "S", "CRF, trained on synthetic"),
    ("ind", "PII + TAB"),
    ("chip", "F", "DistilBERT (stretch goal)"),
    ("i", "floor: regex rules, reported only"),
    "",
    "Ships: best recall on our",
    "300 PII-labelled posts",
])
node(835, 368, 265, 224, "3  Route", [
    "in   redacted text",
    "out  top-3 of 10 classes,",
    "     GP first included",
    ("chip", "S", "TF-IDF + logistic regression"),
    ("chip", "F", "DistilRoBERTa vs BiomedBERT"),
    ("i", "general vs biomedical encoder"),
    ("i", "on patient-written text"),
], subs=[(150, 44, ["if top probability < τ → “Start", "with a GP”; τ tuned on the dev split"])], q=(7,))
node(1140, 368, 220, 224, "4  Explain", [
    ("chip", "O", "Qwen2.5-1.5B-Instruct"),
    "on the Space’s ZeroGPU",
    "in   redacted text + top-3",
    "out  short rationale +",
    "     questions to bring",
    "",
    "prompt forbids diagnosis",
    "template fallback when the",
    "visitor’s GPU quota runs out",
    ("i", "risk: sounds diagnostic"),
], q=(4,))

# A <-> B
arrow([(400, 225), (400, 366)], "ink"); label(408, 300, "raw text")
arrow([(518, 366), (518, 194)], "emerg"); label(526, 300, "red flag found", cls="al emt")
arrow([(770, 366), (770, 242)], "ink"); label(778, 300, "redacted text + spans")
arrow([(1020, 366), (1020, 262)], "pred"); label(1028, 300, "top-3 + confidence")
arrow([(1200, 366), (1200, 262)], "pred"); label(1208, 318, "rationale + questions")
arrow([(525, 470), (558, 470)], "ink"); label(541, 462, "no flag", "middle", "al sm")
arrow([(800, 470), (833, 470)], "ink"); label(816, 462, "text", "middle", "al sm")
arrow([(1100, 470), (1138, 470)], "pred"); label(1119, 462, "top-3", "middle")

# ---------- lane C: data ----------
text(70, 642, "TRAINING DATA", "rowt")
node(70, 652, 220, 62, "nvidia/Nemotron-PII", [
    "synthetic · CC BY 4.0",
    ("i", "separate folder, not counted"),
], mono=True)
node(70, 722, 220, 52, "TAB · 1,268 docs", [
    "court judgments · MIT",
], mono=True)
node(330, 652, 250, 122, "Redaction training set", [
    "Nemotron-PII (healthcare docs",
    "included) + TAB train split",
    ("i", "domain gap: synthetic + legal,"),
    ("i", "tested on our real posts"),
])
node(620, 652, 245, 122, "bagga005/medredqa", [
    "≈ 40k real r/AskDocs posts",
    "label = specialty of the doctor",
    "who answered",
    ("i", "CC BY-NC-SA · ethics clause"),
    ("i", "skews to dermatology"),
], kind="proposed", mono=True, q=(3, 2))
node(905, 652, 245, 122, "Router training set", [
    "600 gold-train posts (ours)",
    "+ MedRedQA, only if approved",
    ("i", "deduplicated against the test"),
    ("i", "split to stop leakage"),
], q=(6,))
arrow([(290, 683), (328, 683)], "ink")
arrow([(290, 748), (328, 748)], "ink")
arrow([(865, 713), (903, 713)], "ink", dashed=True); label(884, 705, "if OK", "middle", "al sm")
arrow([(570, 650), (570, 594)], "train"); label(578, 634, "trains CRF", cls="al tr")
arrow([(1000, 650), (1000, 594)], "train"); label(1008, 634, "trains LogReg + encoders", cls="al tr")

out.append('<line x1="64" y1="790" x2="880" y2="790" class="divider"/>')
text(70, 804, "MANUAL DATA  ·  what we label or collect ourselves", "rowt")
node(70, 818, 220, 96, "stellalisy/MediQ_AskDocs", [
    "≈ 13.5k unique real posts",
    "rows repeat; skip synthetic/",
    ("i", "MIT card · Reddit origin (Q2)"),
], mono=True, q=(1,))
node(330, 818, 250, 82, "Clean the pool", [
    "dedupe on post text · length filter",
    "strip u/handles and links",
    "sample 1,000 posts",
])
node(330, 916, 250, 80, "Public rubrics", [
    "NHS “which service” guide,",
    "specialty scope-of-practice pages",
])
node(620, 818, 245, 178, "Annotate · the two of us", [
    "1,000 posts, routing labels:",
    ("ind", "primary + acceptable alternates,"),
    ("ind", "urgency tier, ambiguous flag"),
    "300 of them also get PII spans",
    ("ind", "(TAB direct / quasi schema)"),
    "150 double-labelled → Cohen’s κ",
    "≈ 25 person-hours in total",
    ("i", "no Presidio pre-highlighting"),
], kind="human", q=(1,))
node(620, 1008, 245, 50, "Clinician checks 100 posts", [
    ("i", "optional, only if we find one"),
], kind="humanp")
node(905, 818, 245, 240, "Gold set · 1,000 posts", [
    "split by post:",
    ("b", "600 train"),
    ("ind", "→ router training"),
    ("b", "100 dev"),
    ("ind", "→ tunes τ and settings"),
    ("b", "300 test"),
    ("ind", "→ every reported number,"),
    ("ind", "never trained on"),
    "",
    "release labels + MediQ ids,",
    "never the post text",
], q=(6,))
node(70, 1016, 510, 84, "Human baseline form · the new headline", [
    "10–15 international students each read 20 redacted test",
    "posts and pick which doctor they would book",
    ("i", "consent notice up front, as in the class data exercise"),
], kind="human", q=(5,))
arrow([(290, 858), (328, 858)], "ink"); label(309, 851, "posts", "middle", "al sm")
arrow([(580, 858), (618, 858)], "ink"); label(599, 851, "1,000", "middle", "al sm")
arrow([(580, 956), (618, 956)], "ink"); label(599, 949, "guide", "middle", "al sm")
arrow([(742, 1008), (742, 998)], "ink")
arrow([(865, 900), (903, 900)], "ink"); label(884, 892, "labels", "middle")
arrow([(1000, 818), (1000, 776)], "train"); label(1008, 804, "600 train", cls="al tr")
arrow([(1150, 960), (1188, 960)], "train"); label(1169, 952, "test", "middle", "al tr")
arrow([(580, 1086), (1188, 1086)], "train"); label(884, 1080, "their picks", "middle", "al tr")

# evaluation
node(1190, 652, 200, 448, "Evaluate", [
    ("b", "Headline:"),
    "model vs the human baseline",
    "on the 300-post test split",
    "",
    "Top-1 / top-3 accuracy and",
    "macro-F1, vs an “always GP”",
    "baseline; clear vs ambiguous",
    "",
    "Emergency recall on its own",
    "line, target ≈ 100%",
    "",
    "Redaction recall on our 300",
    "PII posts + TAB test split",
    "",
    "Ablation across S / F / O:",
    "macro-F1 · latency ·",
    "cost per 1k · rare classes",
    "",
    "Cohen’s κ (150 posts)",
    "Clinician agreement, if any",
    "Post-launch feedback counts",
])
arrow([(1290, 598), (1290, 650)], "train"); label(1282, 632, "every stage’s outputs", "end", "al tr")
arrow([(1430, 302), (1430, 1070), (1392, 1070)], "fb", dashed=True)
label(1438, 470, "opt-in", cls="al fbt"); label(1438, 484, "feedback", cls="al fbt")

# ---------- right panel ----------
PX = 1500
out.append(f'<rect x="{PX}" y="76" width="380" height="1032" rx="8" class="panel"/>')
text(PX + 18, 102, "HOW TO READ THIS", "rowt")
ly = 126
for cls, lab in [("box", "Decided in our plan"), ("box dash", "Proposed, stretch or waiting on an answer"),
                 ("box human", "Human role"), ("box ext", "Outside our system"),
                 ("box emerg", "Emergency path")]:
    out.append(f'<rect x="{PX+18}" y="{ly-13}" width="36" height="18" rx="4" class="{cls}"/>')
    text(PX + 66, ly, lab)
    ly += 24
ly += 2
for cls, lab, dashed in [("ink", "Text and data", False), ("pred", "Prediction shown to the user", False),
                         ("train", "Trains or evaluates", False), ("emerg", "Emergency short-circuit", False),
                         ("fb", "User feedback", True)]:
    arrow([(PX + 18, ly - 4), (PX + 54, ly - 4)], cls, dashed)
    text(PX + 66, ly, lab)
    ly += 22
ly += 4
for (a, la), (b, lb) in [(("S", "From scratch"), ("F", "Fine-tuned")),
                         (("O", "Off-the-shelf"), ("R", "Rules, not a model type"))]:
    chip(PX + 18, ly, a); text(PX + 40, ly, la)
    chip(PX + 170, ly, b); text(PX + 192, ly, lb)
    ly += 22
qbadge(PX + 30, ly - 4, "")
out[-1] = f'<text x="{PX+30}" y="{ly}" class="qbt" text-anchor="middle">Q</text>'
text(PX + 50, ly, "Question for the instructor, listed below")

ly += 34
text(PX + 18, ly, "QUESTIONS FOR THE INSTRUCTOR", "rowt")
ly += 24
QS = [
    (1, ["Floor: 500 or 1,000 posts? Does labelling existing",
         "public posts (MediQ_AskDocs) count as manual data?"]),
    (2, ["Reddit’s terms ban training on its content without",
         "permission. Is training on Reddit-derived datasets",
         "(MediQ, MedRedQA) acceptable for a class project?"]),
    (3, ["MedRedQA asks users to confirm ethics approval.",
         "Does a course project cover that, or should we skip it?"]),
    (4, ["Free CPU Spaces now need PRO. Is a free ZeroGPU",
         "Space acceptable, or a Colab link as in HW3?"]),
    (5, ["New headline: 10–15 international students label 20",
         "posts in a form. Is that OK, and what consent wording?"]),
    (6, ["Can we train on 600 of our 1,000 labelled posts if",
         "the 300-post test split is never touched?"]),
    (7, ["Does TF-IDF + logistic regression (or a CRF) count",
         "as trained from scratch, or must it be a neural net?"]),
]
for n, lines in QS:
    qbadge(PX + 30, ly - 4, n)
    yy = ly
    for s in lines:
        text(PX + 52, yy, s, "tx q")
        yy += 15.5
    ly = yy + 12

ly += 16
text(PX + 18, ly, "DROPPED, AND WHY", "rowt")
ly += 22
DROPPED = [
    ("Specialty subreddits", ["Reddit’s terms ban model training; most are for",
                              "professionals; r/ENT is not about ENT"]),
    ("iCliniq", ["terms ban scraping; HF copies lack specialty"]),
    ("ai4privacy PII set", ["licence bars derivative works without permission"]),
    ("Self-routing baseline", ["AskDocs posts all come from one general forum"]),
    ("Gemini API", ["free tier may use prompts; keep text inside HF"]),
]
for name, lines in DROPPED:
    text(PX + 18, ly, name, "tx b")
    yy = ly + 15.5
    for s in lines:
        text(PX + 18, yy, s, "tx muted")
        yy += 15.5
    ly = yy + 8
out.append('</svg>')
svg = "\n".join(out)

CSS = """
:root{
  --bg:#EEF2F4; --canvas:#F7F9FA; --ink:#15232C; --muted:#5B6C76;
  --laneA:#E3ECF5; --laneB:#F1F4F6; --laneC:#E6EFE9; --box:#FFFFFF; --line:#9AAAB4;
  --human:#ECE5F7; --humanS:#6B4FA8; --emerg:#C0392B; --emergF:#FBE9E6;
  --pred:#3547B5; --train:#0B7A70; --fb:#A86200; --qb:#15232C; --qbt:#FFFFFF; --sub:#F4F6F8;
  --chip:#E8EDF0;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    color-scheme:dark;
    --bg:#0D1418; --canvas:#111A1F; --ink:#E2E9ED; --muted:#93A4AE;
    --laneA:#15212C; --laneB:#141C21; --laneC:#142019; --box:#1A252C; --line:#4E606B;
    --human:#261F36; --humanS:#A98FE6; --emerg:#FF7B6B; --emergF:#35191A;
    --pred:#8E9CFF; --train:#4CC3B4; --fb:#F0A53A; --qb:#E2E9ED; --qbt:#111A1F; --sub:#141D23;
    --chip:#24313A;
  }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --bg:#0D1418; --canvas:#111A1F; --ink:#E2E9ED; --muted:#93A4AE;
  --laneA:#15212C; --laneB:#141C21; --laneC:#142019; --box:#1A252C; --line:#4E606B;
  --human:#261F36; --humanS:#A98FE6; --emerg:#FF7B6B; --emergF:#35191A;
  --pred:#8E9CFF; --train:#4CC3B4; --fb:#F0A53A; --qb:#E2E9ED; --qbt:#111A1F; --sub:#141D23;
  --chip:#24313A;
}
@page{size:1940px 1330px;margin:0}
body{background:var(--bg);color:var(--ink);margin:0;padding-inline:16px;padding-block:20px;
  font-family:"IBM Plex Sans Condensed","Arial Narrow",system-ui,sans-serif;}
.wrap{overflow-x:auto;}
figure{margin:0 auto;max-width:1900px;}
svg{display:block;width:100%;min-width:1150px;height:auto;font-family:"IBM Plex Sans Condensed","Arial Narrow",system-ui,sans-serif;}
figcaption{max-width:70ch;margin:14px auto 0;color:var(--muted);font-size:14px;line-height:1.5;text-align:center;}
.canvas{fill:var(--canvas);}
.lane{stroke:none;} .lA{fill:var(--laneA);} .lB{fill:var(--laneB);} .lC{fill:var(--laneC);}
.lanet{fill:var(--ink);font-size:13px;font-weight:600;letter-spacing:.08em;}
.lanes{fill:var(--muted);font-size:11.5px;}
.h1{fill:var(--ink);font-size:26px;font-weight:600;font-family:"IBM Plex Serif",Georgia,serif;}
.h1sub{fill:var(--muted);font-size:14px;}
.box{fill:var(--box);stroke:var(--ink);stroke-width:1.3;}
.dash{stroke-dasharray:6 4;}
.human{fill:var(--human);stroke:var(--humanS);}
.ext{fill:transparent;stroke:var(--ink);stroke-dasharray:1.5 3.5;stroke-width:1.6;}
.emerg{fill:var(--emergF);stroke:var(--emerg);stroke-width:2;}
.sub{fill:var(--sub);stroke:var(--line);stroke-dasharray:4 3;}
.bound{fill:none;stroke:var(--ink);stroke-dasharray:1.5 3.5;stroke-width:1.4;}
.panel{fill:var(--box);stroke:var(--line);}
.divider{stroke:var(--line);stroke-dasharray:2 4;}
.ttl{fill:var(--ink);font-size:14.5px;font-weight:600;}
.ttl.mono{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12.5px;}
.ttl.em{fill:var(--emerg);}
.tx{fill:var(--ink);font-size:12.5px;}
.tx.b{font-weight:600;} .tx.sm{font-size:11.5px;} .tx.q{font-size:12.5px;}
.muted{fill:var(--muted);} .it{font-style:italic;}
.rowt{fill:var(--muted);font-size:11px;font-weight:600;letter-spacing:.08em;}
.al{fill:var(--ink);font-size:11.5px;} .al.sm{font-size:10.5px;}
.al.muted{fill:var(--muted);font-style:italic;}
.emt{fill:var(--emerg);font-weight:600;} .tr{fill:var(--train);} .fbt{fill:var(--fb);}
.chip{fill:var(--chip);stroke:var(--ink);stroke-width:.8;}
.chipt{fill:var(--ink);font-size:10px;font-weight:700;font-family:"IBM Plex Mono",ui-monospace,monospace;}
.qb{fill:var(--qb);}
.qbt{fill:var(--qbt);font-size:10px;font-weight:700;font-family:"IBM Plex Mono",ui-monospace,monospace;}
.ar{fill:none;stroke-width:1.8;}
.ar.dash{stroke-dasharray:6 4;}
.ar.ink{stroke:var(--ink);} .ar.pred{stroke:var(--pred);} .ar.train{stroke:var(--train);}
.ar.emerg{stroke:var(--emerg);stroke-width:2.4;} .ar.fb{stroke:var(--fb);}
.mk.ink{fill:var(--ink);} .mk.pred{fill:var(--pred);} .mk.train{fill:var(--train);}
.mk.emerg{fill:var(--emerg);} .mk.fb{fill:var(--fb);}
"""

html = f"""<title>Doc Compass Check-in</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=IBM+Plex+Sans+Condensed:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Serif:wght@600&display=swap">
<style>{CSS}</style>
<div class="wrap"><figure>
{svg}
<figcaption>Red-flag rules check the raw text first. The concern is then redacted, routed to a top-3 of specialties and explained, all inside the Space. Offline, our own 1,000 labelled posts train and test the router, and a form filled in by international students gives the human baseline the model has to beat. Dashed items and Q badges wait on an answer from the instructor.</figcaption>
</figure></div>
"""

Path(__file__).with_name("checkin_figure.html").write_text(html)
print("ok")
