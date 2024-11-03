import requests
from app.api.utils.env import get_env, set_env
from app.config import MangadexConfig


# get refresh token
def request_refresh_token() -> requests.Response:
    url = MangadexConfig.MangadexAuthURL
    method = "POST"
    payload = {
        "grant_type": "password",
        "username": get_env("MANGADEX_USERNAME"),
        "password": get_env("MANGADEX_PASSWORD"),
        "client_id": get_env("MANGADEX_CLIENT_ID"),
        "client_secret": get_env("MANGADEX_CLIENT_SECRET"),
    }

    # Validate the payload
    for key, value in payload.items():
        if value is None:
            raise ValueError(f"Missing payload key: {key}")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.request(method=method, url=url, data=payload, headers=headers)

    print(f"[{method}] {url} | {response.status_code}")
    return response


def request_access_token() -> requests.Response:
    url = MangadexConfig.MangadexAuthURL
    method = "POST"

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": get_env("MANGADEX_REFRESH_TOKEN"),
        "client_id": get_env("MANGADEX_CLIENT_ID"),
        "client_secret": get_env("MANGADEX_CLIENT_SECRET"),
    }

    # Validate the payload
    for key, value in payload.items():
        if value is None:
            raise ValueError(f"Missing payload key: {key}")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.request(method=method, url=url, data=payload, headers=headers)

    print(f"[{method}] {url} | {response.status_code}")
    return response


def refresh_refresh_token() -> None:
    response = request_refresh_token()

    if response.status_code == 200:
        data = response.json()
        set_env("MANGADEX_REFRESH_TOKEN", data["refresh_token"])
        set_env("MANGADEX_ACCESS_TOKEN", data["access_token"])
    else:
        raise Exception("Failed to get refresh token")


def refresh_access_token() -> None:
    if get_env("MANGADEX_REFRESH_TOKEN") is None:
        raise Exception("No refresh token found")

    response = request_access_token()
    if response.status_code == 200:
        data = response.json()
        set_env("MANGADEX_ACCESS_TOKEN", data["access_token"])
    else:
        raise Exception("Failed to get access token")


def get_bearer_token() -> str:
    access_token = get_env("MANGADEX_ACCESS_TOKEN")

    if access_token is None:
        raise Exception("No access token found")

    return f"Bearer {access_token}"
