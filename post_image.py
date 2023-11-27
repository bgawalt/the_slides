"""Posts an image to BlueSky.

Usage:

  $ python post_image.py credfile.secret slides_input.db3

TODO: Make this pick a random slide instead of the given user image.
"""

import base64
import dataclasses
import pathlib
import requests
import sys
import sqlite3

from datetime import datetime, timezone
from typing import Tuple


_SELECT_SLIDE_QUERY = """
    WITH collection_counts AS (
        SELECT collection, COUNT(*) as num_img
        FROM slides
        GROUP BY collection
    ),
    img_ranks AS (
        SELECT
            collection,
            filename,
            jpeg_base64,
            RANK() OVER (
                PARTITION BY collection
                ORDER BY filename
            ) AS filename_rank
        FROM slides
    )
    SELECT
        ir.collection,
        ir.filename,
        ir.filename_rank,
        cc.num_img,
        ir.jpeg_base64
    FROM
        img_ranks AS ir
        LEFT JOIN collection_counts AS cc
        ON ir.collection = cc.collection
    ORDER BY RANDOM()
    LIMIT 1
"""


@dataclasses.dataclass(frozen=True)
class BSkyLogin:
    host: str
    username: str
    password: str

    def get_auth_and_did(self) -> Tuple[str, str]:
        """Fetch your (auth token, dist user id) pair."""
        token_request_params = {
            "identifier": self.username,
            "password": self.password
        }
        resp = requests.post(
            f"{self.host}/xrpc/com.atproto.server.createSession",
            json=token_request_params
        )
        auth_token = resp.json().get("accessJwt")
        if auth_token is None:
            raise ValueError("Whoopsie doodle, bad response:" +
                str(resp.json()))
        did = resp.json().get("did")
        return (auth_token, did)


    @staticmethod
    def from_file(path: pathlib.Path):
        """Load a login from a custom-format credfile; see README."""
        lines = path.read_text().split("\n")
        splines = (line.split(" = ") for line in lines if line)
        kv = {spline[0]: spline[1] for spline in splines}
        return BSkyLogin(
            host=kv["ATP_HOST"],
            username=kv["ATP_USERNAME"],
            password=kv["ATP_PASSWORD"],
        )


def post_image(
    collection: str, file_rank: int, collection_size: int, jpeg_b64: str,
    login: BSkyLogin
):
    auth, did = login.get_auth_and_did()
    # Upload the image as a blob:
    blob_hdrs = {
        "Authorization": "Bearer " + auth,
        "Content-Type": "image/jpeg"
    }
    img_bytes = base64.b64decode(jpeg_b64)
    blob_resp = requests.post(
        f"{login.host}/xrpc/com.atproto.repo.uploadBlob",
        data=img_bytes,
        headers=blob_hdrs
    )
    print("Blob upload response status code:", blob_resp.status_code)
    # Post the message:
    text_content = f'"{collection}," slide {file_rank} of {collection_size}'
    dtime_now = datetime.now(timezone.utc)
    timestamp_iso = dtime_now.isoformat().replace("+00:00", "Z")
    msg_hdrs = {"Authorization": "Bearer " + auth}
    msg_data = {
        "collection": "app.bsky.feed.post",
        "$type": "app.bsky.feed.post",
        "repo": "{}".format(did),
        "record": {
            "$type": "app.bsky.feed.post",
            "createdAt": timestamp_iso,
            "text": text_content,
            "embed": {
                "$type": "app.bsky.embed.images",
                "images": [{
                    "alt": "",
                    "image": blob_resp.json().get("blob")
                }]
            }
        }
    }
    msg_resp = requests.post(
        f"{login.host}/xrpc/com.atproto.repo.createRecord",
        json=msg_data,
        headers=msg_hdrs
    )
    print("Message response status code:", msg_resp.status_code)


def main():
    credfile = pathlib.Path(sys.argv[1])
    login = BSkyLogin.from_file(credfile)

    db_filename = sys.argv[2]
    conn = sqlite3.connect(db_filename)
    cur = conn.cursor()
    cur.execute(_SELECT_SLIDE_QUERY)
    collection, _, rank, col_size, jpeg_b64 = cur.fetchone()
    print(collection, rank, col_size)
    post_image(
        collection=collection,
        file_rank=rank,
        collection_size=col_size,
        jpeg_b64=jpeg_b64,
        login=login
    )
    conn.close()


if __name__ == "__main__":
    main()
