from app.core.security import create_access_token, decode_token, hash_password, verify_password

# проверяем, что пароль хешируется и не хранится как обычный текст
def test_hash_and_verify_password() -> None:
    password = "password123"

    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)
    assert not verify_password("wrong_password", password_hash)


# проверяем, что jwt создаётся и корректно декодируется
def test_create_and_decode_access_token() -> None:
    token = create_access_token(user_id=1, role="user")

    payload = decode_token(token)

    assert payload["sub"] == "1"
    assert payload["role"] == "user"
    assert "iat" in payload
    assert "exp" in payload
