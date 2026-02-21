-- Migration: Add weekly_todos and weekly_todo_allocations tables
-- Description: Weekly todo items and per-week, per-day time allocations (Mon-Sun minutes).
-- Run the SQLite block for SQLite databases; run the PostgreSQL block for PostgreSQL.

-- ========== SQLite version ==========
CREATE TABLE IF NOT EXISTS weekly_todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    todo_id INTEGER REFERENCES todos(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_weekly_todos_todo_id ON weekly_todos(todo_id);

CREATE TABLE IF NOT EXISTS weekly_todo_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    weekly_todo_id INTEGER NOT NULL REFERENCES weekly_todos(id) ON DELETE CASCADE,
    week_key TEXT NOT NULL,
    mon INTEGER NOT NULL DEFAULT 0,
    tue INTEGER NOT NULL DEFAULT 0,
    wed INTEGER NOT NULL DEFAULT 0,
    thu INTEGER NOT NULL DEFAULT 0,
    fri INTEGER NOT NULL DEFAULT 0,
    sat INTEGER NOT NULL DEFAULT 0,
    sun INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(weekly_todo_id, week_key)
);

CREATE INDEX IF NOT EXISTS idx_weekly_todo_allocations_weekly_todo_id ON weekly_todo_allocations(weekly_todo_id);
CREATE INDEX IF NOT EXISTS idx_weekly_todo_allocations_week_key ON weekly_todo_allocations(week_key);

-- ========== PostgreSQL version (uncomment if using PostgreSQL) ==========
-- CREATE TABLE IF NOT EXISTS weekly_todos (
--     id SERIAL PRIMARY KEY,
--     title VARCHAR(255) NOT NULL,
--     description TEXT,
--     todo_id INTEGER REFERENCES todos(id),
--     created_at TIMESTAMP NOT NULL DEFAULT NOW(),
--     updated_at TIMESTAMP NOT NULL DEFAULT NOW()
-- );
--
-- CREATE INDEX IF NOT EXISTS idx_weekly_todos_todo_id ON weekly_todos(todo_id);
--
-- CREATE TABLE IF NOT EXISTS weekly_todo_allocations (
--     id SERIAL PRIMARY KEY,
--     weekly_todo_id INTEGER NOT NULL REFERENCES weekly_todos(id) ON DELETE CASCADE,
--     week_key VARCHAR(20) NOT NULL,
--     mon INTEGER NOT NULL DEFAULT 0,
--     tue INTEGER NOT NULL DEFAULT 0,
--     wed INTEGER NOT NULL DEFAULT 0,
--     thu INTEGER NOT NULL DEFAULT 0,
--     fri INTEGER NOT NULL DEFAULT 0,
--     sat INTEGER NOT NULL DEFAULT 0,
--     sun INTEGER NOT NULL DEFAULT 0,
--     created_at TIMESTAMP NOT NULL DEFAULT NOW(),
--     updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
--     UNIQUE(weekly_todo_id, week_key)
-- );
--
-- CREATE INDEX IF NOT EXISTS idx_weekly_todo_allocations_weekly_todo_id ON weekly_todo_allocations(weekly_todo_id);
-- CREATE INDEX IF NOT EXISTS idx_weekly_todo_allocations_week_key ON weekly_todo_allocations(week_key);
