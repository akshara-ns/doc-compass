"""The Gradio interface. Run locally with:  python -m doccompass.app

The result is drawn like a hospital wayfinding sign: one plaque naming the door to knock on,
with the router's top three and the explanation kept quiet underneath.
"""

import argparse
from html import escape

import gradio as gr

from .explain import QwenExplainer
from .labels import GP, SCOPE
from .pipeline import load_router, route_concern

EXAMPLES = [  # made up by us; never real posts
    "I've had an itchy red rash on both shins for about three weeks and creams from the pharmacy haven't helped.",
    "My right knee swells and hurts after I run, and it clicks when I climb stairs.",
    "I've been feeling very sad and anxious for weeks and I can't focus on anything.",
    "My ears have been ringing for a week and my throat is sore when I swallow.",
    "I get a burning feeling when I pee and I have to go all the time.",
    "I suddenly have crushing chest pain and my left arm feels numb.",
]
EXAMPLE_LABELS = ["Itchy rash", "Sore knee", "Feeling low", "Ringing ears", "Burning when I pee", "Crushing chest pain"]
DISCLAIMER = ("Doc Compass suggests which kind of doctor to book. It does not diagnose, and it is not medical advice. "
              "Nothing you type is stored. In an emergency call 911.")

# Atkinson Hyperlegible was drawn for readers with low vision; it suits a health tool.
THEME = gr.themes.Base(
    font=[gr.themes.GoogleFont("Atkinson Hyperlegible"), "system-ui", "sans-serif"],
    radius_size=gr.themes.sizes.radius_sm,
).set(
    body_background_fill="#F4F7FA", body_background_fill_dark="#0F1820",
    block_shadow="none", block_border_width="1px",
    button_primary_background_fill="#1B4F8F", button_primary_background_fill_dark="#1B4F8F",
    button_primary_background_fill_hover="#163F73", button_primary_text_color="#FFFFFF",
    input_border_color_focus="#1B4F8F",
)

CSS = """
.gradio-container {max-width: 1080px !important; --dc-ink: #13212C; --dc-muted: #586A78; --dc-line: #D3DDE6;
  --dc-card: #FFFFFF; --dc-blue: #1B4F8F; --dc-amber: #F2B441; --dc-red: #B3261E;}
.dark .gradio-container, .gradio-container.dark {--dc-ink: #E6EDF3; --dc-muted: #9AAAB7; --dc-line: #2A3A47; --dc-card: #16222C;}

.dc-header h1 {margin: 0; font-size: 2rem; font-weight: 700; letter-spacing: -0.01em; color: var(--dc-ink);}
.dc-header p {margin: 4px 0 0; font-size: 1.05rem; color: var(--dc-muted); max-width: 60ch;}

/* The sign: the one loud element on the page. */
.dc-sign {display: flex; gap: 18px; align-items: center; padding: 22px 24px; border-radius: 6px;
  background: var(--dc-blue); color: #FFFFFF;}
.dc-sign svg {flex: none; width: 54px; height: 54px;}
.dc-sign p {margin: 0; color: inherit;}
.dc-sign .dc-small {font-size: 0.98rem; opacity: 0.92;}
.dc-sign .dc-big {font-size: 2.1rem; line-height: 1.12; font-weight: 700; letter-spacing: -0.01em; margin: 2px 0 4px;}
.dc-sign .dc-sub {font-size: 0.98rem; opacity: 0.92; max-width: 46ch;}
.dc-sign.dc-junction {background: var(--dc-amber); color: #1C1503;}
/* Gradio styles <p> and SVG shapes inside gr.HTML with its own colours; force the sign colours. */
.dc-sign:not(.dc-empty) p {color: #FFFFFF !important;}
.dc-sign.dc-junction p {color: #1C1503 !important;}
.dc-sign:not(.dc-empty) svg [stroke] {stroke: #FFFFFF !important;} .dc-sign:not(.dc-empty) svg [fill="currentColor"] {fill: #FFFFFF !important;}
.dc-sign.dc-junction svg [stroke] {stroke: #1C1503 !important;} .dc-sign.dc-junction svg [fill="currentColor"] {fill: #1C1503 !important;}
.dc-sign.dc-emergency {background: var(--dc-red);}
.dc-sign.dc-empty {background: transparent; color: var(--dc-muted); border: 1.5px dashed var(--dc-line);}
.dc-sign.dc-empty .dc-big {font-size: 1.25rem; color: var(--dc-ink);}

/* The router's top three, as a quiet directory under the sign. */
.dc-doors {margin: 14px 0 0; padding: 14px 18px; border: 1px solid var(--dc-line); border-radius: 6px; background: var(--dc-card);}
.dc-doors h2 {margin: 0 0 8px; font-size: 0.95rem; font-weight: 400; color: var(--dc-muted);}
.dc-door {display: grid; grid-template-columns: minmax(9rem, 13rem) 1fr 3.2rem; gap: 12px; align-items: center; padding: 5px 0;
  color: var(--dc-ink); font-size: 1rem;}
.dc-door .dc-track {height: 8px; border-radius: 4px; background: var(--dc-line); overflow: hidden;}
.dc-door .dc-fill {display: block; height: 100%; background: var(--dc-blue); border-radius: 4px;}
.dark .dc-door .dc-fill {background: #6FA8EA;}
.dc-door .dc-pct {text-align: right; font-variant-numeric: tabular-nums; color: var(--dc-muted);}

.dc-explain {padding: 2px 4px; font-size: 1.02rem; line-height: 1.55;}
.dc-explain p, .dc-explain li {max-width: 62ch;}
.dc-note, .dc-note p {font-size: 0.92rem; color: var(--dc-muted) !important;}
.dc-footer p {margin: 8px 0 0; font-size: 0.9rem; color: var(--dc-muted); max-width: 80ch;}
@media (max-width: 640px) {.dc-sign .dc-big {font-size: 1.6rem;} .dc-door {grid-template-columns: 8rem 1fr 3rem;}}
"""

_ARROW = ('<svg viewBox="0 0 54 54" aria-hidden="true"><circle cx="27" cy="27" r="25" fill="none" stroke="currentColor" stroke-width="3"/>'
          '<path d="M15 27h22M29 18l9 9-9 9" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/></svg>')
_FORK = ('<svg viewBox="0 0 54 54" aria-hidden="true"><circle cx="27" cy="27" r="25" fill="none" stroke="currentColor" stroke-width="3"/>'
         '<path d="M27 41V28M27 28l-10-10M27 28l10-10M17 25v-7h7M37 25v-7h-7" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>')
_ALERT = ('<svg viewBox="0 0 54 54" aria-hidden="true"><circle cx="27" cy="27" r="25" fill="none" stroke="currentColor" stroke-width="3"/>'
          '<path d="M27 14v18" stroke="currentColor" stroke-width="4.5" stroke-linecap="round"/><circle cx="27" cy="40" r="2.8" fill="currentColor"/></svg>')


def _sign(kind: str, icon: str, small: str, big: str, sub: str = "") -> str:
    sub_html = f"<p class='dc-sub'>{sub}</p>" if sub else ""
    return (f"<div class='dc-sign dc-{kind}' role='status'>{icon}<div><p class='dc-small'>{small}</p>"
            f"<p class='dc-big'>{big}</p>{sub_html}</div></div>")


EMPTY_SIGN = _sign("empty", "", "Your result appears here", "Describe what's going on, then press the button.",
                   "We check for emergency signs first, then suggest up to three kinds of doctor.")


def _doors(options: list[dict]) -> str:
    rows = "".join(
        f"<div class='dc-door'><span>{escape(option['label'])}</span>"
        f"<span class='dc-track'><span class='dc-fill' style='width:{option['confidence']:.0%}'></span></span>"
        f"<span class='dc-pct'>{option['confidence']:.0%}</span></div>" for option in options)
    return f"<div class='dc-doors'><h2>How sure the router is</h2>{rows}</div>"


def render(result: dict) -> tuple[str, str, str]:
    """Turn a pipeline result into (sign and directory HTML, explanation, small note)."""
    if result["status"] == "invalid":
        return _sign("empty", "", "Nothing to route yet", escape(result["message"])), "", ""
    if result["status"] == "emergency":
        reasons = "; ".join(
            (f"“{escape(flag['matched'])}”" if flag["matched"] else "a second, language-model check judged that this may match a published warning sign")
            + f" ([{flag['source']}]({flag['url']}))" for flag in result["flags"])
        sign = _sign("emergency", _ALERT, "This may be an emergency", "Seek emergency care now",
                     escape(result["message"].replace("This may be an emergency. ", "")))
        return sign, f"Why this was flagged: {reasons}. The rest of the app did not run.", ""

    options = result["options"]
    first = options[0]["label"]
    second = options[1]["label"] if len(options) > 1 else None
    if not result["unsure"] or second is None:
        if first == GP:
            sign = _sign("routed", _ARROW, "Your first step", GP, "A GP treats common problems and can refer you on.")
        else:
            sign = _sign("routed", _ARROW, "Book an appointment with", first, f"Covers {SCOPE[first]}.")
    elif GP in (first, second):
        other = next((option["label"] for option in options if option["label"] != GP), None)
        sign = _sign("junction", _FORK, "Not clear-cut, so you decide", GP,
                     f"Or {other}, if that fits what you are feeling better." if other else "")
    else:
        sign = _sign("junction", _FORK, "Two doors could fit, so you decide", f"{first} or {second}",
                     "If neither clearly fits, start with a GP.")

    note = f"“{GP}” is always a reasonable first step if you are unsure."
    if result["message"]:
        note = f"{result['message']} {note}"
    if result["removed"]:
        note += " Removed before routing: " + ", ".join(f"{item['kind']} ({escape(item['text'])})" for item in result["removed"]) + "."
    if result["explained_by"] != "template":
        note += f" The reason and questions were written by {result['explained_by']}; the choice of doctor was not."
    return sign + _doors(options), result["explanation"], note


def build_app(router, explainer=None) -> gr.Blocks:
    def run(text: str):
        """Always returns (sign, explanation, note)."""
        try:
            return render(route_concern(text, router, explainer))
        except Exception:  # the page should never show a stack trace
            return _sign("empty", "", "Something went wrong on our side", "If you are unsure where to go, start with a GP."), "", ""

    with gr.Blocks(title="Doc Compass") as demo:
        gr.HTML("<div class='dc-header'><h1>Doc Compass</h1>"
                "<p>Tell us what's going on in your own words. We'll point you to the kind of doctor to book.</p></div>")
        with gr.Row():
            with gr.Column(scale=5):
                concern = gr.Textbox(label="What's going on?", lines=6, placeholder="For example: I've had an itchy rash on both shins for three weeks…")
                submit = gr.Button("Suggest a kind of doctor", variant="primary", size="lg")
                gr.Examples(EXAMPLES, inputs=concern, example_labels=EXAMPLE_LABELS, label="Or try a made-up example")
            with gr.Column(scale=6):
                sign = gr.HTML(EMPTY_SIGN, padding=False)
                explanation = gr.Markdown(elem_classes="dc-explain")
                note = gr.Markdown(elem_classes="dc-note")
        gr.HTML(f"<div class='dc-footer'><p>{DISCLAIMER}</p></div>")
        outputs = [sign, explanation, note]
        submit.click(run, concern, outputs)
        concern.submit(run, concern, outputs)
    return demo


def launch(router, explainer=None, **options):
    """Build and launch with the app's theme and styles; extra options go to Gradio's launch()."""
    return build_app(router, explainer).launch(css=CSS, theme=THEME, **options)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Doc Compass app.")
    parser.add_argument("--llm", action="store_true", help="write explanations with Qwen (downloads about 3 GB the first time)")
    parser.add_argument("--share", action="store_true", help="also create a temporary public link")
    args = parser.parse_args()
    launch(load_router(), QwenExplainer() if args.llm else None, share=args.share)
