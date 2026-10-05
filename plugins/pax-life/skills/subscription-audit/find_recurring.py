"""Find recurring charges (subscriptions) in bank or credit-card CSV exports. Standard library only.

Usage:
    python find_recurring.py [files or folders ...] [--out recurring.csv] [--dayfirst]
                             [--charges positive|negative] [--min-count 2]

With no paths, reads every *.csv in the current folder. Prints a Markdown table plus monthly/annual totals.
Tolerates common bank layouts: Date/Description/Amount, Debit/Credit columns, Withdrawal/Deposit columns,
and a few junk lines above the header row. Nothing is uploaded anywhere.
"""
import argparse, csv, re, statistics, sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DATE_COLS = ["transaction date", "trans. date", "trans date", "date", "posting date", "posted date", "post date"]
DESC_COLS = ["description", "merchant", "payee", "name", "transaction description", "details", "memo", "narrative"]
AMOUNT_COLS = ["amount", "transaction amount", "amount (usd)", "billing amount"]
DEBIT_COLS = ["debit", "debit amount", "withdrawal", "withdrawals", "withdrawal amount", "charges", "money out"]
CREDIT_COLS = ["credit", "credit amount", "deposit", "deposits", "deposit amount", "payments", "money in"]

DATE_FORMATS_US = ["%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%Y/%m/%d", "%m-%d-%Y", "%b %d, %Y", "%d %b %Y", "%Y%m%d"]
DATE_FORMATS_DAYFIRST = ["%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d %b %Y", "%b %d, %Y", "%Y%m%d"]

# Cadence name, min days, max days, multiplier to get a monthly cost
CADENCES = [("weekly", 5, 9, 52 / 12), ("every 2 weeks", 12, 16, 26 / 12), ("monthly", 25, 35, 1.0),
            ("every 2 months", 55, 66, 0.5), ("quarterly", 84, 98, 1 / 3), ("twice a year", 170, 195, 1 / 6),
            ("annual", 350, 380, 1 / 12)]

NOISE = re.compile(r"\b(pos|debit|purchase|recurring|card|visa|mc|ach|online|payment|pmt|web|id|ref|"
                   r"checkcard|dbt|crd|pre-?authorized|autopay|bill ?pay)\b", re.I)
NOT_SUBSCRIPTIONS = re.compile(r"\b(transfer|xfer|zelle|venmo|atm|withdrawal|deposit|interest|payroll|"
                               r"thank you|autopay payment|credit card payment)\b", re.I)


def find_col(headers, names):
    low = [h.strip().lower() for h in headers]
    for n in names:
        if n in low:
            return low.index(n)
    return None


def read_rows(path):
    """Yield (headers, rows) after skipping any preamble above the real header row."""
    text = Path(path).read_text(encoding="utf-8-sig", errors="replace").splitlines()
    rows = list(csv.reader(text))
    for i, row in enumerate(rows[:30]):
        if find_col(row, DATE_COLS) is not None and find_col(row, DESC_COLS) is not None:
            return row, rows[i + 1:]
    raise ValueError(f"{path}: could not find a header row with a date and description column")


def parse_money(s):
    s = (s or "").strip().replace("$", "").replace(",", "").replace("£", "").replace("€", "")
    if not s:
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def parse_date(s, formats):
    s = (s or "").strip()
    for f in formats:
        try:
            return datetime.strptime(s, f).date()
        except ValueError:
            pass
    return None


def merchant_key(desc):
    d = desc.upper()
    d = re.sub(r"https?://\S+|WWW\.|\.(COM|NET|ORG|CO|IO|TV)\b|\b(INC|LLC|LTD)\b", " ", d)
    d = re.sub(r"[#*]\S*|\d[\d\-/.:]*", " ", d)       # reference numbers, dates, store numbers
    d = NOISE.sub(" ", d)
    d = re.sub(r"[^A-Z& ]", " ", d)
    words = [w for w in d.split() if len(w) > 1]
    return " ".join(words[:3]) or desc.strip().upper()[:20]


def load(paths, formats, charges_sign):
    charges = []
    for p in paths:
        headers, rows = read_rows(p)
        di, si = find_col(headers, DATE_COLS), find_col(headers, DESC_COLS)
        ai, dbi, cri = find_col(headers, AMOUNT_COLS), find_col(headers, DEBIT_COLS), find_col(headers, CREDIT_COLS)
        if ai is None and dbi is None:
            raise ValueError(f"{p}: no Amount or Debit/Withdrawal column found (headers: {headers})")
        raw = []
        for r in rows:
            if len(r) <= max(i for i in (di, si, ai, dbi) if i is not None):
                continue
            date = parse_date(r[di], formats)
            if not date:
                continue
            if dbi is not None:                       # separate debit column: charges are what's in it
                v = parse_money(r[dbi])
                amt = abs(v) if v else None
            else:
                amt = parse_money(r[ai])
            if amt:
                raw.append((date, r[si].strip(), amt))
        if ai is not None and dbi is None:            # single Amount column: work out which sign means a charge
            sign = charges_sign
            if sign is None:
                negs = sum(1 for _, _, a in raw if a < 0)
                sign = "negative" if negs >= len(raw) / 2 else "positive"
            raw = [(d, s, abs(a)) for d, s, a in raw if (a < 0) == (sign == "negative")]
        charges += [(d, s, a, Path(p).name) for d, s, a in raw if not NOT_SUBSCRIPTIONS.search(s)]
    return charges


def classify(days):
    for name, lo, hi, mult in CADENCES:
        if lo <= days <= hi:
            return name, mult
    return None, None


def analyse(charges, min_count):
    groups = defaultdict(list)
    for d, s, a, f in charges:
        groups[merchant_key(s)].append((d, a, s))
    found = []
    for key, items in groups.items():
        items.sort()
        if len(items) < min_count:
            continue
        gaps = [(b[0] - a[0]).days for a, b in zip(items, items[1:]) if (b[0] - a[0]).days > 2]
        if not gaps:
            continue
        cadence, mult = classify(statistics.median(gaps))
        amounts = [a for _, a, _ in items]
        typical = statistics.median(amounts)
        if not cadence or max(amounts) > typical * 1.25 or min(amounts) < typical * 0.75:
            continue                                   # irregular timing or amounts: not a subscription
        flags = []
        if amounts[-1] > amounts[0] * 1.02:
            flags.append(f"price up {amounts[0]:.2f}->{amounts[-1]:.2f}")
        current = amounts[-1]                          # latest price is what it costs now
        if current * mult < 15:
            flags.append("small, easy to forget")
        if len({round(a, 2) for a in amounts}) > 1 and "price up" not in " ".join(flags):
            flags.append("amount varies")
        found.append({"merchant": key.title(), "example": items[-1][2], "cadence": cadence, "count": len(items),
                      "amount": round(current, 2), "last": items[-1][0].isoformat(),
                      "monthly": round(current * mult, 2), "annual": round(current * mult * 12, 2),
                      "flags": "; ".join(flags)})
    return sorted(found, key=lambda r: -r["monthly"])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", default=["."])
    ap.add_argument("--out", help="also write the table to this CSV file")
    ap.add_argument("--dayfirst", action="store_true", help="dates are DD/MM/YYYY (UK/EU banks)")
    ap.add_argument("--charges", choices=["positive", "negative"], help="sign of charges in a single Amount column")
    ap.add_argument("--min-count", type=int, default=2, help="minimum charges to count as recurring (default 2)")
    a = ap.parse_args()
    sys.stdout.reconfigure(errors="replace")           # odd characters in merchant names won't crash Windows consoles

    files = []
    for p in map(Path, a.paths):
        files += sorted(p.glob("*.csv")) if p.is_dir() else [p]
    files = [f for f in files if a.out is None or f.resolve() != Path(a.out).resolve()]
    if not files:
        sys.exit("No CSV files found. Export transactions from your bank as CSV and put them here.")
    charges = load(files, DATE_FORMATS_DAYFIRST if a.dayfirst else DATE_FORMATS_US, a.charges)
    if not charges:
        sys.exit("No charges found. Check the file has transactions, or try --charges positive/negative.")
    span = (max(c[0] for c in charges) - min(c[0] for c in charges)).days
    rows = analyse(charges, a.min_count)

    print(f"Read {len(charges)} charges from {len(files)} file(s), covering {span} days.")
    if span < 360:
        print("Note: under a year of data, so annual subscriptions may be missing.")
    print()
    print("| Service | Cadence | Amount | Times seen | Last charged | Per month | Per year | Flags |")
    print("|---|---|---:|---:|---|---:|---:|---|")
    for r in rows:
        print(f"| {r['merchant']} | {r['cadence']} | {r['amount']:.2f} | {r['count']} | {r['last']} | "
              f"{r['monthly']:.2f} | {r['annual']:.2f} | {r['flags']} |")
    print()
    print(f"Total: {sum(r['monthly'] for r in rows):.2f} per month, {sum(r['annual'] for r in rows):.2f} per year "
          f"across {len(rows)} recurring charges.")
    if a.out:
        with open(a.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["merchant"])
            w.writeheader(); w.writerows(rows)
        print(f"Saved {a.out}")


if __name__ == "__main__":
    main()
