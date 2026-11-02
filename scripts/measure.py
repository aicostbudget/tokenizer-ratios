"""Count every sample with a tiktoken encoding and report characters and words per token by category.

Usage: python scripts/measure.py [--encoding o200k_base] [--out results/chars-per-token-o200k_base.json]
"""
import argparse, json
from pathlib import Path
import tiktoken

ROOT = Path(__file__).resolve().parent.parent

parser = argparse.ArgumentParser()
parser.add_argument("--encoding", default="o200k_base")
parser.add_argument("--out", default=None)
args = parser.parse_args()

enc = tiktoken.get_encoding(args.encoding)
samples = [json.loads(line) for line in open(ROOT / "data" / "samples.jsonl", encoding="utf8")]

categories = {}
for s in samples:
    tokens = len(enc.encode(s["text"]))
    c = categories.setdefault(s["category"], {"samples": 0, "characters": 0, "tokens": 0, "words": 0, "perSample": []})
    c["samples"] += 1
    c["characters"] += len(s["text"])
    c["tokens"] += tokens
    c["words"] += len(s["text"].split())
    c["perSample"].append(len(s["text"]) / tokens)

out = {"encoding": args.encoding, "tiktoken": tiktoken.__version__, "samples": len(samples), "categories": {}}
for name, c in sorted(categories.items(), key=lambda kv: -kv[1]["characters"] / kv[1]["tokens"]):
    out["categories"][name] = {
        "samples": c["samples"],
        "characters": c["characters"],
        "tokens": c["tokens"],
        "charsPerToken": round(c["characters"] / c["tokens"], 3),
        "wordsPerToken": round(c["words"] / c["tokens"], 3),
        "charsDividedBy4Ratio": round(c["characters"] / 4 / c["tokens"], 3),
        "minCharsPerToken": round(min(c["perSample"]), 3),
        "maxCharsPerToken": round(max(c["perSample"]), 3),
    }

target = Path(args.out) if args.out else ROOT / "results" / f"chars-per-token-{args.encoding}.json"
target.write_text(json.dumps(out, indent=2) + "\n", encoding="utf8")
print(f"{'category':<8} {'n':>4} {'chars/tok':>9} {'words/tok':>9} {'chars/4':>8}")
for name, r in out["categories"].items():
    print(f"{name:<8} {r['samples']:>4} {r['charsPerToken']:>9} {r['wordsPerToken']:>9} {r['charsDividedBy4Ratio']:>8}")
