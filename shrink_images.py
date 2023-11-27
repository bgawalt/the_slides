"""Translates the original image files into a SQLite table of smaller images.

Presuming `sqlite_output.db` is an empty file, or otherwise uninitialized
SQLite3 file, use as:

  $ python shrink_images.py sqlite_output.db3

This scans for JPEGs in directories under `img/raw/`, as specified by the module
constant `_RAW_ROOT_DIR`, and shoves em in a three-column table named `slides`
in that destination DB file.
"""


import base64
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
        jpeg_base64 text
    );
"""

_INSERT_IMAGE_QUERY = """
    INSERT INTO slides (collection, filename, jpeg_base64)
    VALUES (?, ?, ?)
"""


def process_image(img_path: pathlib.Path) -> str:
    """Loads the given big JPEG and returns a shrunken, Base64 version."""
    # Load and resize the image:
    img_orig = Image.open(img_path)
    w_orig, h_orig = img_orig.size
    w_new = 600
    h_new = int(float(h_orig * w_new) / w_orig)
    img_new = img_orig.resize((w_new, h_new), Image.Resampling.LANCZOS)
    # Serialize it into "a file":
    out_bytes_io = io.BytesIO()
    img_new.save(out_bytes_io, format='jpeg')
    # Reload the file and return its bytes as Base64:
    out_bytes_io.seek(0)
    out_bytes = out_bytes_io.read()
    out_b64 = base64.b64encode(out_bytes)
    return out_b64


def dir_to_collection_name(dir_path: pathlib.Path) -> str:
    return 


def main():
    raw_root_path = pathlib.Path(_RAW_ROOT_DIR)
    img_paths = tuple(raw_root_path.glob('*/*.jpeg'))

    db_filename = sys.argv[1]
    conn = sqlite3.connect(db_filename)
    cur = conn.cursor()
    cur.execute(_CREATE_TABLE_QUERY)

    n = len(img_paths)
    for i, p in enumerate(sorted(img_paths), 1):
        small_jpeg_b64 = process_image(p)
        insert_tuple = (
            p.parent.name.replace("__", ", ").replace("_", " "),  # collection
            p.name,  # filename
            small_jpeg_b64  # jpeg_base64
        )
        cur.execute(_INSERT_IMAGE_QUERY, insert_tuple)
        conn.commit()
        print(p, f'processed ({i} of {n})')
    
    conn.close()


if __name__ == "__main__":
    main()