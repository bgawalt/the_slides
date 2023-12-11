"""Posts an image to BlueSky.

Usage:

  $ python post_image.py credfile.secret slides_input.db3

See README for description of the credentials file and the table expected
in the SQLite file.
"""

import base64
import pathlib
import sys
import sqlite3

import bsky_lib


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


_COLLECTION_URLS = {
    "AFSC 35mm presentation slides": "https://www.sambiddle.com/afsc",
    "Alaskan Air Command": "https://www.sambiddle.com/aac",
    "MX Missile": "https://www.sambiddle.com/mx-missile",
    "NORAD 35mm presentation slides": "https://www.sambiddle.com/norad",
    "ORGANIZATION FOR NATIONAL SECURITY": "https://www.sambiddle.com/organization-for-national-security-vd037",
    "SERIES 78, AERO SPACE DEFENSE COMMAND BOX 1 OF 2 V-0092": "https://www.sambiddle.com/series-78-aero-space-defense-command-box-1-of-2-v-0092",
    "SOVIET MILITARY CAPABILITIES S-100-18-85 BOX 1 OF 2": "https://www.sambiddle.com/soviet-military-capabilities-s-100-18-85-box-1-of-2",
    "US Navy 35mm presentation slides": "https://www.sambiddle.com/us-navy",
    "V-0073 TACTICAL AIR COMMAND 1978 BX 1 of 2": "https://www.sambiddle.com/v-0073-tactical-air-command-1978-bx-1-of-2"
}


def post_image(
    collection: str, file_rank: int, collection_size: int, jpeg_b64: str,
    login: bsky_lib.BSkyLogin
):
    collection_url = _COLLECTION_URLS.get(
        collection, "https://www.sambiddle.com/35mm-scans")
    builder = bsky_lib.BSkyMessageBuilder()
    builder.add_segment(
        bsky_lib.PlainTextSegment(
            f'"{collection}," slide {file_rank} of {collection_size} ['
        )
    )
    builder.add_segment(
        bsky_lib.HyperlinkSegment(text="gallery", url=collection_url)
    )
    builder.add_segment(bsky_lib.PlainTextSegment("]"))
    img_bytes = base64.b64decode(jpeg_b64)
    builder.add_jpeg(img_bytes)
    builder.post(login)


def main():
    credfile = pathlib.Path(sys.argv[1])
    login = bsky_lib.BSkyLogin.from_file(credfile)

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
