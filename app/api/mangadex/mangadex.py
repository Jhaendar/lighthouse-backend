from typing import Any
import requests

from app.config import MangadexConfig
import app.api.mangadex.auth as auth
import time

JSON = Any


def get_default_params() -> dict[str, JSON]:
    return {"translatedLanguage[]": ["en"]}


def request_get_manga_status() -> requests.Response:
    url = MangadexConfig.URLS["manga_status"].format(BaseURL=MangadexConfig.BaseURL)
    method = "GET"

    headers = {
        "Authorization": auth.get_bearer_token(),
    }

    response = requests.request(method=method, url=url, headers=headers)

    print(f"[{method}] {url} | {response.status_code}")
    return response


def get_all_manga_reading_status() -> dict[str, list[str]]:
    response = request_get_manga_status()

    # retry if access token is invalid
    if response.status_code == 401:
        print("Access token is invalid, refreshing...")
        auth.refresh_access_token()
        response = request_get_manga_status()

    if response.status_code != 200:
        raise Exception("Failed to get manga reading status")

    data = response.json()
    if data["result"] == "error":
        raise Exception("Error in manga reading status request")

    # group into values
    statuses: dict[str, list[str]] = dict()
    for id, status in data["statuses"].items():
        if status not in statuses:
            statuses[status] = list()

        statuses[status].append(id)

    return statuses


def request_get_manga_by_ids(
    ids: list[str], limit: int = 10, offset: int = 0
) -> requests.Response:
    if len(ids) > 100:
        raise Exception("Maximum of 100 ids per request")

    url = MangadexConfig.URLS["manga"].format(BaseURL=MangadexConfig.BaseURL)
    method = "GET"

    params = {
        "limit": limit,
        "offset": offset,
        "ids[]": ids,
        "availableTranslatedLanguage[]": ["en"],
        "includes[]": ["cover_art"],
    }

    response = requests.request(method=method, url=url, params=params)

    print(f"[{method}] {url} | {response.status_code}")
    return response


def get_manga_by_ids(ids: list[str]) -> JSON:
    # batch ids into groups of 100
    manga_data: list[JSON] = list()

    for batch_ids in [ids[i : i + 100] for i in range(0, len(ids), 100)]:
        time.sleep(1)
        response = request_get_manga_by_ids(batch_ids, 100, 0)

        if response.status_code == 200:
            data = response.json()

            if data["result"] != "ok":
                raise Exception("Failed to get manga by ids")

            manga_data.extend(data["data"])
        else:
            raise Exception("Failed to get manga by ids")

    return manga_data


def request_get_manga_feed(
    id: str, limit: int = 100, offset: int = 0
) -> requests.Response:
    url = MangadexConfig.URLS["manga_feed"].format(
        BaseURL=MangadexConfig.BaseURL, id=id
    )

    method = "GET"

    # default params
    params = get_default_params()
    params.update(
        {
            "limit": limit,
            "offset": offset,
            "order[createdAt]": "desc",
            "order[updatedAt]": "desc",
            "order[publishAt]": "desc",
            "order[readableAt]": "desc",
            "order[volume]": "desc",
            "order[chapter]": "desc",
        }
    )

    response = requests.request(method=method, url=url, params=params)

    print(f"[{method}] {url} | {response.status_code}")
    return response


def get_manga_feed(id: str) -> list[JSON]:
    chapters: list[JSON] = list()

    limit = 100
    offset = 0
    total = float("inf")
    while True:
        if offset >= total:
            break
        response = request_get_manga_feed(id, limit=limit, offset=offset)

        if response.status_code != 200:
            raise Exception("Failed to get manga feed")

        data = response.json()
        if data["result"] == "error":
            raise Exception("Failed to get parse manga feed")

        chapters.extend(data["data"])

        total = data["total"]
        offset += limit
        print(f"Got ({offset}/{total})")

        time.sleep(1)

    return chapters


def request_get_manga_aggregate(id: str) -> requests.Response:
    url = MangadexConfig.URLS["manga_aggregate"].format(
        BaseURL=MangadexConfig.BaseURL, id=id
    )
    method = "GET"

    params = get_default_params()

    response = requests.request(method=method, url=url, params=params)

    print(f"[{method}] {url} | {response.status_code}")
    return response


def get_manga_aggregate(id: str) -> JSON:
    response = request_get_manga_aggregate(id)

    if response.status_code == 200:
        data = response.json()
        return data

    raise Exception("Failed to get manga aggregate")


def request_get_manga_read_markers_batch(ids: list[str]) -> requests.Response:
    url = MangadexConfig.URLS["manga_read_marker_batch"].format(
        BaseURL=MangadexConfig.BaseURL
    )
    method = "GET"

    headers = {
        "Authorization": auth.get_bearer_token(),
    }
    params = {
        "ids[]": ids,
        "grouped": "true",
    }

    response = requests.request(method=method, url=url, params=params, headers=headers)
    print(f"[{method}] {url} | {response.status_code}")
    return response


def get_manga_read_markers_batch(ids: list[str]) -> JSON:
    limit = 100
    offset = 0
    total = len(ids)

    read_markers: dict[str, list[str]] = dict()

    while offset < total:
        response = request_get_manga_read_markers_batch(ids[offset : offset + limit])

        if response.status_code != 200:
            raise Exception("Failed to get manga read markers batch")

        data = response.json()
        if data["result"] == "error":
            raise Exception("Failed to parse manga read markers batch")

        read_markers.update(data["data"])
        offset += limit
        print("Processed", offset, "of", total)

        time.sleep(1)

    return read_markers


def get_manga_cards(ids: list[str], limit: int = 10, offset: int = 0) -> JSON:
    """
    Get Manga Card page by page
    """
    # initial data
    data = {
        "total": len(ids),
        "offset": offset,
        "limit": limit,
        "data": list(),
    }

    # current ids
    ids = ids[offset : offset + limit]

    # get manga by ids
    data["data"] = get_manga_by_ids(ids)
    read_markers = get_manga_read_markers_batch(ids)

    for manga in data["data"]:
        id = manga["id"]
        aggregate = get_manga_aggregate(id)
        chapter_read_marker = read_markers.get(id, list())

        read = 0
        total = 0
        for v in aggregate["volumes"].values():
            total += len(v["chapters"])
            for chapter in v["chapters"].values():
                for id in [chapter["id"]] + chapter["others"]:
                    if id in chapter_read_marker:
                        read += 1
                        break

        manga["read"] = read
        manga["total"] = total

    return data
