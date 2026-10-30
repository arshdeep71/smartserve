"""Generate isolated, explicitly synthetic SmartServe ML demo datasets.

These files are not imported by the production ML loaders or written to MongoDB.
Run with: .venv/Scripts/python.exe data/synthetic_demo/generate_demo_data.py
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent
SEED = 20261030


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def make_feedback(rng, train_count=120, eval_count=30):
    phrases = {
        "positive": ["tasted fresh", "was delicious", "had a nice flavour", "was filling", "was well cooked", "was enjoyable"],
        "spice": ["was too spicy", "had too much chilli", "was hotter than expected", "needs less pepper", "burned my mouth", "was too mild"],
        "quality": ["was cold", "did not taste fresh", "was overcooked", "smelled unpleasant", "was dry", "had poor texture"],
    }
    starts = ["The meal", "Today's lunch", "The dish", "My food", "This plate"]
    endings = ["today", "at lunch", "for me", "this time", "overall"]
    contexts = ["with the usual portion", "from the lunch counter", "during the break", "as served", "on campus", "with lunch"]
    all_rows = []
    used_comments = set()
    for split, count in (("train", train_count), ("eval", eval_count)):
        rows = []
        for i in range(count):
            label = ("positive", "spice", "quality")[i % 3]
            for _attempt in range(1000):
                phrase = rng.choice(phrases[label])
                text = f"{rng.choice(starts)} {phrase} {rng.choice(endings)} {rng.choice(contexts)}."
                if text not in used_comments:
                    used_comments.add(text)
                    break
            else:
                raise RuntimeError("Could not create enough unique synthetic comments")
            row = {"comment": text, "label": label, "source": "synthetic_demo", "is_synthetic": "true", "split": split}
            rows.append(row)
        write_csv(OUT / f"feedback_{split}.csv", ["comment", "label", "source", "is_synthetic", "split"], rows)
        all_rows.extend(rows)
    return all_rows


def make_sales(rng, days=90, end_date=date(2026, 10, 30)):
    catalog = [("demo-ra", "DEMO Rajma Chawal", 35), ("demo-dal", "DEMO Dal Roti", 28), ("demo-chana", "DEMO Chana Chawal", 24)]
    daily = []
    for offset in range(days):
        day = end_date - timedelta(days=days - 1 - offset)
        split = "train" if offset < int(days * .8) else "eval"
        for item_id, name, base in catalog:
            weekend = 1.12 if day.weekday() >= 5 else 1.0
            trend = 1 + offset * .0015
            quantity = max(0, round(rng.gauss(base * weekend * trend, base * .12)))
            daily.append({"date": day.isoformat(), "item_id": item_id, "item": name, "quantity": quantity,
                          "source": "synthetic_demo", "is_synthetic": "true", "split": split})
    fields = ["date", "item_id", "item", "quantity", "source", "is_synthetic", "split"]
    for split in ("train", "eval"):
        write_csv(OUT / f"sales_{split}.csv", fields, [row for row in daily if row["split"] == split])
    return daily


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--end-date", type=date.fromisoformat, default=date(2026, 10, 30))
    args = parser.parse_args()
    rng = random.Random(args.seed)
    feedback = make_feedback(rng)
    sales = make_sales(rng, args.days, args.end_date)
    manifest = {"source": "synthetic_demo", "is_synthetic": True, "seed": args.seed,
                "warning": "Generated data is for software demonstrations only; it is not real sales or customer feedback.",
                "feedback_records": len(feedback), "feedback_train": 120, "feedback_eval": 30,
                "feedback_classes": {label: sum(row["label"] == label for row in feedback) for label in ("positive", "spice", "quality")},
                "sales_rows": len(sales), "sales_days": args.days, "sales_items": 3,
                "sales_train_days": int(args.days * .8), "sales_eval_days": args.days - int(args.days * .8),
                "sales_date_start": min(row["date"] for row in sales), "sales_date_end": max(row["date"] for row in sales)}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
