"""Check all the images in the SQLite DB.

Specifically,

*  Are all the entries in the `collection` column recognized Biddle galleries?
*  Do all the `jpeg_base64` column's strings really parse into JPEGs?

Usage:

  $ python test_db.py sqlite_file.db3
  
"""

import base64
import io
import sqlite3
import sys

from PIL import Image

import post_image


_QUERY = """
SELECT
  collection,
  filename,
  jpeg_base64
FROM slides
"""


def main():
  db_filename = sys.argv[1]
  conn = sqlite3.connect(db_filename)
  cur = conn.cursor()
  cur.execute(_QUERY)
  i = 0
  for collection, filename, jpeg_b64 in cur.fetchall():
    i += 1
    if collection not in post_image.COLLECTION_URLS:
      raise ValueError(f"unrecognized collection {collection}")
    img_bytes = base64.b64decode(jpeg_b64)
    bio = io.BytesIO()
    bio.write(img_bytes)
    try:
      _ = Image.open(bio)
    except:
      print(f"filename {filename} has unparseable jpeg_base64")
      raise
  print(f"Successfully scanned {i} images")


if __name__ == "__main__":
  main()