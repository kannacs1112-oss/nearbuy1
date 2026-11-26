# NEARBUY manual update and rollback policy

## Release process
1. Update source and increment `app.config["VERSION"]` in `app.py` and `MyAppVersion` in `installer/NEARBUY.iss`.
2. Build on Windows using `scripts/build_windows.ps1`.
3. Test the new build with a clean test profile and a copy of a real test database.
4. Package the installer and publish a release note describing changes and any database changes.

## User update process
1. Exit NEARBUY. Confirm `NEARBUY.exe` is no longer running.
2. Back up `%LOCALAPPDATA%\NEARBUY` (database and secret key).
3. Install the new application build. The installer updates files under Program Files and does not touch user data.
4. Launch and verify the app.

## Rollback
1. Exit NEARBUY.
2. Reinstall the previous application build.
3. Restore the matching pre-upgrade data backup only if the newer release changed the database schema. Never restore an old database over newer orders without first preserving a copy of the newer database.

## Important
- Updates are manual by design. There is no background updater and no remote code execution.
- The database and secret key are user data, not application files. Never include them in the installer.
- This version does not yet include Alembic migrations. Back up before every release that changes SQLAlchemy models.

## Release notes: 3.0.0 (international)
- Database change: shops gain `country`, `currency`, `timezone`; orders gain `currency`, `timezone`. The first start adds these columns automatically with defaults of India / INR / Asia/Kolkata, so existing records keep their meaning. No rows are deleted or rewritten.
- Rollback: a v2.x build cannot write orders into a v3.0.0 database, because it does not know the new `currency` column. Roll back only by restoring the pre-upgrade backup of `%LOCALAPPDATA%\NEARBUY`.
- Test before release: run `python -m pytest -q tests` on Windows. `test_migration.py` checks the upgrade path against a v2-style database.
- Translations must be reviewed by native speakers before a release is announced to a new language community.
