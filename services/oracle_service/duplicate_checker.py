from dataclasses import dataclass


def _normalize(value) -> str:
    return str(value).strip().lower()


@dataclass(frozen=True)
class DuplicateCheckResult:
    duplicate_indices: list[tuple[int, int]]
    """Pairs of record indices considered duplicates of each other."""

    @property
    def has_duplicates(self) -> bool:
        return bool(self.duplicate_indices)


def find_duplicates(records: list[dict], key_fields: list[str]) -> DuplicateCheckResult:
    """Flags duplicate records by exact match on normalized key fields (e.g. lead
    company name + email), for the Sales & Lead Generation / Research & Competitive
    Intelligence categories per the PRD.

    This is a lightweight, dependency-free stand-in for the pgvector-based embedding
    similarity search the Oracle Verification Service PRD calls for — it catches exact
    and near-exact duplicates (same value, different casing/whitespace) but not
    semantic near-duplicates (e.g. "Acme Inc" vs "Acme Incorporated"). Swap this out for
    an embedding-based implementation once Postgres + pgvector is provisioned; the
    interface (a list of duplicate index pairs) is designed to stay the same when that
    happens, so callers don't need to change."""
    seen: dict[tuple, int] = {}
    duplicates: list[tuple[int, int]] = []
    for i, record in enumerate(records):
        key = tuple(_normalize(record.get(f, "")) for f in key_fields)
        if key in seen:
            duplicates.append((seen[key], i))
        else:
            seen[key] = i
    return DuplicateCheckResult(duplicate_indices=duplicates)
