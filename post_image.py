"""Posts an image to BlueSky.

Usage:

  $ python post_image.py credfile.secret slides_input.db3

See README for description of the credentials file and the table expected
in the SQLite file.
"""

import base64
import dataclasses
import hashlib
import pathlib
import sys
import sqlite3

import bsky_lib


_SELECT_SLIDE_QUERY = """
    WITH collection_counts AS (
        SELECT collection, COUNT(*) as num_img
        FROM slides
        GROUP BY collection
    )
    SELECT
        sl.rowid,
        sl.collection,
        sl.file_id_num,
        cc.num_img,
        sl.jpeg_base64,
        sl.width,
        sl.height,
        sl.alt_text
    FROM
        slides AS sl
        LEFT JOIN collection_counts AS cc
        ON sl.collection = cc.collection
    ORDER BY RANDOM()
    LIMIT 1
"""


COLLECTION_URLS = {
    "AFSC 35mm presentation slides": "https://www.sambiddle.com/afsc",
    "Alaskan Air Command": "https://www.sambiddle.com/aac",
    "MX Missile": "https://www.sambiddle.com/mx-missile",
    "NORAD 35mm presentation slides": "https://www.sambiddle.com/norad",
    "ORGANIZATION FOR NATIONAL SECURITY": "https://www.sambiddle.com/organization-for-national-security-vd037",
    "SERIES 78, AERO SPACE DEFENSE COMMAND BOX 1 OF 2 V-0092": "https://www.sambiddle.com/series-78-aero-space-defense-command-box-1-of-2-v-0092",
    "SOVIET MILITARY CAPABILITIES S-100-18-85 BOX 1 OF 2": "https://www.sambiddle.com/soviet-military-capabilities-s-100-18-85-box-1-of-2",
    "US Navy 35mm presentation slides": "https://www.sambiddle.com/us-navy",
    "V-0073 TACTICAL AIR COMMAND 1978 BX 1 of 2": "https://www.sambiddle.com/v-0073-tactical-air-command-1978-bx-1-of-2",
    "Untitled Slide Box 1": "https://www.sambiddle.com/new-page",
    "Air Force Communications Command": "https://www.sambiddle.com/afcc",
    "Military Airlift Command": "https://www.sambiddle.com/mac",
    "MATHER NAV TRAINING S--1124 Bx 1 of 2": "https://www.sambiddle.com/mather-nav",
    "Untitled Slide Box 2": "https://www.sambiddle.com/unlabeled-box-2",
    "SOVIET MILITARY CAPABILITIES S-100-18-85 BOX 2 OF 2": "https://www.sambiddle.com/soviet-military-capabilities-s-100-18-85-box-2-of-2"
}


@dataclasses.dataclass(frozen=True)
class Slide:
    """A slide, as fetched from the SQLite database."""
    collection: str
    rank: int
    collection_size: int
    jpeg: bytes
    width: int
    height: int
    alt_text: str

    def __post_init__(self):
        if self.collection not in COLLECTION_URLS:
            raise ValueError(f'Unrecognized collection {self.collection}')            
        if self.rank < 1:
            raise ValueError(f'rank too small: {self.rank}')
        if self.collection_size < 5:
            raise ValueError(
                f'collection size too small: {self.collection_size}')
        if self.rank > self.collection_size:
            raise ValueError(
                f'rank ({self.rank}) is too large relative to collection size '
                f'({self.collection_size})'
            )
        if self.width <= 10:
            raise ValueError(f'Image width too small: {self.width}')
        if self.height <= 10:
            raise ValueError(f'Image width too small: {self.height}')
        if len(self.jpeg) < 10:
            raise ValueError(f'Image bytes too short: {len(self.jpeg)}')
        if not self.alt_text:
            raise ValueError('Must supply alt text, even if just row id')

    def __str__(self) -> str:
        return f'{self.collection} {self.rank} {self.collection_size}'

    @classmethod
    def from_cursor(cls, cur: sqlite3.Cursor) -> 'Slide':
        rowid, collection, rank, col_size, jpeg_b64, w, h, alt = cur.fetchone()
        if alt is None:
            alt = '[no alt text added yet! reply with yours!] '
        alt += f'id:{rowid}'
        img_bytes = base64.b64decode(jpeg_b64)
        return Slide(
            collection=collection,
            rank=rank,
            collection_size=col_size,
            jpeg=img_bytes,
            width=w,
            height=h,
            alt_text=alt
        )


def post_image(slide: Slide, db_hash: str, login: bsky_lib.BSkyLogin):
    collection_url = COLLECTION_URLS.get(
        slide.collection, "https://www.sambiddle.com/35mm-scans")
    builder = bsky_lib.BSkyMessageBuilder()
    builder.add_segment(
        bsky_lib.PlainTextSegment(
            f'"{slide.collection}," slide {slide.rank} of '
            + f'{slide.collection_size} ['
        )
    )
    builder.add_segment(
        bsky_lib.HyperlinkSegment(text="gallery", url=collection_url)
    )
    builder.add_segment(bsky_lib.PlainTextSegment("]"))
    builder.add_jpeg(
        slide.jpeg,
        width=slide.width,
        height=slide.height,
        alt_text=(slide.alt_text + f" db:{db_hash}")
      )
    builder.post(login)


def db_hashcode(db_filename: str) -> str:
    with open(db_filename, 'rb') as infile:
      contents = infile.read()
    h = hashlib.sha256()
    h.update(contents)
    return h.hexdigest()[:5]


def main():
    credfile = pathlib.Path(sys.argv[1])
    login = bsky_lib.BSkyLogin.from_file(credfile)

    db_filename = sys.argv[2]
    db_hash = db_hashcode(db_filename)
    print("Database version:", db_hash)

    conn = sqlite3.connect(db_filename)
    cur = conn.cursor()
    cur.execute(_SELECT_SLIDE_QUERY)
    slide = Slide.from_cursor(cur)
    print(slide)
    post_image(slide, db_hash, login)
    conn.close()


if __name__ == "__main__":
    main()
