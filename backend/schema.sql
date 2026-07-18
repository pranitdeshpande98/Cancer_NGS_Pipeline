CREATE TABLE runs (
    id SERIAL PRIMARY KEY,
    sample_name TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT now(),
    finished_at TIMESTAMP
);

CREATE TABLE variants (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    chrom TEXT NOT NULL,
    position INTEGER NOT NULL,
    ref TEXT NOT NULL,
    alt TEXT NOT NULL,
    consequence TEXT,
    clinical_significance TEXT
);