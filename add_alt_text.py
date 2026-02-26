"""Update a slide's alt text in the slides database.

Usage:

  $ python add_alt_text.py slides_db.db3 id:1234 /tmp/alt.txt

Those arguments are:

1)  `slides_db.db3` is the sqlite3 db file used for the slides posts.
2)  `id:1234` is the rowid from the table `slides` of the slide you whose alt
      text you want to update/replace.
3)  `/tmp/alt.txt` is a text file containing the new alt text.
"""

import base64
import dataclasses
import io
import sqlite3
import sys


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


def main():
    db_filename = sys.argv[1]
    rowid_str = sys.argv[2]
    alt_text_filename = sys.argv[3]

    if not rowid_str.startswith('id:'):
        raise ValueError(f'rowid arg must start with "id:", got {rowid_str}')
    rowid_num = int(rowid_str[3:])

    alt_text = None
    with open(alt_text_filename, 'rt') as alt_text_file:
        alt_text = alt_text_file.read().strip()
    if not alt_text:
        raise ValueError(f'Empty alt text after reading {alt_text_filename}')

    
    print(f'Attempting to update rowid {rowid_num} with alt text:\n{alt_text}')
    proceed = input('Proceed [y/n]? ')
    if proceed.strip() != 'y':
        print(f'Exiting (got non-"y" response: {proceed.strip()})')
    
    conn = sqlite3.connect(db_filename)
    cur = conn.cursor()
    AltTextUpdater(rowid=rowid_num, alt_text=alt_text).execute(cur)
    conn.commit()  
    conn.close()



if __name__ == "__main__":
    main()