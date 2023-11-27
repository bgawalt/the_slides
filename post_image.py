"""Posts an image to BlueSky.

Usage:

  $ python post_image.py credfile.secret path/to/image.jpeg

TODO: Make this pick a random slide instead of the given user image.
"""

import base64
import dataclasses
import pathlib
import requests
import sys

from datetime import datetime, timezone
from typing import Tuple


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


def post_image(text_content: str, img: pathlib.Path, login: BSkyLogin):
    auth, did = login.get_auth_and_did()
    # Upload the image as a blob:
    blob_hdrs = {
        "Authorization": "Bearer " + auth,
        "Content-Type": "image/jpeg"
    }
    img_bytes = img.read_bytes()

    img_encode = base64.b64encode(img_bytes)
    img_decode = base64.b64decode(img_encode)

    blob_resp = requests.post(
        f"{login.host}/xrpc/com.atproto.repo.uploadBlob",
        data=img_bytes,
        headers=blob_hdrs
    )
    print("Blob upload response status code:", blob_resp.status_code)
    # Post the message:
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

    imgfile = pathlib.Path(sys.argv[2])
    what_to_post = input("Enter message: ")
    post_image(what_to_post, imgfile, login)


if __name__ == "__main__":
    main()
