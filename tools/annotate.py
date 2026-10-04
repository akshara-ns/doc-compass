"""Local labelling tool. One post at a time; saves ids and labels only.

Run:  python tools/annotate.py --annotator sohum
Your labels go to data/manual/<annotator>.labels.csv, which is safe to commit.
Test posts come first and are shown with nothing pre-selected. Train and dev posts
show a first-pass label, if one exists, for you to confirm or change.
"""

import argparse
import sys
from pathlib import Path

import gradio as gr
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doccompass import paths
from doccompass.labels import ANNOTATION_CHOICES, EMERGENCY, LABELS, SKIP, URGENCY

COLUMNS = ["id", "part", "annotator", "primary", "alternate", "urgency", "ambiguous"]
NO_ALTERNATE = "(none)"


def load_queue(annotator: str) -> pd.DataFrame:
    """This annotator's posts, test first, with any first-pass labels attached."""
    if not paths.POOL.exists():
        sys.exit("No pool found. Run: python scripts/prepare_data.py")
    pool = pd.read_csv(paths.POOL)
    mine = pool[pool["annotators"].str.split("+").map(lambda names: annotator in names)]
    if mine.empty:
        sys.exit(f"No posts are assigned to '{annotator}'. Names in the pool: {sorted(set('+'.join(pool['annotators']).split('+')))}")
    mine = pd.concat([mine[mine["part"] == "test"], mine[mine["part"] != "test"]])
    if paths.DRAFT_LABELS.exists():
        draft = pd.read_csv(paths.DRAFT_LABELS).add_prefix("draft_").rename(columns={"draft_id": "id"})
        mine = mine.merge(draft, on="id", how="left")
    return mine.reset_index(drop=True)


def build(annotator: str) -> gr.Blocks:
    queue = load_queue(annotator)
    out_path = paths.MANUAL / f"{annotator}.labels.csv"
    saved = pd.read_csv(out_path, dtype=str).fillna("") if out_path.exists() else pd.DataFrame(columns=COLUMNS)
    labels = {row["id"]: row for row in saved.to_dict("records")}

    def first_unlabelled() -> int:
        todo = [i for i, post_id in enumerate(queue["id"]) if post_id not in labels]
        return todo[0] if todo else len(queue) - 1

    def show(position: int, message: str = ""):
        """Everything the page displays for one post."""
        post = queue.iloc[position]
        done = sum(post_id in labels for post_id in queue["id"])
        header = f"**Post {position + 1} of {len(queue)}** · {post['part']} · {done} labelled"
        if post["id"] in labels:  # revisiting: show what was saved
            row = labels[post["id"]]
            values = (row["primary"], row["alternate"] or NO_ALTERNATE, row["urgency"] or URGENCY[0], row["ambiguous"] == "True")
            header += " · already saved"
        elif post["part"] != "test" and isinstance(post.get("draft_primary"), str):
            alternate = post.get("draft_alternate")
            urgency = post.get("draft_urgency")
            values = (post["draft_primary"], alternate if isinstance(alternate, str) else NO_ALTERNATE,
                      urgency if isinstance(urgency, str) else URGENCY[0], False)
            header += f" · first pass: {post['draft_primary']}"
        else:  # test posts are labelled with nothing pre-selected
            values = (None, NO_ALTERNATE, URGENCY[0], False)
        return (position, header, post["text"], *values, message)

    def save(position: int, primary, alternate, urgency, ambiguous):
        if primary is None:
            return show(position, "Pick a primary label first.")
        post = queue.iloc[position]
        is_routed = primary in LABELS
        labels[post["id"]] = {
            "id": post["id"], "part": post["part"], "annotator": annotator, "primary": primary,
            "alternate": alternate if is_routed and alternate not in (NO_ALTERNATE, primary) else "",
            "urgency": "emergency" if primary == EMERGENCY else (urgency if is_routed else ""),
            "ambiguous": str(bool(ambiguous and primary != SKIP)),
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(labels.values(), columns=COLUMNS).to_csv(out_path, index=False)
        if position + 1 >= len(queue):
            return show(position, "Saved. That was the last post.")
        return show(position + 1, "Saved.")

    def back(position: int):
        return show(max(position - 1, 0))

    with gr.Blocks(title="Doc Compass labelling") as page:
        position = gr.State(0)
        header = gr.Markdown()
        post_text = gr.Textbox(label="Post", lines=14, interactive=False)
        primary = gr.Radio(ANNOTATION_CHOICES, label="Which kind of doctor should this person book?")
        with gr.Row():
            alternate = gr.Dropdown([NO_ALTERNATE] + LABELS, value=NO_ALTERNATE, label="Also acceptable (optional)")
            urgency = gr.Radio(URGENCY, value=URGENCY[0], label="Urgency")
            ambiguous = gr.Checkbox(label="Ambiguous: I couldn't really decide")
        with gr.Row():
            back_button = gr.Button("Back")
            save_button = gr.Button("Save and next", variant="primary")
        message = gr.Markdown()

        outputs = [position, header, post_text, primary, alternate, urgency, ambiguous, message]
        page.load(lambda: show(first_unlabelled()), outputs=outputs)
        save_button.click(save, [position, primary, alternate, urgency, ambiguous], outputs)
        back_button.click(back, [position], outputs)
    return page


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--annotator", required=True, help="your name as it appears in the pool, e.g. sohum")
    build(parser.parse_args().annotator.lower()).launch(inbrowser=True)
