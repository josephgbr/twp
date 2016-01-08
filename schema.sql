CREATE TABLE IF NOT EXISTS issues (
    "server_id" INTEGER NOT NULL,
    "date" REAL NOT NULL,
    "message" TEXT
);

CREATE TABLE IF NOT EXISTS players (
    "name" TEXT NOT NULL,
    "create_date" REAL NOT NULL DEFAULT (0),
    "last_seen_date" REAL NOT NULL DEFAULT (0),
    "status" INTEGER NOT NULL DEFAULT (0)
);

CREATE TABLE IF NOT EXISTS "players_server" (
    "server_id" INTEGER NOT NULL,
    "name" TEXT NOT NULL,
    "clan" TEXT,
    "country" INTEGER,
    "date" REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS servers (
    "fileconfig" TEXT NOT NULL,
    "base_folder" TEXT NOT NULL,
    "bin" TEXT,
    "alaunch" INTEGER NOT NULL DEFAULT (0),
    "port" TEXT NOT NULL DEFAULT (8303),
    "name" TEXT NOT NULL DEFAULT ('Unnamed Server'),
    "status" TEXT NOT NULL DEFAULT ('Stopped'),
    "gametype" TEXT NOT NULL DEFAULT ('dm'),
    "register" INTEGER NOT NULL DEFAULT (1),
    "password" INTEGER NOT NULL DEFAULT (0),
    "logfile" TEXT,
    "econ_port" TEXT,
    "econ_password" TEXT
);

CREATE TABLE IF NOT EXISTS users (
    "username" TEXT PRIMARY KEY,
    "password" TEXT NOT NULL
, "level" INTEGER  NOT NULL  DEFAULT (1));
