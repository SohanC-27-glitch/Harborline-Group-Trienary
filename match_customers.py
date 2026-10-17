#!/usr/bin/env python3
"""Flag candidate duplicate customer pairs; never merges records automatically."""
import csv
import re
import sys
from difflib import SequenceMatcher
from itertools import combinations

CITY_ALIASES = {
    "mangalore": "mangaluru",
    "mangaluru": "mangaluru",
}

def clean(value):
    return (value or "").strip().casefold()

def norm_name(value):
    return " ".join(re.findall(r"[a-z0-9]+", clean(value)))

def norm_phone(value):
    digits = re.sub(r"\D", "", value or "")
    # Treat +91XXXXXXXXXX and XXXXXXXXXX as equivalent for Indian 10-digit phones.
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    return digits

def norm_email(value):
    value = clean(value)
    return value if value else ""

def norm_city(value):
    city = clean(value)
    return CITY_ALIASES.get(city, city)

def similarity(a, b):
    a, b = norm_name(a), norm_name(b)
    return SequenceMatcher(None, a, b).ratio() if a and b else 0.0

def kind(row):
    # Basic guard only. Production data should have an explicit entity-type field.
    name = clean(row.get("Name", ""))
    if any(marker in name for marker in
           (" pvt ltd", " private limited", " limited", " llp", " inc", " corporation")):
        return "organization"
    if name.endswith(" family"):
        return "group"
    return "person"

def compare(a, b):
    # Don't compare different entity kinds as duplicate identities.
    if kind(a) != kind(b):
        return []

    phone_a, phone_b = norm_phone(a.get("Phone")), norm_phone(b.get("Phone"))
    email_a, email_b = norm_email(a.get("Email")), norm_email(b.get("Email"))
    city_a, city_b = norm_city(a.get("City")), norm_city(b.get("City"))
    sim = similarity(a.get("Name"), b.get("Name"))

    same_phone = bool(phone_a) and phone_a == phone_b
    same_email = bool(email_a) and email_a == email_b
    same_city = bool(city_a) and city_a == city_b
    same_name = bool(norm_name(a.get("Name"))) and norm_name(a.get("Name")) == norm_name(b.get("Name"))

    reasons = []
    if same_phone:
        reasons.append("same normalized phone")
    if same_email:
        reasons.append("same normalized email")
    if sim >= 0.85 and same_phone:
        reasons.append("similar name + same phone")
    if sim >= 0.85 and same_city:
        reasons.append("similar name + same city")
    if same_name:
        reasons.append("exact normalized name; contact details may differ")

    # Candidate rules: exact phone/email, exact name (review-only), or
    # similar name plus same canonical city. No automatic merge occurs.
    if same_phone or same_email or same_name or (sim >= 0.85 and same_city):
        return reasons
    return []

def main(input_path, output_path="duplicate_candidates.csv"):
    with open(input_path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    candidates = []
    for i, j in combinations(range(len(rows)), 2):
        a, b = rows[i], rows[j]
        reasons = compare(a, b)
        if not reasons:
            continue
        candidates.append({
            "record_a": i + 1,
            "name_a": a.get("Name", ""),
            "business_a": a.get("Company", ""),
            "record_b": j + 1,
            "name_b": b.get("Name", ""),
            "business_b": b.get("Company", ""),
            "name_similarity": round(similarity(a.get("Name"), b.get("Name")), 3),
            "reasons": "; ".join(reasons),
            "decision": "MANUAL REVIEW",
        })

    fields = ["record_a", "name_a", "business_a", "record_b", "name_b",
              "business_b", "name_similarity", "reasons", "decision"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(candidates)

    print(f"Read {len(rows)} records; flagged {len(candidates)} candidate pairs.")
    print(f"Review {output_path}; this script never merges records.")

if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit("Usage: python match_customers.py input.csv [output.csv]")
    main(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else "duplicate_candidates.csv")
