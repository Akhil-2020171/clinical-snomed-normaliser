from app.linker.snomed_loader import SnomedLoader
from app.linker.snomed_linker import SnomedLinker


# --------------------------------------------------
# Load SNOMED data
# --------------------------------------------------

print("Loading SNOMED CT...")

snomed_loader = SnomedLoader()
snomed_data = snomed_loader.load()

snomed_linker = SnomedLinker(
    snomed_data
)

print("SNOMED loaded.\n")


# --------------------------------------------------
# Test exact candidate generation
# --------------------------------------------------

terms = [
    "coronary disease",
    "coronary artery disease",
    "coronary heart disease",
    "ischemic heart disease",
    "disease"
]

print("=" * 70)
print("EXACT / NORMALIZED CANDIDATE TEST")
print("=" * 70)

for term in terms:

    candidates = snomed_linker.find_candidates(
        term
    )

    print(f"\nTERM: {term}")
    print(f"Candidates: {len(candidates)}")

    for candidate in candidates:
        print(candidate)


# --------------------------------------------------
# Test contained-term fallback
# --------------------------------------------------

print("\n")
print("=" * 70)
print("CONTAINED TERM TEST")
print("=" * 70)

mention = "coronary disease"

contained_terms = (
    snomed_linker.find_contained_terms(
        mention
    )
)

print(f"\nMENTION: {mention}")
print(f"Contained matches: {len(contained_terms)}")

for candidate in contained_terms:
    print(candidate)