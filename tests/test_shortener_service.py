from app.services.shortener import (
    generate_short_code,
    create_short_url,
    get_url_by_code,
    increment_click,
    CODE_LENGTH,
)


def test_generate_short_code_default_length():
    code = generate_short_code()
    assert len(code) == CODE_LENGTH


def test_generate_short_code_custom_length():
    code = generate_short_code(length=10)
    assert len(code) == 10


def test_generate_short_code_is_alphanumeric():
    code = generate_short_code()
    assert code.isalnum()


def test_generate_short_code_is_random():
    codes = {generate_short_code() for _ in range(100)}
    assert len(codes) > 90


def test_create_short_url_persists_to_db(db):
    url_entry = create_short_url(db, "https://example.com")
    assert url_entry.id is not None
    assert url_entry.original_url == "https://example.com"
    assert len(url_entry.short_code) == CODE_LENGTH
    assert url_entry.click_count == 0


def test_get_url_by_code_returns_entry(db):
    created = create_short_url(db, "https://example.com")
    fetched = get_url_by_code(db, created.short_code)
    assert fetched is not None
    assert fetched.id == created.id


def test_get_url_by_code_returns_none_for_missing(db):
    result = get_url_by_code(db, "zzzzzz")
    assert result is None


def test_increment_click_increases_count(db):
    url_entry = create_short_url(db, "https://example.com")
    assert url_entry.click_count == 0
    updated = increment_click(db, url_entry)
    assert updated.click_count == 1
    updated = increment_click(db, url_entry)
    assert updated.click_count == 2


def test_soft_delete_marks_url_as_deleted(db):
    from app.services.shortener import soft_delete
    url_entry = create_short_url(db, "https://example.com")
    soft_delete(db, url_entry)
    assert url_entry.is_deleted is True


def test_get_url_by_code_ignores_deleted(db):
    from app.services.shortener import soft_delete
    url_entry = create_short_url(db, "https://example.com")
    code = url_entry.short_code
    soft_delete(db, url_entry)
    result = get_url_by_code(db, code)
    assert result is None


def test_url_has_updated_at(db):
    url_entry = create_short_url(db, "https://example.com")
    assert url_entry.updated_at is not None


def test_create_short_url_handles_collision(db):
    """Force a collision by pre-inserting a code and verify retry succeeds."""
    from unittest.mock import patch
    existing = create_short_url(db, "https://existing.com")
    codes = [existing.short_code, "newcode"]
    with patch("app.services.shortener.generate_short_code", side_effect=codes):
        result = create_short_url(db, "https://new.com")
    assert result.short_code == "newcode"