from backend.core.security import names_match, verify_password, hash_password

def test_names_match_ignores_spaces():
    assert names_match("  Ahmed   Mohamed ", "ahmed mohamed")
    assert not names_match("Ahmed", "Ali")

def test_password_hash():
    h = hash_password("secret123")
    assert verify_password("secret123", h)
    assert not verify_password("wrong", h)