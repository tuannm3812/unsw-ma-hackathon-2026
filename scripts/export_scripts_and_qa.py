#!/usr/bin/env python3
"""Extract two single-purpose reading files out of the two prep documents:

  docs/presentation/speaker_scripts.md  - just the ten spoken scripts
  docs/presentation/qa_answers.md       - just the Q&A entries

Both are DERIVED. Never edit them by hand; edit the source document
(deck_content.md / qa_pack.md) and re-run this script. The header of each
generated file says so, and the script asserts on anything it cannot parse
rather than silently emitting a short file.

Usage:  python3 scripts/export_scripts_and_qa.py
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DECK = REPO / "docs/presentation/deck_content.md"
QA = REPO / "docs/presentation/qa_pack.md"
OUT_SCRIPTS = REPO / "docs/presentation/speaker_scripts.md"
OUT_QA = REPO / "docs/presentation/qa_answers.md"

# The deck carries ten slides, each with exactly one script block.
EXPECTED_SLIDES = 10
# Rehearsal pacing, matching the two rates quoted in the deck brief.
MEASURED_WPM = 130
PRESENTATION_WPM = 140

# Four scripts enumerate parallel items in prose. The rehearsal copy breaks
# those into bullets so a presenter can find their place at a glance; the deck
# brief and the pptx speaker notes keep the spoken paragraph unchanged.
# "items" are the exact substrings each bullet starts at, "tail" the substring
# where prose resumes. split_bullets() asserts the pieces rejoin to the source
# text character for character, so this can never alter a spoken word.
SCRIPT_BULLETS = {
    3: {"items": ["For prediction:", "For the framing claims:"],
        "tail": "Most headline-looking results did not survive."},
    6: {"items": ["Urgency language looked like",
                  "Family framing \u2014 and here our own first version",
                  "Sentiment is the honest illustration:"],
        "tail": "We'd rather report no robust evidence"},
    8: {"items": ["One: don't ship writing tips",
                  "Two \u2014 an experiment, not an action",
                  "Three \u2014 review, not change"],
        "tail": "And the classifier stays a prototype"},
    9: {"items": ["Association, never causation",
                  "We measure how fast funded loans fund",
                  "And our framing measures are transparent"],
        "tail": "We'd rather you know exactly"},
}

SLIDE_RE = re.compile(r"^### Slide (\d+) · (.+)$")
SCRIPT_RE = re.compile(r"^> \*\*Script · (.+?) · ~(.+?)\*\* — (.+)$")
QA_RE = re.compile(r"^#### ([A-F]\d+) · (.+)$")
GROUP_RE = re.compile(r"^### (.+)$")


def parse_duration(text: str) -> int:
    """'30s' / '1m50s' / '2m' -> seconds."""
    m = re.fullmatch(r"(?:(\d+)m)?(?:(\d+)s)?", text.strip())
    assert m and (m.group(1) or m.group(2)), f"unparsed duration: {text!r}"
    return int(m.group(1) or 0) * 60 + int(m.group(2) or 0)


def mmss(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02d}"


def split_bullets(spoken: str, spec: dict) -> tuple[str, list[str], str]:
    """Cut one spoken paragraph into lead-in, bullets, and closing prose."""
    marks = list(spec["items"]) + ([spec["tail"]] if spec["tail"] else [])
    cuts = []
    for mark in marks:
        assert spoken.count(mark) == 1, f"marker not unique: {mark!r}"
        cuts.append(spoken.index(mark))
    assert cuts == sorted(cuts), f"markers out of order: {marks}"
    bounds = [0] + cuts + [len(spoken)]
    pieces = [spoken[a:b] for a, b in zip(bounds, bounds[1:])]
    assert "".join(pieces) == spoken, "bullet split lost or altered text"
    lead = pieces[0].strip()
    tail = pieces[-1].strip() if spec["tail"] else ""
    items = [x.strip() for x in (pieces[1:-1] if spec["tail"] else pieces[1:])]
    assert lead and all(items), "empty lead-in or bullet"
    return lead, items, tail


def extract_scripts() -> list[dict]:
    """One record per slide, in deck order."""
    slides: list[dict] = []
    for line in DECK.read_text(encoding="utf-8").split("\n"):
        m = SLIDE_RE.match(line)
        if m:
            slides.append({"num": int(m.group(1)), "title": m.group(2), "script": None})
            continue
        m = SCRIPT_RE.match(line)
        if m:
            assert slides, "script block before any slide heading"
            assert slides[-1]["script"] is None, (
                f"slide {slides[-1]['num']} has more than one script block"
            )
            slides[-1].update(
                speaker=m.group(1), budget=m.group(2), script=m.group(3).strip()
            )
    assert len(slides) == EXPECTED_SLIDES, f"found {len(slides)} slides, expected {EXPECTED_SLIDES}"
    missing = [s["num"] for s in slides if s["script"] is None]
    assert not missing, f"slides without a script block: {missing}"
    return slides


def write_scripts(slides: list[dict]) -> None:
    total_words = 0
    total_budget = 0
    body: list[str] = []
    for s in slides:
        # Spoken words only: the script is a quoted line, strip the quotes.
        spoken = s["script"].strip()
        if spoken.startswith('"') and spoken.endswith('"'):
            spoken = spoken[1:-1]
        words = len(spoken.split())
        total_words += words
        total_budget += parse_duration(s["budget"])
        body += [
            f"## Slide {s['num']} · {s['title']}",
            "",
            f"**{s['speaker']}** · budget ~{s['budget']} · {words} words "
            f"(~{mmss(round(words / MEASURED_WPM * 60))} at {MEASURED_WPM} wpm)",
            "",
        ]
        if s["num"] in SCRIPT_BULLETS:
            lead, items, tail = split_bullets(spoken, SCRIPT_BULLETS[s["num"]])
            body += [lead, ""] + [f"- {x}" for x in items] + [""]
            if tail:
                body += [tail, ""]
        else:
            body += [spoken, ""]

    at_measured = round(total_words / MEASURED_WPM * 60)
    at_presentation = round(total_words / PRESENTATION_WPM * 60)
    head = [
        "# Speaker scripts",
        "",
        "Spoken lines only, in running order — the rehearsal copy. "
        "Everything else (headlines, exhibits, backup numbers) lives in the deck brief.",
        "",
        f"**{total_words} words** across {len(slides)} slides · "
        f"**{mmss(at_measured)}** at a measured {MEASURED_WPM} wpm · "
        f"**{mmss(at_presentation)}** at a normal {PRESENTATION_WPM} wpm · "
        f"the per-slide budgets sum to {mmss(total_budget)}. "
        "Hard cut-off is 10:00; target finishing by 9:00.",
        "",
        "> Generated by `scripts/export_scripts_and_qa.py` from "
        "`docs/presentation/deck_content.md`. Edit the deck brief, not this file.",
        "",
        "---",
        "",
    ]
    OUT_SCRIPTS.write_text("\n".join(head + body), encoding="utf-8")
    print(
        f"{OUT_SCRIPTS.relative_to(REPO)}: {len(slides)} scripts, {total_words} words, "
        f"{mmss(at_measured)} at {MEASURED_WPM} wpm"
    )


def extract_qa() -> tuple[list[dict], dict[str, str]]:
    """One record per Q&A entry, plus the group heading each letter belongs to.

    Grouping is by letter prefix rather than by position: D6 was appended to
    the pack after the criteria-mapping section, so its nearest preceding
    heading is the wrong one. The letter is the reliable key.
    """
    lines = QA.read_text(encoding="utf-8").split("\n")
    entries: list[dict] = []
    groups: dict[str, str] = {}
    current_group = None
    for line in lines:
        g = GROUP_RE.match(line)
        if g and not QA_RE.match(line):
            current_group = g.group(1).strip()
            continue
        m = QA_RE.match(line)
        if m:
            qid, question = m.group(1), m.group(2).strip()
            letter = qid[0]
            # First entry of a letter fixes that letter's group heading.
            if letter not in groups:
                assert current_group, f"{qid} appears before any group heading"
                groups[letter] = current_group
            entries.append({"id": qid, "letter": letter, "question": question, "body": []})
            continue
        if entries:
            entries[-1]["body"].append(line)
    assert entries, "no Q&A entries found"
    for e in entries:
        while e["body"] and not e["body"][-1].strip():
            e["body"].pop()
        assert e["body"], f"{e['id']} has an empty body"
    return entries, groups


def write_qa(entries: list[dict], groups: dict[str, str]) -> None:
    order = sorted(groups, key=lambda ltr: min(i for i, e in enumerate(entries) if e["letter"] == ltr))
    by_letter = {ltr: [e for e in entries if e["letter"] == ltr] for ltr in order}
    for ltr in order:
        by_letter[ltr].sort(key=lambda e: int(e["id"][1:]))

    hard = [e["id"] for ltr in order for e in by_letter[ltr] if "`[HARD]`" in e["question"]]

    index: list[str] = ["## Index", ""]
    body: list[str] = []
    for ltr in order:
        index.append(f"**{groups[ltr]}**")
        index.append("")
        body += [f"## {groups[ltr]}", ""]
        for e in by_letter[ltr]:
            question = e["question"].replace(" `[HARD]`", "")
            flag = " · **hard**" if "`[HARD]`" in e["question"] else ""
            index.append(f"- **{e['id']}** · {question}{flag}")
            body += [f"### {e['id']} · {question}{flag}", ""] + e["body"] + [""]
        index.append("")

    head = [
        "# Q&A answers",
        "",
        "Every prepared answer, and nothing else — the question-time copy. "
        "The report half of the pack (findings, limitations, crib sheet) stays in the Q&A pack itself.",
        "",
        f"**{len(entries)} questions** in {len(order)} groups · "
        f"**{len(hard)} flagged hard**: {', '.join(hard)}.",
        "",
        "> Generated by `scripts/export_scripts_and_qa.py` from "
        "`docs/presentation/qa_pack.md`. Edit the Q&A pack, not this file. "
        "Grouped by question letter, so D6 sits with the other methods questions "
        "rather than at the end of the source document.",
        "",
        "---",
        "",
    ]
    OUT_QA.write_text("\n".join(head + index + ["---", ""] + body), encoding="utf-8")
    print(
        f"{OUT_QA.relative_to(REPO)}: {len(entries)} questions in {len(order)} groups, "
        f"{len(hard)} hard"
    )


def main() -> None:
    write_scripts(extract_scripts())
    write_qa(*extract_qa())


if __name__ == "__main__":
    main()
