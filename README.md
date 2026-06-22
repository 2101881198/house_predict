# Smart House Exploration Platform

Smart House Exploration Platform is a Django + MySQL course-project prototype for importing, cleaning, storing, analyzing, predicting, and displaying house listing data.

## Features

- MySQL storage for cities, districts, houses, crawl tasks, analysis results, and prediction records.
- Bundled Shandong demo house data that can be imported with management commands.
- Data cleaning for field normalization, invalid record filtering, and source URL de-duplication.
- Dashboard, province analysis, city analysis, house list, house detail, and price prediction pages.
- Django Admin management for base data, houses, crawl tasks, analysis results, and prediction records.

## Setup And Run

Prerequisites:

- MySQL must be installed and running.
- The `mysql` command must be available on `PATH`.
- The configured database user must be able to create/use the project database. Non-root users need the appropriate MySQL grants.

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` now and set the MySQL user, password, host, port, and database name before running migrations.

```powershell
Get-Content scripts/sql/create_database.sql | mysql -u root -p
cd web
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo_data
python manage.py generate_analysis
python manage.py train_price_model
python manage.py createsuperuser
python manage.py runserver
```

In `cmd.exe`, the SQL import can also be run as:

```cmd
mysql -u root -p < scripts\sql\create_database.sql
```

After the server starts, open [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

### mysqlclient On Windows

If `pip install -r requirements.txt` fails while installing `mysqlclient`, prefer a Python version that has a compatible prebuilt wheel. If a wheel is not available, install Microsoft C++ Build Tools and matching MySQL or MariaDB client development libraries, or install a wheel that matches your Python and Windows architecture.

## Demo Crawler

Run the course-project demo crawler flow from the Django project directory:

```powershell
cd web
python manage.py run_demo_crawler --city 济南 --pages 1
```

The first version of the demo crawler does not crawl a real website. It creates a crawl task record and imports the bundled Shandong sample house data.

## Verification Commands

Run these from the Django project directory:

```powershell
cd web
python manage.py check
pytest houses/tests -q
```

## API And Admin

House queries, statistical analysis, prediction, and other public APIs can be accessed directly. Crawl-task management APIs and Django Admin require a logged-in staff user.
