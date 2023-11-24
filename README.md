# Sam Biddle's "The Slides"

Sam Biddle has collected, scanned, and curated a large number of slides.
"The slides appear to be 1970s/1980s informational or training images from the
United States Air Force, NORAD, Navy, and beyond." You can visit Sam's site
dedicated to these slides at
[sambiddle.com](https://www.sambiddle.com/35mm-scans), and download the slides
themselves via his account at
[the Internet Archive](https://archive.org/details/@sambiddle).

This Python suite posts The Slides to Bluesky, once an hour.

## Reprocessing originals

I have downloaded, just manually, via browser, nine slide collections in JPEG
format.  These nine were the ones available on the Internet Archive (link above)
on Nov 23, 2023, and match the galleries available on Sam's site.  Altogether,
they come to 291 images of total size 985 MB.  Their typical resolution was
around 5,550 pixels wide by 3,500 pixels tall.

I will reprocess these images to a width of 600 pixels, since that seems to be
just a bit wider than the photos you see in your BlueSky timeline.

I've organized these originals in directories with names corresponding to the
names Sam gave the collections.  The only weird part is I did some minor
substitutions to make them feel more like real directory names -- no whitespace,
no punctuation.  This just means that `'_'` in a directory name means "a space"
in the actual collection name, while `'__'` means "a comma, then a space."
Capitalization & casing are kept constant. So the directory
`SERIES_78__AERO_SPACE_DEFENSE_COMMAND_BOX_1_OF_2_V-0092` maps to its collection
name "SERIES 78, AERO SPACE DEFENSE COMMAND BOX 1 OF 2 V-0092".  This matters
because I want to include the original collection name in the text of the
BlueSky post, and these directories are the only way I save those names.