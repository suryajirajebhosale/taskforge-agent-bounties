import hashlib
import secrets


def generate_api_key() -> str:
    return f"agt_{secrets.token_urlsafe(32)}"


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def key_prefix(raw_key: str) -> str:
    """Short, non-secret slice kept for display purposes (e.g. in a dashboard listing
    an agent's keys) so a developer can recognize a key without ever seeing it again."""
    return raw_key[:12]
