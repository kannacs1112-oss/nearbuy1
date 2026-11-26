# NEARBUY Desktop — Local Marketplace (v3.0.0, international)

NEARBUY is a local-first marketplace application built with Flask, SQLite and SQLAlchemy. The desktop build runs a private local web server and opens the application in your default browser. It does not require an internet connection for core marketplace operations.

## What is included in v3.0.0

**International**
- Five interface languages: English, Spanish, French, Hindi and Tamil. Visitors choose in the footer; the choice is remembered. Without a choice, the browser's language is used.
- Shops register in any supported country (India, United States, United Kingdom, UAE, Singapore, Australia, France, Spain, Mexico). The country sets the currency and time zone.
- Each shop prices and sells in its own currency. Orders keep the currency and time zone from the moment of purchase.
- Money is formatted per currency: lakh grouping for ₹ (₹12,34,567.00), local separators for Spanish and French.
- Carts and admin totals are shown per currency. Amounts in different currencies are never added together.
- Order and shop times are shown in the shop's own time zone, in unambiguous numeric format.
- Translations live in `locales/*.json`, so they can be reviewed and edited without touching code.

**Marketplace (from v2.x)**
- Customer registration, login, cart, checkout and order history
- Shopkeeper registration, admin approval, product and order management
- Delivery partner dashboard and delivery status workflow
- Administrator dashboard, shop approvals and platform metrics
- Merchant Retail Intelligence: 30-day sales velocity, stock-cover estimates, low-stock alerts and transparent 14-day reorder suggestions
- Merchant stock adjustment workflow and customer-facing stock availability labels
- First-launch owner setup: create your own administrator; no shipped admin password
- CSRF protection on all POST forms, secure password hashing, hardened session defaults
- Per-Windows-user persistent database and generated secret key
- Waitress production-style local server (debug mode is off)
- Windows PyInstaller packaging and Inno Setup installer scripts
- Manual update workflow that backs up the application and preserves the database

## Run from source (Windows)
1. Extract the ZIP. Open PowerShell in the `nearbuy` folder.
2. Create and activate an environment:
   ```powershell
   py -3.10 -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
3. Install dependencies and start:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   python app.py
   ```
4. The browser opens at `http://127.0.0.1:5000`. On first launch, create your administrator account.

## Run the tests
```powershell
python -m pytest -q tests
```
- `tests/test_intl.py` checks translations, currency and time-zone rules. It needs only the standard library and pytest.
- `tests/test_smoke.py` runs the full flow: first-run setup, a US shop selling in USD, checkout, and per-currency admin totals. It needs the full requirements.
- `tests/test_migration.py` upgrades a database created by v2.x and checks that no records are lost.

## Build the Windows desktop distribution
Build on a Windows 10/11 machine (PyInstaller does not cross-compile Windows EXEs from Linux/macOS). Install Python 3.10 or 3.11 64-bit.

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\build_windows.ps1
```

Output: `dist\NEARBUY\NEARBUY.exe` and the complete `dist\NEARBUY` folder. The build includes the translation files and the time zone database (`tzdata`). Use the optional Inno Setup script `installer\NEARBUY.iss` to create a setup installer. Install Inno Setup 6 first, then compile the `.iss` file.

## Adding or fixing a translation
1. Open `locales/<language>.json` (for example `locales/fr.json`). The key is the English text; the value is the translation.
2. Keep placeholders such as `{name}`, `{n}` and `{id}` exactly as they are.
3. Run `python -m pytest -q tests/test_intl.py`. It reports missing strings and changed placeholders.
4. To add a language, add its code and name to `LANGUAGES` in `intl.py` and create `locales/<code>.json` with every key. Right-to-left languages also go in `RTL_LANGUAGES`.

**The Hindi and Tamil translations, and the Spanish and French ones, were drafted by machine-assisted translation and have not yet been checked by native speakers. Have a native speaker review every locale before public use.**

## Currency and time rules
- A shop's country is chosen at registration and sets its currency and time zone. Once the shop has products or orders, the country is locked, because changing it would re-label existing prices.
- Currency is never converted automatically. The platform does not hold exchange rates, so each shop's prices are in its own currency.
- Checkout still handles one shop per order, so a single order always has a single currency.
- Times are stored in UTC and displayed in the shop's time zone.

## Data and backup
Packaged app data is stored at `%LOCALAPPDATA%\NEARBUY\nearbuy.db`; the generated `.secret_key` is stored beside it. Application upgrades do not overwrite this directory. Back up the whole `%LOCALAPPDATA%\NEARBUY` folder before replacing an application build.

## Manual updates (recommended workflow)
1. Close NEARBUY completely.
2. Copy `%LOCALAPPDATA%\NEARBUY` to a safe backup location.
3. Run the new installer / replace the `NEARBUY` application folder with the new release. Do not delete the data folder.
4. Launch NEARBUY and verify the version shown in the footer and that users, shops, products and orders remain present.
5. Keep the previous release and backup until verification is complete.

The app intentionally does not auto-download or silently install updates. You decide when to install a new release. See `docs/MANUAL_UPDATES.md`.

**Upgrading from v2.x changes the database.** The first start adds `country`, `currency` and `timezone` to shops, and `currency` and `timezone` to orders. Existing records are set to India / INR / Asia/Kolkata, which matches the original pilot. Back up before upgrading, and do not roll back to v2.x without restoring that backup.

## Demo data
Fresh installs include fictional sample shops and products in Madurai to make the interface useful immediately. No demo customer, shopkeeper, delivery or administrator accounts are created. Create the first administrator using the first-run setup screen, then register other roles from the app. Remove sample listings before any real public launch.

## Important scope and production notes
- Checkout is simulated; no payment gateway is connected and no real money is collected. A real international launch needs a payment provider per country and its own compliance review.
- Tax is not calculated. Invoices, VAT/GST and sales-tax rules are not implemented.
- Product discovery is keyword matching, not a generative AI model. Keyword matching works on the text as written, so a search in Hindi will not find an English product name. Multilingual search needs a synonym or translation layer, which is not yet built.
- Shop descriptions, product names and addresses are entered by merchants and are shown as written; they are not translated.
- Retail Intelligence uses transparent arithmetic over recent orders, not a trained forecasting model.
- Phone numbers are stored as entered. Include the country code (for example `+91` or `+1`); the app does not validate them yet.
- The desktop build is designed for one computer and local data. It is not a multi-computer synchronization system. Each installation has its own database unless you deliberately configure a shared server database.
- For public multi-user deployment, add HTTPS, verified email/phone, rate limiting, formal database migrations (Alembic), audit logging, backup automation, privacy/terms pages, payment integration, GDPR/local data-protection review and operational monitoring.
- The database upgrade in v3.0.0 is additive and idempotent, but the app does not yet use a formal migration framework. Back up before every upgrade.

## Project layout
```
nearbuy/
  app.py, config.py, models.py, intl.py
  locales/            translations (en source, es, fr, hi, ta)
  templates/, static/
  tests/              test_intl.py, test_smoke.py, test_migration.py
  scripts/build_windows.ps1
  installer/NEARBUY.iss
  docs/MANUAL_UPDATES.md, docs/FOUNDING_PLAN.md, docs/DEMO_CHECKLIST.md
  NEARBUY.spec
```
