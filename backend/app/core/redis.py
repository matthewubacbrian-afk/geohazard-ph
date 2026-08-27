from app.config import get_settings


def get_redis_url() -> str:
    return get_settings().redis_url
