"""Translates the original image files into a SQLite table of smaller images.

Presuming `sqlite_output.db` is an empty file, or otherwise uninitialized
SQLite3 file, use as:

  $ python shrink_images.py sqlite_output.db3

This scans for JPEGs in directories under `img/raw/`, as specified by the module
constant `_RAW_ROOT_DIR`, and shoves 'em in a four-column table named `slides`
in that destination DB file.

The four columns of `slides`, in order:

1.  `collection`, the name of the slide deck this slide is drawn from
2.  `filename`, the filename of the slide image file
3.  `file_id_num`, the 1-indexed position of this image file in the sort order
      of this collection's file name
4.  `jpeg_base64`, the Base64 encoding of the image (JPEG format)
"""


import base64
import dataclasses
import io
import pathlib
import sqlite3
import sys

from PIL import Image


_RAW_ROOT_DIR = 'img/raw/'


_CREATE_TABLE_QUERY = """
    CREATE TABLE slides(
        collection text,
        filename text,
        file_id_num integer,
        jpeg_base64 text,
        width integer,
        height integer
    );
"""

_INSERT_IMAGE_QUERY = """
    INSERT INTO slides (
      collection, filename, file_id_num, jpeg_base64, width, height
    )
    VALUES (?, ?, ?, ?, ?, ?)
"""


@dataclasses.dataclass(frozen=True)
class ShrunkenImage:
    bytes_b64: bytes
    width: int
    height: int


def process_image(img_path: pathlib.Path) -> ShrunkenImage:
    """Loads the given big JPEG and returns a shrunken, Base64 version."""
    # Load and resize the image:
    img_orig = Image.open(img_path)
    w_orig, h_orig = img_orig.size
    w_new = 600
    h_new = int(float(h_orig * w_new) / w_orig)
    img_new = img_orig.resize((w_new, h_new), Image.Resampling.LANCZOS)
    w_new, h_new = img_new.size
    # Serialize it into "a file":
    out_bytes_io = io.BytesIO()
    img_new.save(out_bytes_io, format='jpeg')
    # Reload the file and return its bytes as Base64:
    out_bytes_io.seek(0)
    out_bytes = out_bytes_io.read()
    out_b64 = base64.b64encode(out_bytes)
    return ShrunkenImage(out_b64, width=w_new, height=h_new)


def main():
    raw_root_path = pathlib.Path(_RAW_ROOT_DIR)
    img_paths = tuple(raw_root_path.glob('*/*.jpeg'))

    db_filename = sys.argv[1]
    conn = sqlite3.connect(db_filename)
    cur = conn.cursor()
    cur.execute(_CREATE_TABLE_QUERY)

    n = len(img_paths)
    prev_coll = None
    file_id_num = 1
    for i, p in enumerate(sorted(img_paths), 1):
        small_jpeg = process_image(p)
        collection = p.parent.name.replace("__", ", ").replace("_", " ")
        if collection != prev_coll:
            file_id_num = 1
        insert_tuple = (
            collection,  # collection
            p.name,  # filename
            file_id_num,  # file_id_num
            small_jpeg.bytes_b64 , # jpeg_base64
            small_jpeg.width,  # width
            small_jpeg.height  # height
        )
        cur.execute(_INSERT_IMAGE_QUERY, insert_tuple)
        conn.commit()
        print(p, f'processed ({i} of {n})')
        file_id_num += 1
        prev_coll = collection
    
    conn.close()


if __name__ == "__main__":
    main()