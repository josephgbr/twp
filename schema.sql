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

-- Create Default Admin User (admin:admin)
INSERT OR IGNORE INTO users ('username','password') 
VALUES('admin', 'c7ad44cbad762a5da0a452f9e854fdc1e0e7a52a38015f23f3eab1d80b931dd472634dfac71cd34ebc35d16ab7fb8a90c81f975113d6c7538dc69dd8de9077ec');
