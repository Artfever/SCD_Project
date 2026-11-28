CREATE TABLE cards (
    id           text PRIMARY KEY,
    name         text NOT NULL,
    summary      text NOT NULL,
    problem      text NOT NULL DEFAULT '',
    customer     text NOT NULL DEFAULT '',
    niche_tags   text[] NOT NULL DEFAULT '{}',
    stage        text NOT NULL DEFAULT 'unknown',
    funding_usd  bigint,
    source       text NOT NULL,
    url          text NOT NULL,
    published_at date,
    fetched_at   timestamptz NOT NULL,
    text         text NOT NULL DEFAULT '',
    content_hash text NOT NULL,
    updated_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX cards_source_date ON cards (source, published_at);
CREATE INDEX cards_tags ON cards USING gin (niche_tags);

-- Every place a card was seen, so each claim can be credited
CREATE TABLE card_sources (
    card_id    text NOT NULL REFERENCES cards ON DELETE CASCADE,
    platform   text NOT NULL,
    url        text NOT NULL,
    fetched_at timestamptz NOT NULL,
    PRIMARY KEY (card_id, platform, url)
);

CREATE TABLE chunks (
    chunk_id text PRIMARY KEY,
    card_id  text NOT NULL REFERENCES cards ON DELETE CASCADE,
    position integer NOT NULL,
    text     text NOT NULL,
    tsv      tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED
);
CREATE INDEX chunks_card ON chunks (card_id);
CREATE INDEX chunks_tsv ON chunks USING gin (tsv);

CREATE TABLE ingestion_runs (
    run_id      text NOT NULL,
    source      text NOT NULL,
    added       integer NOT NULL,
    updated     integer NOT NULL,
    unchanged   integer NOT NULL,
    dropped     integer NOT NULL,
    finished_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (run_id, source)
);
