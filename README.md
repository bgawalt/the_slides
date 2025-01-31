# Sam Biddle's "The Slides"

Sam Biddle has collected, scanned, and curated a large number of slides.
"The slides appear to be 1970s/1980s informational or training images from the
United States Air Force, NORAD, Navy, and beyond." You can visit Sam's site
dedicated to these slides at
[sambiddle.com](https://www.sambiddle.com/35mm-scans), and download the slides
themselves via his account at
[the Internet Archive](https://archive.org/details/@sambiddle).

This Python suite posts The Slides to Bluesky, four times a day*, at the account
[theslides.bsky.social](https://bsky.app/profile/theslides.bsky.social).

(* Or, it will, soon! Before Dec 1, 2023, for sure.)

## Dependencies

This project relies on:

*  [Pillow](https://pillow.readthedocs.io/) to process the original slide scans
   into tinier, more-uploadable sizes
*  [requests](https://pypi.org/project/requests/) for communicating with BlueSky

They can be installed with these commands:

```
$ pip install --upgrade Pillow
$ pip install requests
```

Here's what the virtualenv I have on my laptop looks like overall
(Nov 23, 2023):

```
$ pip freeze
certifi==2023.11.17
charset-normalizer==3.3.2
idna==3.5
Pillow==10.1.0
requests==2.31.0
urllib3==2.1.0
```

## `shrink_images.py`: Reprocessing originals

I have downloaded, just manually, via browser, the slide collections in JPEG
format, as available on the Internet Archive (link above). The first nine were
downloaded on Nov 23, 2023, and the next five on Jan 29, 2025, and match the
galleries available on Sam's site.  Altogether, they come to 422 images of total
size 1.5 GB.  Their typical resolution was around 5,550 pixels wide by 3,500
pixels tall.

I reprocess these images to a width of 600 pixels, since that seems to be
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

The shrunken images are serialized as JPEGs, and their Base64-encoded bytes
are stored in a SQLite table named `slides` with the following columns,
all of type `text`:

*  `collection`: The name of the slide deck the image comes from
*  `filename`: The actual filename of the image
*  `jpeg_base64`: Base64 encoding of the 600-pixel-wide version of the image


## `post_image.py`: Post a processed slide to BlueSky

You supply login credentials with a text file of this wacky custom format, with
these specific keys pointing to your own particular values:

```
ATP_HOST = [your host, very likely to be https://bsky.social]
ATP_USERNAME = [your username; like, right now, I'm using brian.gawalt.com]
ATP_PASSWORD = [an app password for this account]
```

To be clear: everything outside the square brackets needs to appear in this
credentials file verbatim.

The script then connects to, and extracts an image and its metadata from, the
SQLite file created by `shrink_images.py`. It reports the name of the collection
the slide comes from, as well as a "slide X of Y" designation based on the
sort-order of the filename of the slide within its collection.

## TODO

In the order I'll do 'em:

*  Deploy with a 4x daily CRON job
*  Alt text: I'll have to come up with a tool to let me write descriptive text
   for all ~250 slides