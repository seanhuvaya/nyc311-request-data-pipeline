CREATE TABLE IF NOT EXISTS metadata.ingestion_metadata (
    pipeline_name TEXT NOT NULL,
    source_name TEXT NOT NULL,
    watermark_column TEXT NOT NULL,

    watermark_value TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (pipeline_name, source_name, watermark_column)
);