def normalize_single_speciality(raw):
    if not isinstance(raw, str): return str(raw)
    s = raw.lower()
    if "allgemeinmedizin" in s: return "Allgemeinmedizin"
    if "kinder" in s and "jugend" in s: return "Kinderheilkunde"
    if "frauenheilkunde" in s or "gynäkologie" in s: return "Gynäkologie & Geburtshilfe"
    if "innere medizin" in s: return "Innere Medizin"
    # Moved up
    if "zahn" in s or "kiefer" in s: return "Zahnmedizin / Kieferorthopädie"
    if "orthopädie" in s: return "Orthopädie"
    if "hno" in s or "hals" in s: return "HNO"
    if "kardiologie" in s: return "Innere Medizin (Kardiologie)"
    return raw

test_cases = [
    "Kieferorthopädie",
    "Zahnarzt",
    "Orthopädie",
    "Unfallchirurgie und Orthopädie"
]

for t in test_cases:
    print(f"'{t}' -> '{normalize_single_speciality(t)}'")
