"""Pulls up images that need alt text and lets you type it in.

Usage, where `slides_db.db3` is the SQLite3 DB file being used:

  $ python add_alt_text.py slides_db.db3

This is a janky Tkinter app that does not look or feel good, but it is getting
the job done.
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

    @classmethod
    def from_row(cls, row: tuple[int, str, int, int]) -> 'Slide':
        rid, jb64, w, h = row
        return Slide(rid, jb64, w, h)

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
    if not row:
        print("Nothing to do here.")
    slide = Slide.from_row(row)
    print('Got slide', slide.rowid, slide.width, slide.height)
    slide_tk = slide.to_tk()
    slide_panel = tkinter.Label(root, image=slide_tk)
    slide_panel.pack(side='top')

    alt_text_panel = tkinter.Text(
        root, width=80, height=6, font=("Arial", 15))
    alt_text_panel.insert(1.0, "Enter alt text here.")
    alt_text_panel.pack(side="top")

    def submit():
        print('submitted:')
        print(alt_text_panel.get('1.0', 'end'))
        alt_text_panel.delete('1.0', 'end')
        row = cur.fetchone()
        if not row:
            alt_text_panel.insert('1.0', 'All done!!')
            return
        slide = Slide.from_row(row)
        print('Got slide', slide.rowid, slide.width, slide.height)
        slide_tk = slide.to_tk()
        slide_panel.configure(image=slide_tk)
        slide_panel.image = slide_tk
        alt_text_panel.insert('1.0', 'Enter alt text here.')

    submit_button = tkinter.Button(root, text='Submit', command=submit)
    submit_button.pack(side='top')

    root.mainloop()    
    conn.close()


if __name__ == "__main__":
    main()