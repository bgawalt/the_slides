import dataclasses
import pathlib
import sys

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import requests


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


class BSkyMessageSegment:
    
    def __init__(self, text: str):
        self._text = text
    
    def text(self) -> str:
        return self._text
    
    def byte_len(self) -> int:
        return len(self.text().encode("UTF-8"))
    
    def get_facet(self, byte_start: int) -> Optional[Dict]:
        return None


class PlainTextSegment(BSkyMessageSegment):

    def __init__(self, text: str):
        super().__init__(text)


class HyperlinkSegment(BSkyMessageSegment):

    def __init__(self, text: str, url: str):
        super().__init__(text)
        self._url = url
    
    def get_facet(self, byte_start: int) -> Optional[Dict]:
        return {
            "index": {
                "byteStart": byte_start,
                "byteEnd": byte_start + self.byte_len()
            },
            "features": [
                {            
                    "$type": "app.bsky.richtext.facet#link",
                    "uri": self._url
                }
            ]
        }


class BSkyMessageBuilder:

    def __init__(self):
        self._segments = []
        self._facets = []
        self._total_byte_len = 0
        self._img_bytes = []
        self._img_alts = []
    
    def add_segment(self, segment: BSkyMessageSegment) -> None:
        self._segments.append(segment)
        facet = segment.get_facet(self._total_byte_len)
        if facet is not None:
            self._facets.append(facet)
        self._total_byte_len += segment.byte_len()
    
    def add_jpeg(self, img_bytes: bytes, alt_text: str = "") -> None:
        if len(self._img_bytes) == 4:
            raise RuntimeError("That's too many jpegs!!")
        self._img_bytes.append(img_bytes)
        self._img_alts.append(alt_text)
    
    def post(self,
             login: BSkyLogin,
             timestamp_iso: Optional[str] = None) -> None:
        auth, did = login.get_auth_and_did()
        if timestamp_iso is None:
            dtime_now = datetime.now(timezone.utc)
            timestamp_iso = dtime_now.isoformat().replace("+00:00", "Z")
        text_content = "".join(seg.text() for seg in self._segments)
        record = {
            "$type": "app.bsky.feed.post",
            "createdAt": timestamp_iso,
            "text": text_content,
        }
        if self._facets:
            record["facets"] = list(self._facets)
        if self._img_bytes:
            blobs = self._get_jpeg_blobs(host=login.host, auth=auth)
            images = [{"alt": alt, "image": blob}
                      for alt, blob in zip(self._img_alts, blobs)]
            record["embed"] = {
                "$type": "app.bsky.embed.images",
                "images": images
            }
        msg_hdrs = {"Authorization": "Bearer " + auth}
        msg_data = {
            "collection": "app.bsky.feed.post",
            "$type": "app.bsky.feed.post",
            "repo": did,
            "record": record
        }
        msg_resp = requests.post(
            f"{login.host}/xrpc/com.atproto.repo.createRecord",
            json=msg_data,
            headers=msg_hdrs
        )
        msg_resp.raise_for_status()
        return
    
    def _get_jpeg_blobs(self, host: str, auth: str) -> List[Dict]:
        blob_hdrs = {
            "Authorization": "Bearer " + auth,
            "Content-Type": "image/jpeg"
        }
        blobs = []
        for img in self._img_bytes:
            blob_resp = requests.post(
                f"{host}/xrpc/com.atproto.repo.uploadBlob",
                data=img,
                headers=blob_hdrs
            )
            blob_resp.raise_for_status()
            blobs.append(blob_resp.json()["blob"])
        return blobs

            
def main():
    credfile = pathlib.Path(sys.argv[1])
    login = BSkyLogin.from_file(credfile)
    builder = BSkyMessageBuilder()
    builder.add_segment(PlainTextSegment(
        "Trying it out again, again. "
    ))
    builder.add_segment(PlainTextSegment(
        "Here's a link to another favorite website: "
    ))
    builder.add_segment(HyperlinkSegment(
        text="More blue link text", url="https://brian.gawalt.com/risk/"
    ))
    builder.post(login)


if __name__ == "__main__":
    main()