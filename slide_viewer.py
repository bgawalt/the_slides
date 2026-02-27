"""Pulls up a specific image by rowid in a TkInter window.

Usage, where `slides_db.db3` is the SQLite3 DB file being used:

  $ python slide_viewer.py slides_db.db3 id:1234

That pulls up a specific image.  The `id:` prefix is required.

If you want to pull up a random image, one which has no alt text, simply omit
that last argument.
"""

import base64
import dataclasses
import io
import sqlite3
import sys
import tkinter

from PIL import Image
from PIL import ImageTk


_TARGET_IMAGE_QUERY = """
    SELECT
        rowid,
        jpeg_base64,
        collection,
        alt_text
    FROM slides
    WHERE rowid = ?
"""


_RANDOM_IMAGE_QUERY = """
    SELECT  rowid
    FROM slides
    WHERE LENGTH(alt_text) IS NULL OR LENGTH(alt_text) = 0
    ORDER BY RANDOM()
    LIMIT 1
"""


@dataclasses.dataclass(frozen=True)
class Slide:
    rowid: int
    jpeg_base64: str
    collection: str
    alt_text: str

    @classmethod
    def from_row(cls, row: tuple[int, str, str, str]) -> 'Slide':
        rid, jb64, col, alt = row
        if not alt:
            alt = '[no alt text on file]'
        return Slide(rid, jb64, col, alt)

    @property
    def slide_id(self) -> str:
        return f'{self.collection} :: {str(self.rowid)}'

    def to_tk(self) -> ImageTk.PhotoImage:
        jpeg_bio = io.BytesIO(base64.b64decode(self.jpeg_base64))
        pil_img = Image.open(jpeg_bio, formats=['jpeg'])
        curr_width, curr_height = pil_img.size
        return ImageTk.PhotoImage(
            pil_img.resize(
                (round(curr_width * 2.5), round(curr_height * 2.5)),
                Image.Resampling.LANCZOS)
        )


def get_rowid() -> int | None:
    if len(sys.argv) == 3:
        rowid_str = sys.argv[2]
        if not rowid_str.startswith('id:'):
            raise ValueError(
                f'rowid arg must start with "id:", got {rowid_str}')
        return int(rowid_str[3:])
    conn = sqlite3.connect(sys.argv[1])
    cur = conn.cursor()
    cur.execute(_RANDOM_IMAGE_QUERY)
    rows = cur.fetchall()
    if len(rows) == 0:
        print('No alt-text-less images found.  Congrats!')
        return None
    assert(len(rows) == 1), (
        f'Got too many rows back from random image query ({len(rows)})')
    return rows[0][0]


def main():
    root = tkinter.Tk()

    if len(sys.argv) == 1:
        raise ValueError('Must supply db filename.')
    db_filename = sys.argv[1]
    rowid = get_rowid()
    if rowid is None:
        return
    
    conn = sqlite3.connect(db_filename)
    cur = conn.cursor()
    cur.execute(_TARGET_IMAGE_QUERY, (rowid,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if len(rows) != 1:
        raise ValueError(f'Multiple rows found for rowid {rowid}')
    slide = Slide.from_row(rows[0])

    slide_id_panel = tkinter.Label(root, text=slide.slide_id)
    slide_id_panel.pack()
    slide_tk = slide.to_tk()
    slide_panel = tkinter.Label(root, image=slide_tk)
    slide_panel.pack(side='top')

    alt_text_panel = tkinter.Text(
        root, width=80, height=6, font=('Arial', 15))
    alt_text_panel.insert(1.0, slide.alt_text)
    alt_text_panel.pack(side='top')
    
    root.geometry('%dx%d+%d+%d' % (1600, 1600, 800, 800))
    root.mainloop()


if __name__ == "__main__":
    main()