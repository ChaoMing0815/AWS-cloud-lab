import hashlib


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
