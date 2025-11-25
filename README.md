# Streaming Service Movie & TV Data Dashboard

Centralized dashboard dataset built from four public streaming catalog CSVs (Netflix, Amazon Prime Video, Hulu, Disney+). The `data_wrangling/etl_streaming_titles.py` script loads and normalizes raw CSV data into a MySQL schema defined in `documents/tv_movie_DDL.sql`.

## 1. Repository Structure (Quick Reference)
```
raw_data/                # Source CSV files (must stay in this relative path)
data_wrangling/          # ETL script and helper docs
	etl_streaming_titles.py
documents/               # SQL DDL for all tables
	tv_movie_DDL.sql
.env.example              # Template for your .env file
README.md
```

## 2. Prerequisites
1. MySQL Server 8.x (or compatible). Install via your OS package manager or download from mysql.com.
2. MySQL Workbench (optional but helpful) OR the MySQL command-line client.
3. Python 3.9+ (recommended 3.10 or later) and `pip`.
4. Basic terminal access (Linux/macOS Terminal or Windows PowerShell/Git Bash).

### Python Packages Needed
Install these once (inside a virtual environment if you prefer):
```
pip install pandas mysql-connector-python python-dotenv
```

## 3. Step-by-Step Setup

### Step 1: Clone or Download the Project
If you have git:
```
git clone https://github.com/nthPerson/MIS686_Streaming_Service_Movie_-_TV_Data_Dashboard.git
cd MIS686_Movie_TV_Dashboard
```
Otherwise download the ZIP and extract it, then open the folder. Repository is located at [MIS686_Streaming_Service_Movie_TV_Data_Dashboard](https://github.com/nthPerson/MIS686_Streaming_Service_Movie_-_TV_Data_Dashboard)

### Step 2: Create the Database and Tables
Open MySQL Workbench OR use the CLI.

Method A (Workbench GUI):
1. Open MySQL Workbench.
2. Select all text from the `documents/tv_movie_DDL.sql` file and copy it. 
3. Paste DDL text into a new Workbench query and run it.</br>
This creates the database (`streaming_media_db`) and all tables.

Method B (MySQL CLI):
```
mysql -u root -p
```
Enter your root password, then:
```
SOURCE /full/path/to/documents/tv_movie_DDL.sql;
```
Confirm tables exist:
```
USE streaming_media_db;
SHOW TABLES;
```
You should see 13 tables (rating, streaming_service, title, movie, tv_show, genre, title_genre, country, title_country, person, role_type, title_person_role, streaming_availability).

### Step 3: Create a Dedicated Database User (Recommended)
Choose a username and strong password (example uses `movie_tv_app`, but you can fill in these details yourself). In MySQL:
```
CREATE USER 'movie_tv_app'@'localhost' IDENTIFIED BY 'YourStrongPasswordHere!';
GRANT ALL PRIVILEGES ON streaming_media_db.* TO 'movie_tv_app'@'localhost';
FLUSH PRIVILEGES;
```

### Step 4: Create Your `.env` File (stores project secrets, like passwords and database credentials, securely so they don't get leaked to GitHub)
In the project root (same folder as `README.md`) create a file named `.env` by copying `.env.example`:
```
cp .env.example .env
```
Edit `.env` and fill in values (remove comments if you like). This is what your `.env` file should look like (with your database username (DB_USER) and password (DB_PASSWORD)):
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=movie_tv_app
DB_PASSWORD=YourStrongPasswordHere!
DB_NAME=streaming_media_db
```

### Step 5: Set Up Python Environment (Required)
From a terminal in the project root folder:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 6: Configure Python Virtual Environment in VScode
1. In VScode, press CRTL + SHIFT + P (or CMD + SHIFT + P in MacOS) to open the Command Palette.
2. Search for `Python: Select Interpreter`.
3. Select the line that says: `Python 3.XX.X (.venv) ./.venv/python ....... Recommended`<br/>
Note that "Recommended" will be highlighted in blue text.

### Step 7: Test the Database Connection
Run the ETL script with the test flag:
```
python data_wrangling/etl_streaming_titles.py --test-connection
```
Expected outcome: a success message listing all required tables. Exit code 0 means OK; any missing tables will be reported (re-run Step 2 if needed).

### Step 8: Perform a Dry Run (No Inserts)
This checks that the four CSV files are readable and the parsing logic works:
```
python etl_streaming_titles.py --dry-run
```
Options:
```
python etl_streaming_titles.py --dry-run --sample-size 10
```
The script prints simulated insert summaries (counts and sample rows). No data is written to MySQL.

### Step 9: Live ETL Run (Actual Inserts)
When dry run looks good:
```
python etl_streaming_titles.py --live-run
```
If you omit flags it defaults to live run:
```
python etl_streaming_titles.py
```
Progress messages will show each CSV being processed. The script uses caching to reduce duplicate inserts and respects uniqueness constraints.

### Step 10: Verify Data Loaded
In MySQL:
```
USE streaming_media_db;
SELECT COUNT(*) FROM title;
SELECT COUNT(*) FROM movie;
SELECT COUNT(*) FROM tv_show;
SELECT COUNT(*) FROM genre;
SELECT COUNT(*) FROM streaming_availability;
```
You can also inspect a few joined rows:
```
SELECT t.global_title_name, t.release_year, sa.platform_show_id, ss.service_name
FROM streaming_availability sa
JOIN title t ON sa.title_id = t.title_id
JOIN streaming_service ss ON sa.streaming_service_id = ss.streaming_service_id
LIMIT 10;
```

### Step 10: Re-Runs & Idempotency
- The script uses `INSERT IGNORE` and natural unique keys to avoid duplicating previously loaded rows.
- If you add new CSV rows later, re-run the live ETL; only truly new titles/persons/etc. should be inserted.
- To completely refresh, you can re-run the DDL (dropping tables) and then do the live run again.

## 4. Troubleshooting
| Issue | Possible Fix |
|-------|--------------|
| `mysql.connector.errors.ProgrammingError: 1049 (Unknown database)` | Database name mismatch: confirm `DB_NAME` in `.env` matches created DB. |
| Authentication error | Re-check username/password; if using root, ensure you entered the correct root password. |
| CSV file not found | Make sure you run the script from the project root or use the relative paths exactly as provided. |
| Missing tables in test connection | Re-run Step 2; ensure the DDL executed without errors. |
| Character encoding problems | Ensure MySQL tables use `utf8mb4` (already set by DDL). |

## 5. Useful Command-Line Shortcuts
Show current users & their grants:
```
SELECT user, host FROM mysql.user;
SHOW GRANTS FOR 'movie_tv_app'@'localhost';
```
View a sample of inserted titles by recent release year:
```
SELECT global_title_name, release_year
FROM title
ORDER BY release_year DESC
LIMIT 20;
```

## 6. Updating Environment Variables
If your password or user changes, update `.env` and re-run `--test-connection`. No need to reload existing data unless you dropped tables.

## 7. Next Ideas (Optional Enhancements)
- Add a `requirements.txt` and pin versions (e.g., pandas, mysql-connector-python).
- Extend ETL with basic data quality reports (counts per rating, per genre).
- Add logging to a file instead of only printing to console.
- Build a lightweight dashboard (e.g., Streamlit) querying the populated tables.

---
Questions or improvements? Create an issue or comment so the team can iterate. Happy data exploring!
