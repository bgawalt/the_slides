"""Translates the original image files into a SQLite table of smaller images.

Usage, where `slides_db.db3` is the SQLite3 DB file being used:

  $ python shrink_images.py slides_db.db3

This scans for JPEGs in directories under `img/raw/`, as specified by the module
constant `_RAW_ROOT_DIR`, and shoves 'em in a seven-column table named `slides`
in that destination DB file.  Before processing and inserting an image, it makes
sure no existing row in the table matches the candidate image's metadata (its
collection and file names).

The seven columns of `slides`, in order:

1.  `collection`, the name of the slide deck this slide is drawn from
2.  `filename`, the filename of the slide image file
3.  `file_id_num`, the 1-indexed position of this image file in the sort order
      of this collection's file name
4.  `jpeg_base64`, the Base64 encoding of the image (JPEG format)
5.  `width`, the width of the image in pixels
6.  `height`, the height of the image in pixels
7.  `alt_text`, the alt text entered for this image.  This is initially blank;
      you need to add alt text with `add_alt_text.py`.
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
    CREATE TABLE IF NOT EXISTS slides(
        collection text NOT NULL,
        filename text NOT NULL,
        file_id_num integer,
        jpeg_base64 text NOT NULL,
        width integer NOT NULL CHECK(width > 1),
        height integer NOT NULL CHECK(width > 1),
        alt_text text
    );
"""


_SELECT_EXISTING_QUERY = "SELECT collection, filename FROM slides;"


## Note: no `file_id_num` and no `alt_text`
_INSERT_IMAGE_QUERY = """
    INSERT INTO slides (
      collection, filename, jpeg_base64, width, height
    )
    VALUES (?, ?, ?, ?, ?)
"""


_UPDATE_FILE_ID_NUM_QUERYFILE = "./assign_file_id_num.sql"


@dataclasses.dataclass(frozen=True)
class ShrunkenImage:
    bytes_b64: bytes
    width: int
    height: int


def apply_file_id_nums(cur: sqlite3.Cursor):
    with open(_UPDATE_FILE_ID_NUM_QUERYFILE) as queryfile:
        query = queryfile.read()
    cur.execute(query)
            

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
    img_paths = tuple(sorted(raw_root_path.glob('*/*.jpeg')))

    db_filename = sys.argv[1]
    conn = sqlite3.connect(db_filename)
    cur = conn.cursor()
    cur.execute(_CREATE_TABLE_QUERY)
    cur.execute(_SELECT_EXISTING_QUERY)
    existing_slides = set(
        (collection, filename) for collection, filename in cur.fetchall())

    n = len(img_paths)
    duplicate_count = 0
    for i, p in enumerate(sorted(img_paths), 1):
        collection = p.parent.name.replace("__", ", ").replace("_", " ")
        if (collection, p.name) in existing_slides:
            duplicate_count += 1
            continue
        small_jpeg = process_image(p)
        insert_tuple = (
            collection,  # collection
            p.name,  # filename
            small_jpeg.bytes_b64 , # jpeg_base64
            small_jpeg.width,  # width
            small_jpeg.height  # height
        )
        cur.execute(_INSERT_IMAGE_QUERY, insert_tuple)
        conn.commit()
        print(p, f'processed ({i} of {n})')
    apply_file_id_nums(cur)
    print(f'Duplicate count: {duplicate_count} of {n}')
    conn.close()


if __name__ == "__main__":
    main()