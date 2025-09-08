ATTACH TABLE _ UUID '29f45214-5a15-4e1a-b754-4ed13148928c'
(
    `type` String,
    `sourceVersion` String,
    `sourceName` String,
    `device` String,
    `startDate` DateTime,
    `endDate` DateTime,
    `creationDate` DateTime,
    `unit` String,
    `value` String,
    `numerical` Float32
)
ENGINE = MergeTree
ORDER BY startDate
SETTINGS index_granularity = 8192
