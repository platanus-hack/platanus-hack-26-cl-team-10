"""Convierte subtítulos automáticos de YouTube (json3) en Markdown con marcas de tiempo,
partido por los capítulos de la descripción del video.

Uso: python3 -I scripts/yt_transcript.py <id>.es-orig.json3 <id>.description <salida.md> "<título>" <url>
"""
import json
import re
import sys

PARAGRAPH_SECONDS = 30


def fmt(ms: int) -> str:
    s = ms // 1000
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}"


def parse_chapters(description: str) -> list[tuple[int, str]]:
    chapters = []
    for line in description.splitlines():
        m = re.match(r"^\s*((?:\d+:)?\d+:\d{2})\s*-?\s*(.+)$", line)
        if not m:
            continue
        parts = [int(p) for p in m.group(1).split(":")]
        while len(parts) < 3:
            parts.insert(0, 0)
        h, mi, se = parts
        chapters.append(((h * 3600 + mi * 60 + se) * 1000, m.group(2).strip()))
    return chapters


def words(events: list[dict]) -> list[tuple[int, str]]:
    out = []
    for ev in events:
        text = "".join(seg.get("utf8", "") for seg in ev.get("segs") or []).replace("\n", " ").strip()
        if text:
            out.append((ev.get("tStartMs", 0), text + " "))
    return out


def main() -> None:
    subs_path, desc_path, out_path, title, url = sys.argv[1:6]
    with open(subs_path, encoding="utf-8") as f:
        events = json.load(f)["events"]
    with open(desc_path, encoding="utf-8") as f:
        description = f.read()
    chapters = parse_chapters(description) or [(0, "Video completo")]
    toks = words(events)

    lines = [
        f"# {title}",
        "",
        f"> Fuente: <{url}>. Transcripción automática de YouTube (español), sin corregir: los nombres propios y términos técnicos pueden venir mal escritos. Los capítulos salen de la descripción del video. Generado con `scripts/yt_transcript.py`.",
        "",
        "## Descripción del video",
        "",
        "```text",
        description.strip(),
        "```",
        "",
    ]
    bounds = chapters + [(10**12, "")]
    i = 0
    for (c_start, c_title), (c_end, _) in zip(bounds, bounds[1:]):
        lines += [f"## [{fmt(c_start)}] {c_title}", ""]
        para: list[str] = []
        para_start = None
        while i < len(toks) and toks[i][0] < c_end:
            t, w = toks[i]
            if para_start is None:
                para_start = t
            para.append(w)
            if t - para_start >= PARAGRAPH_SECONDS * 1000:
                lines += [f"**[{fmt(para_start)}]** " + re.sub(r"\s+", " ", "".join(para)).strip(), ""]
                para, para_start = [], None
            i += 1
        if para:
            lines += [f"**[{fmt(para_start)}]** " + re.sub(r"\s+", " ", "".join(para)).strip(), ""]
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
