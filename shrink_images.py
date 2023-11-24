import pathlib

from PIL import Image


_RAW_ROOT_DIR = 'img/raw/'
_PROC_ROOT_DIR = 'img/proc/'


def process_image(img_path: pathlib.Path) -> None:
    img_orig = Image.open(img_path)
    w_orig, h_orig = img_orig.size
    w_new = 600
    h_new = int(float(h_orig * w_new) / w_orig)
    img_new = img_orig.resize((w_new, h_new), Image.Resampling.LANCZOS)
    # This is buggy!!  I couldn't immediately get this to create directories
    # as it went, so instead I just made a recursive copy of RAW into PROC, and
    # then had this job overwrite the files.
    out_path = str(img_path).replace(_RAW_ROOT_DIR, _PROC_ROOT_DIR)
    img_new.save(out_path)


def main():
    raw_root_path = pathlib.Path(_RAW_ROOT_DIR)
    img_paths = tuple(raw_root_path.glob('*/*.jpeg'))
    n = len(img_paths)
    for i, p in enumerate(sorted(img_paths), 1):
        process_image(p)
        print(p, f'processed ({i} of {n})')


if __name__ == "__main__":
    main()