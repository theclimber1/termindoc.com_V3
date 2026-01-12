from dashboard import normalize_single_speciality

test_cases = [
    "Kieferorthopädie",
    "Zahnarzt",
    "Orthopädie",
    "Unfallchirurgie und Orthopädie"
]

for t in test_cases:
    print(f"'{t}' -> '{normalize_single_speciality(t)}'")
