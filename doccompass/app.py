"""The Gradio interface. Run locally with:  python -m doccompass.app"""

import gradio as gr

from .labels import GP
from .pipeline import load_router, route_concern

EXAMPLES = [  # made up by us; never real posts
    "I've had an itchy red rash on both shins for about three weeks and creams from the pharmacy haven't helped.",
    "My right knee swells and hurts after I run, and it clicks when I climb stairs.",
    "I've been feeling very sad and anxious for weeks and I can't focus on anything.",
    "My ears have been ringing for a week and my throat is sore when I swallow.",
    "I get a burning feeling when I pee and I have to go all the time.",
    "I suddenly have crushing chest pain and my left arm feels numb.",
]
DISCLAIMER = ("Doc Compass suggests which kind of doctor to book. It does not diagnose, and it is not medical advice. "
              "Nothing you type is stored. In an emergency call 911.")
CSS = """
.banner {border-radius: 10px; padding: 14px 18px; border-left: 6px solid #3547B5; background: rgba(53, 71, 181, .08);}
.banner.emergency {border-left-color: #C0392B; background: rgba(192, 57, 43, .10);}
.banner p {margin: 0; font-size: 1.05rem;}
"""
EMPTY = ("", None, "", "")


def build_app(router) -> gr.Blocks:
    def run(text: str):
        """Always returns (banner, options, explanation, note)."""
        try:
            result = route_concern(text, router)
        except Exception:  # the page should never show a stack trace
            return ("<div class='banner'><p>Something went wrong on our side. If you are unsure where to go, start with a GP.</p></div>", None, "", "")
        if result["status"] == "invalid":
            return (f"<div class='banner'><p>{result['message']}</p></div>", None, "", "")
        if result["status"] == "emergency":
            reasons = "; ".join(f"“{flag['matched']}” ([{flag['source']}]({flag['url']}))" for flag in result["flags"])
            return (f"<div class='banner emergency'><p><strong>Seek emergency care now.</strong> {result['message']}</p></div>",
                    None, f"Why this was flagged: {reasons}.", "")
        options, headline = result["options"], result["headline"]
        if result["message"]:
            headline += f" {result['message']}"
        note = f"“{GP}” is always a reasonable first step if you are unsure."
        if result["removed"]:
            note += " Removed before routing: " + ", ".join(f"{item['kind']} ({item['text']})" for item in result["removed"]) + "."
        return (f"<div class='banner'><p>{headline}</p></div>",
                {option["label"]: option["confidence"] for option in options}, result["explanation"], note)

    with gr.Blocks(title="Doc Compass") as demo:
        gr.Markdown("# Doc Compass\nWhich kind of doctor should I book? Describe what's going on in your own words.")
        with gr.Row():
            with gr.Column():
                concern = gr.Textbox(label="Your concern", lines=6, placeholder="For example: I've had an itchy rash on both shins for three weeks…")
                submit = gr.Button("Suggest a kind of doctor", variant="primary")
                gr.Examples(EXAMPLES, inputs=concern, label="Try an example (made up)")
            with gr.Column():
                banner = gr.HTML()
                options = gr.Label(label="Top 3, with confidence", num_top_classes=3)
                explanation = gr.Markdown()
                note = gr.Markdown()
        gr.Markdown(f"*{DISCLAIMER}*")
        outputs = [banner, options, explanation, note]
        submit.click(run, concern, outputs)
        concern.submit(run, concern, outputs)
    return demo


if __name__ == "__main__":
    build_app(load_router()).launch(css=CSS)
