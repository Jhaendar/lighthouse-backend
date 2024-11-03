class EnvironmentConfig:
    ENVIRONMENT_PATH = ".env"


class MangadexConfig:
    BaseURL = "https://api.mangadex.org"
    MangadexAuthURL = (
        "https://auth.mangadex.org/realms/mangadex/protocol/openid-connect/token"
    )
    URLS = {
        "manga_status": "{BaseURL}/manga/status",
        "manga": "{BaseURL}/manga",
        "manga_feed": "{BaseURL}/manga/{id}/feed",
        "manga_aggregate": "{BaseURL}/manga/{id}/aggregate",
        "manga_read_marker_batch": "{BaseURL}/manga/read",
    }
