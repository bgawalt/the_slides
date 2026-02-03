WITH rowid_file_id_nums AS (
    SELECT
        rowid,
        row_number() OVER collection_partition AS file_id_num
    FROM slides
    WINDOW collection_partition AS (PARTITION BY collection ORDER BY filename)
)
UPDATE slides
SET file_id_num = (
    SELECT file_id_num
    FROM rowid_file_id_nums
    WHERE rowid = slides.rowid
);