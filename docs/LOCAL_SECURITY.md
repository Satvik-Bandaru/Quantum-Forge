# Local service security and database upgrades

M2 keeps the application bound to loopback, with one bounded CPU job at a time.

## HTTP clients

Production accepts localhost, 127.0.0.1 and ::1 Host names. `testserver` is enabled only by `create_app(testing=True)`, which also requires an explicit database path outside the application's data directory.

POST, PUT, PATCH and DELETE require an Origin matching the request's scheme, host and effective port. Browser requests from the application already provide this. CLI clients should send, for example, `Origin: http://127.0.0.1:8777` when accessing that address. A different localhost port is rejected. For a deliberately originless local CLI workflow, the server may be launched with `QF_ALLOW_ORIGINLESS=1`; this is an explicit exception and is not the default. The body limit remains 256,000 bytes for both fixed-length and streamed bodies.

## Existing database upgrades

Opening an old database now stops startup with `MigrationRequired` unless the owner explicitly opts in. New empty databases initialize automatically. Existing user databases have **not** been migrated as part of M2 verification.

After owner approval and a clean shutdown of the old service, a one-time launch with `QF_ALLOW_DB_MIGRATION=1 ./start.command` permits the upgrade. Do not leave this variable enabled globally. The launcher reuses an already-running service, so the old process must first be stopped for an upgrade to occur.

Before schema changes, the migration engine reserves the SQLite writer and makes a SQLite backup beside the database, named `backup-<UTC timestamp>-<unique suffix>.sqlite3`. The backup includes committed WAL pages. Versioned schema changes run transactionally; failed changes roll back, and the backup remains. Unsupported future schema versions are rejected. v1 describes the original tables; v2 adds a nullable cached history summary. Existing records with no summary retain a fallback to their full document. Subsequent writes populate the cache.

To recover from an unsuccessful upgrade, stop the service and preserve both the original database and backup before selecting a restore path. Do not overwrite a live SQLite database or remove its WAL files.

## Storage and workers

`QF_MAX_SAVED_CIRCUITS` defaults to 1,000 and has a minimum of 100. Saving a circuit transactionally removes the oldest saved circuits beyond that cap. This affects saved circuit templates, not experiment history.

Worker termination and join occur outside the request coordination lock. The slot stays reserved until the process is confirmed dead and the terminal record is persisted. Transient cleanup/storage failures retain the original result and retry; persistent failures intentionally keep the slot unavailable and emit a warning. Closing a manager disallows new jobs. The existing timeout, memory and concurrency limits remain in force.

These are local-service safeguards, not multi-user authentication or remote deployment support.
