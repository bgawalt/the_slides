"""Pulls up images that need alt text and lets you type it in.

Usage, where `slides_db.db3` is the SQLite3 DB file being used:

  $ python add_alt_text.py slides_db.db3

flurpity floo
"""

import base64
import dataclasses
import io
import sqlite3
import sys
import tkinter

from PIL import Image
from PIL import ImageTk


_SELECT_ALTLESS_IMAGES = """
    SELECT
        rowid,
        jpeg_base64,
        width,
        height
    FROM slides
    WHERE LENGTH(alt_text) IS NULL OR LENGTH(alt_text) = 0
"""


@dataclasses.dataclass(frozen=True)
class Slide:
    rowid: int
    jpeg_base64: str
    width: int
    height: int

    def to_tk(self) -> ImageTk.PhotoImage:
        jpeg_bio = io.BytesIO(base64.b64decode(self.jpeg_base64))
        pil_img = Image.open(jpeg_bio, formats=['jpeg'])
        return ImageTk.PhotoImage(pil_img)


def main():
    root = tkinter.Tk()
    
    db_filename = sys.argv[1]
    conn = sqlite3.connect(db_filename)
    cur = conn.cursor()
    cur.execute(_SELECT_ALTLESS_IMAGES)
    row = cur.fetchone()
    rid, jb64, w, h = row
    s = Slide(rid, jb64, w, h)
    stk = s.to_tk()

    panel = tkinter.Label(root, image=stk)
    panel.pack(side="top")
    root.mainloop()
    
    conn.close()


if __name__ == "__main__":
    main()