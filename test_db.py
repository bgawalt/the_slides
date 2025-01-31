"""Check all the images in the SQLite DB.

Specifically,

*  Are all the entries in the `collection` column recognized Biddle galleries?
*  Do all the `jpeg_base64` column's strings really parse into JPEGs?
*  Are all the images "big" in both dimensions?

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
  jpeg_base64,
  width, 
  height
FROM slides
"""


def main():
  db_filename = sys.argv[1]
  conn = sqlite3.connect(db_filename)
  cur = conn.cursor()
  cur.execute(_QUERY)
  i = 0
  for collection, filename, jpeg_b64, width, height in cur.fetchall():
    i += 1
    if collection not in post_image.COLLECTION_URLS:
      raise ValueError(f"unrecognized collection {collection}")
    img_bytes = base64.b64decode(jpeg_b64)
    bio = io.BytesIO()
    bio.write(img_bytes)
    try:
      _ = Image.open(bio)
    except:
      print(f"{collection}:{filename} has unparseable jpeg_base64")
      raise
    if width < 100:
      raise ValueError(f"{collection}:{filename} is not wide enough: {width}")
    if height < 100:
      raise ValueError(f"{collection}:{filename} is not tall enough: {height}")
  print(f"Successfully scanned {i} images")


if __name__ == "__main__":
  main()