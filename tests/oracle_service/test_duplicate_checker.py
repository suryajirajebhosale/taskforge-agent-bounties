from services.oracle_service.duplicate_checker import find_duplicates


def test_no_duplicates():
    records = [{"email": "a@x.com"}, {"email": "b@x.com"}]
    result = find_duplicates(records, key_fields=["email"])
    assert not result.has_duplicates


def test_exact_duplicate_detected():
    records = [{"email": "a@x.com"}, {"email": "a@x.com"}]
    result = find_duplicates(records, key_fields=["email"])
    assert result.has_duplicates
    assert result.duplicate_indices == [(0, 1)]


def test_case_and_whitespace_insensitive():
    records = [{"email": "A@X.com"}, {"email": " a@x.com "}]
    result = find_duplicates(records, key_fields=["email"])
    assert result.has_duplicates


def test_multi_field_key_requires_all_fields_to_match():
    records = [{"company": "Acme", "email": "a@x.com"}, {"company": "Acme", "email": "b@x.com"}]
    result = find_duplicates(records, key_fields=["company", "email"])
    assert not result.has_duplicates


def test_multiple_duplicates_chain_off_the_first_occurrence():
    records = [{"email": "a@x.com"}, {"email": "a@x.com"}, {"email": "a@x.com"}]
    result = find_duplicates(records, key_fields=["email"])
    assert result.duplicate_indices == [(0, 1), (0, 2)]


def test_missing_key_field_treated_as_empty_string():
    records = [{"email": "a@x.com"}, {}]
    result = find_duplicates(records, key_fields=["email"])
    assert not result.has_duplicates
