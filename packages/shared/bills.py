import re


BILL_TYPE_LABELS = {
    "hr": "H.R.",
    "hres": "H.Res.",
    "hjres": "H.J.Res.",
    "hconres": "H.Con.Res.",
    "s": "S.",
    "sres": "S.Res.",
    "sjres": "S.J.Res.",
    "sconres": "S.Con.Res.",
}


def display_bill_id(bill_id: str) -> str:
    match = re.fullmatch(r"([a-z]+)-(\d+)-(\d+)", bill_id.strip().lower())
    if not match:
        return bill_id

    bill_type, number, congress = match.groups()
    label = BILL_TYPE_LABELS.get(bill_type, bill_type.upper())
    return f"{label} {int(number)} ({ordinal(int(congress))} Congress)"


def ordinal(value: int) -> str:
    if 10 <= value % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"
