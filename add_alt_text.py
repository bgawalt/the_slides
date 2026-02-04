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


_SELECT_ALTLESS_IMAGES_QUERY = """
    SELECT
        rowid,
        jpeg_base64,
        collection
    FROM slides
    WHERE LENGTH(alt_text) IS NULL OR LENGTH(alt_text) = 0
    ORDER BY RANDOM()
    LIMIT 3
"""

class AltTextUpdater:
    """Use this to update the alt text for one row of the slides table."""
    _QUERY = "UPDATE slides SET alt_text = ? WHERE rowid = ?"

    def __init__(self, rowid: int, alt_text: str):
        if rowid < 1:
            raise ValueError(f"Unexpectedly low rowid: {rowid}")
        self._rowid = rowid
        self._alt_text = alt_text
    
    def execute(self, cur: sqlite3.Cursor):
        cur.execute(AltTextUpdater._QUERY, (self._alt_text, self._rowid))


@dataclasses.dataclass(frozen=True)
class Slide:
    rowid: int
    jpeg_base64: str
    collection: str

    @classmethod
    def from_row(cls, row: tuple[int, str, str]) -> 'Slide':
        rid, jb64, col = row
        return Slide(rid, jb64, col)

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


def main():
    root = tkinter.Tk()

    db_filename = sys.argv[1]
    conn = sqlite3.connect(db_filename)
    read_cur = conn.cursor()
    write_cur = conn.cursor()

    all_done = False
    def mark_all_done():
        all_done = True

    read_cur.execute(_SELECT_ALTLESS_IMAGES_QUERY)
    row = read_cur.fetchone()
    if not row:
        print("Nothing to do here.")
    slide = Slide.from_row(row)

    slide_id_panel = tkinter.Label(root, text=slide.slide_id)
    slide_id_panel.pack()
    slide_tk = slide.to_tk()
    slide_panel = tkinter.Label(root, image=slide_tk)
    slide_panel.pack(side='top')

    alt_text_panel = tkinter.Text(
        root, width=80, height=6, font=('Arial', 15))
    alt_text_panel.insert(1.0, 'Enter alt text here.')
    alt_text_panel.pack(side='top')

    def submit():
        print('Attempting to save alt text...')
        if all_done:
            print('i SAID all DONE.')
            root.destroy()
            return
        AltTextUpdater(
            rowid=int(slide_id_panel['text'].split(" :: ")[-1]),
            alt_text=alt_text_panel.get('1.0', 'end')
        ).execute(write_cur)
        conn.commit()
        print('... success.')

        alt_text_panel.delete('1.0', 'end')
        row = read_cur.fetchone()
        if not row:
            root.quit()
            return
        slide = Slide.from_row(row)
        print('Got slide', slide.slide_id)
        slide_tk = slide.to_tk()
        slide_id_panel.configure(text=slide.slide_id)
        slide_panel.configure(image=slide_tk)
        slide_panel.image = slide_tk  # type: ignore
        alt_text_panel.insert('1.0', 'Enter alt text here.')

    submit_button = tkinter.Button(root, text='Submit', command=submit)
    submit_button.pack(side='top')

    root.mainloop()    
    conn.close()


if __name__ == "__main__":
    main()