#!/usr/bin/env python3

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pdfplumber


MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


HEADER_SKIP_PREFIXES = (
    "Date",
    "Description",
    "Cheques&Debits($)",
    "Deposits&Credits($)",
    "Balance($)",
    "AccountActivityDetails",
    "AccountActivityDetails-continued",
    "Business Account Statement",
)

FOOTER_SKIP_PREFIXES = (
    "Closingbalance",
    "AccountFees:",
    "DepositInterestEarned:",
    "1of",
    "2of",
)


@dataclass
class StatementPeriod:
    start: date
    end: date


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract transaction candidates from RBC account statements.")
    parser.add_argument("pdfs", nargs="+", help="PDF statements to parse")
    parser.add_argument("--output", required=True, help="Output JSON path")
    return parser.parse_args()


def clean_amount(text: str) -> float | None:
    stripped = text.replace("$", "").replace(",", "").strip()
    if not stripped:
        return None
    try:
        return float(stripped)
    except ValueError:
        return None


def compress_repeats(text: str) -> str:
    if not text:
        return text
    out = [text[0]]
    for ch in text[1:]:
        if ch != out[-1]:
            out.append(ch)
    return "".join(out)


def normalize_date_token(token: str) -> str | None:
    compact = re.sub(r"[^A-Za-z0-9]", "", token)
    if not compact:
        return None
    direct = re.fullmatch(r"(\d{1,2})([A-Za-z]{3})", compact)
    if direct:
        return f"{int(direct.group(1)):02d}{direct.group(2).title()}"

    digits = "".join(ch for ch in compact if ch.isdigit())
    letters = "".join(ch for ch in compact if ch.isalpha()).lower()
    letters = compress_repeats(letters)

    month_key = None
    for key in MONTHS:
        if key in letters:
            month_key = key
            break
    if not month_key or not digits:
        return None

    if len(digits) == 4 and digits[:2] == digits[2:]:
        digits = digits[:2]
    elif len(digits) > 2:
        digits = digits[:2]

    if not digits.isdigit():
        return None
    return f"{int(digits):02d}{month_key.title()}"


def parse_period(text: str) -> StatementPeriod | None:
    match = re.search(
        r"([A-Za-z]+)(\d{1,2}),(\d{4})to([A-Za-z]+)(\d{1,2}),(\d{4})",
        text.replace(" ", ""),
    )
    if not match:
        return None

    start_month = MONTHS[match.group(1)[:3].lower()]
    start_day = int(match.group(2))
    start_year = int(match.group(3))
    end_month = MONTHS[match.group(4)[:3].lower()]
    end_day = int(match.group(5))
    end_year = int(match.group(6))
    return StatementPeriod(
        start=date(start_year, start_month, start_day),
        end=date(end_year, end_month, end_day),
    )


def infer_full_date(token: str, period: StatementPeriod) -> str | None:
    normalized = normalize_date_token(token)
    if not normalized:
        return None
    day = int(normalized[:2])
    month = MONTHS[normalized[2:].lower()]

    candidate_years = [period.start.year, period.end.year]
    for year in candidate_years:
        try:
            candidate = date(year, month, day)
        except ValueError:
            continue
        if period.start <= candidate <= period.end:
            return candidate.isoformat()

    # Fall back to statement end year for same-year periods.
    try:
        return date(period.end.year, month, day).isoformat()
    except ValueError:
        return None


def find_table_header(page: pdfplumber.page.Page) -> dict[str, float] | None:
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    header_words = {}
    for word in words:
        text = word["text"].strip()
        if text in {"Date", "Description", "Cheques&Debits($)", "Deposits&Credits($)", "Balance($)"}:
            header_words[text] = word
    required = {"Date", "Description", "Cheques&Debits($)", "Deposits&Credits($)", "Balance($)"}
    if set(header_words) != required:
        return None
    return {
        "top": float(header_words["Date"]["top"]),
        "date_x": float(header_words["Date"]["x0"]),
        "desc_x": float(header_words["Description"]["x0"]),
        "debit_x": float(header_words["Cheques&Debits($)"]["x0"]),
        "credit_x": float(header_words["Deposits&Credits($)"]["x0"]),
        "balance_x": float(header_words["Balance($)"]["x0"]),
    }


def group_rows(page: pdfplumber.page.Page) -> list[dict[str, Any]]:
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    header = find_table_header(page)
    if not header:
        return []

    buckets: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for word in words:
        top = float(word["top"])
        if top <= header["top"] + 8:
            continue
        if top >= page.height - 70:
            continue
        top_key = int(round(float(word["top"]) / 2.0) * 2)
        buckets[top_key].append(word)

    rows = []
    for top_key in sorted(buckets):
        words_in_row = sorted(buckets[top_key], key=lambda item: float(item["x0"]))
        row = {"raw_words": words_in_row, "date": [], "description": [], "debit": [], "credit": [], "balance": []}
        for word in words_in_row:
            x0 = float(word["x0"])
            text = word["text"].strip()
            if x0 < header["desc_x"] - 6:
                row["date"].append(text)
            elif x0 < header["debit_x"] - 6:
                row["description"].append(text)
            elif x0 < header["credit_x"] - 6:
                row["debit"].append(text)
            elif x0 < header["balance_x"] - 6:
                row["credit"].append(text)
            else:
                row["balance"].append(text)
        rows.append(row)
    return rows


def joined(values: list[str]) -> str:
    return " ".join(item for item in values if item).strip()


def looks_like_new_transaction(row: dict[str, Any]) -> bool:
    date_text = joined(row["date"])
    return normalize_date_token(date_text) is not None


def parse_statement(pdf_path: Path) -> dict[str, Any]:
    with pdfplumber.open(pdf_path) as pdf:
        first_page_text = (pdf.pages[0].extract_text() or "").replace("\n", " ")
        period = parse_period(first_page_text)
        account_match = re.search(r"Accountnumber:\s*([0-9 -]+)", first_page_text)
        account_number = account_match.group(1).strip() if account_match else ""
        account_type = "savings" if "SavingsAccount" in first_page_text else "chequing"

        statement: dict[str, Any] = {
            "file_name": pdf_path.name,
            "file_path": str(pdf_path),
            "page_count": len(pdf.pages),
            "account_number": account_number,
            "account_type": account_type,
            "statement_period": {
                "start": period.start.isoformat() if period else None,
                "end": period.end.isoformat() if period else None,
            },
            "transactions": [],
            "extraction_notes": [],
        }

        current: dict[str, Any] | None = None
        txn_index = 0

        for page_number, page in enumerate(pdf.pages, start=1):
            for row in group_rows(page):
                date_text = joined(row["date"])
                desc_text = joined(row["description"])
                debit_text = joined(row["debit"])
                credit_text = joined(row["credit"])
                balance_text = joined(row["balance"])

                if any(date_text.startswith(prefix) for prefix in HEADER_SKIP_PREFIXES):
                    continue
                if any(desc_text.startswith(prefix) for prefix in HEADER_SKIP_PREFIXES):
                    continue
                if any(desc_text.startswith(prefix) for prefix in FOOTER_SKIP_PREFIXES):
                    if current:
                        statement["transactions"].append(current)
                    current = None
                    continue
                if date_text.startswith("Openingbalance") or desc_text.startswith("Openingbalance"):
                    current = None
                    continue

                if looks_like_new_transaction(row):
                    if current:
                        statement["transactions"].append(current)
                    txn_index += 1
                    normalized_token = normalize_date_token(date_text) or date_text
                    current = {
                        "source_page": page_number,
                        "source_date_token": date_text,
                        "date": infer_full_date(date_text, period) if period else None,
                        "date_parse_note": None,
                        "description_parts": [desc_text] if desc_text else [],
                        "debit_amount": clean_amount(debit_text),
                        "credit_amount": clean_amount(credit_text),
                        "balance": clean_amount(balance_text),
                        "sequence_in_statement": txn_index,
                        "normalized_date_token": normalized_token,
                    }
                    if normalized_token != date_text:
                        current["date_parse_note"] = f"normalized date token from '{date_text}' to '{normalized_token}'"
                    continue

                if current is None:
                    continue

                if date_text and not desc_text and not debit_text and not credit_text and not balance_text:
                    # Ignore stray date-only noise rows.
                    continue

                if date_text and normalize_date_token(date_text) is None:
                    current.setdefault("continuation_noise", []).append(date_text)
                if desc_text:
                    current["description_parts"].append(desc_text)
                if debit_text and current.get("debit_amount") is None:
                    current["debit_amount"] = clean_amount(debit_text)
                if credit_text and current.get("credit_amount") is None:
                    current["credit_amount"] = clean_amount(credit_text)
                if balance_text:
                    current["balance"] = clean_amount(balance_text)

        if current:
            statement["transactions"].append(current)

    normalized_transactions = []
    for txn in statement["transactions"]:
        description = " ".join(part for part in txn.pop("description_parts", []) if part).strip()
        debit_amount = txn.get("debit_amount")
        credit_amount = txn.get("credit_amount")
        if debit_amount is not None and credit_amount is not None:
            direction = "ambiguous"
            amount = debit_amount
            statement["extraction_notes"].append(
                f"{pdf_path.name}: transaction {txn['sequence_in_statement']} had both debit and credit columns populated"
            )
        elif debit_amount is not None:
            direction = "debit"
            amount = debit_amount
        elif credit_amount is not None:
            direction = "credit"
            amount = credit_amount
        else:
            direction = "unknown"
            amount = None
            statement["extraction_notes"].append(
                f"{pdf_path.name}: transaction {txn['sequence_in_statement']} missing both debit and credit amount"
            )

        normalized_transactions.append(
            {
                "transaction_id": f"cand_{statement['account_number'].replace(' ', '')}_{txn['sequence_in_statement']:03d}",
                "date": txn["date"],
                "description": description,
                "raw_description": description,
                "amount": amount,
                "direction": direction,
                "balance": txn.get("balance"),
                "account": statement["account_number"],
                "currency": "CAD",
                "receipt": None,
                "cheque_info": None,
                "supplementary_context": None,
                "bs_source": pdf_path.name,
                "source_page": txn["source_page"],
                "source_date_token": txn["source_date_token"],
                "normalized_date_token": txn["normalized_date_token"],
                "date_parse_note": txn.get("date_parse_note"),
                "continuation_noise": txn.get("continuation_noise", []),
            }
        )

    statement["transactions"] = normalized_transactions
    return statement


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    statements = [parse_statement(Path(pdf)) for pdf in args.pdfs]
    structured_candidates = [txn for statement in statements for txn in statement["transactions"]]

    source_bundle = {
        "files": [
            {
                "path": statement["file_path"],
                "file_type": "pdf",
                "account_number": statement["account_number"],
                "account_type": statement["account_type"],
                "statement_period": statement["statement_period"],
                "page_count": statement["page_count"],
            }
            for statement in statements
        ],
        "structured_candidates": structured_candidates,
        "source_notes": [note for statement in statements for note in statement["extraction_notes"]],
        "explicit_unknowns": [],
        "statement_summaries": statements,
    }

    output_path.write_text(json.dumps(source_bundle, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
