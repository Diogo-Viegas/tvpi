DROP TABLE IF EXISTS episodes;
DROP TABLE IF EXISTS series;

CREATE TABLE series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'quero ver',
    rating INTEGER,
    poster_url TEXT,
    tmdb_id INTEGER,
    overview TEXT,
    first_air_date TEXT,
    favorite INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    episode INTEGER NOT NULL,
    title TEXT,
    watched INTEGER NOT NULL DEFAULT 0,
    watched_at TIMESTAMP,
    FOREIGN KEY(series_id) REFERENCES series(id),
    UNIQUE(series_id, season, episode)
);