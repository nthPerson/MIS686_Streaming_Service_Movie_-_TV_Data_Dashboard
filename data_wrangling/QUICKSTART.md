# QUICK START: Loading Streaming Catalog Data

This guide shows you how to use `etl_streaming_titles.py` to put the CSV catalog data from our 4 datasets into your local (or later, hosted) MySQL database.

---
## 1. What You Need First
1. A running MySQL Server on your machine (default: host `localhost`, port `3306`).
2. Python 3.9+ installed.
3. The CSV files placed in the `raw_data/` folder:
   - `amazon_prime_titles.csv`
   - `disney_plus_titles.csv`
   - `hulu_titles.csv`
   - `netflix_titles.csv`
4. The database tables created. Run the code in the `documents/tv_movie_DDL.sql` file inside MySQL Workbench before running the ETL script.

---
## 2. Create the Database and Tables (One-Time)
Open a MySQL client (Workbench, command line, etc.) and run:
```sql
SOURCE /full/path/to/documents/tv_movie_DDL.sql;
```
This creates the `streaming_media_db` database and all required tables.

---
## 3. Set Up Python Environment (Required)
From a terminal in the project root folder:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install mysql-connector-python pandas
```

---
## 4. Check the Database Connection
Run the script with the connection test option:
```bash
# from the root directory
python data_wrangling/etl_streaming_titles.py --test-connection

# or from the data_wrangling directory
python etl_streaming_titles.py --test-connection
```
Expected result: It prints the list of required tables. If it says "All required tables present." you are good to go.

If you see an error like "Access denied" or missing tables:
- Verify the username/password in the script (`DB_CONFIG` near the top).
- Make sure you ran the DDL file.

---
## 5. Dry Run (Practice Mode) 
This shows what would be inserted WITHOUT changing the database.
```bash
cd data_wrangling
python etl_streaming_titles.py --dry-run --sample-size 5
```
What you will see:
- Each CSV file is read.
- Warnings if a file is missing.
- A summary for each target table: how many rows would be inserted + a small sample.

If you see warnings about files not found:
- Confirm the filenames and that they are in the `raw_data/` folder.

---
## 6. Live Run (Real Insert) 
When you are ready to load the data:
```bash
cd data_wrangling  # make sure you're in the data_wrangling directory
python etl_streaming_titles.py --live-run
```
If you omit all flags, the script also defaults to a live run.

What happens:
- Each CSV is processed.
- Data is inserted into the appropriate tables.
- It commits after each file.

You can re-run safely; duplicates are ignored due to `INSERT IGNORE` and unique constraints.

---
## 7. After Loading
You can explore the data, for example:
```sql
USE streaming_media_db;
SELECT COUNT(*) FROM title;
SELECT service_name, COUNT(*) AS titles
FROM streaming_service s
JOIN streaming_availability a ON a.streaming_service_id = s.streaming_service_id
GROUP BY service_name;
```

---
## 8. Common Problems & Fixes
| Problem | Cause | Fix |
|---------|-------|-----|
| File not found warning | CSV not in `raw_data/` or name mismatch | Check folder & spelling |
| Access denied (MySQL) | Wrong user/password or MySQL not running | Update `DB_CONFIG` or start MySQL |
| Missing tables | DDL not executed | Run `tv_movie_DDL.sql` again |
| Empty dry run summary | CSV files empty or unreadable | Open CSV to confirm content |

---
## 9. Changing Configuration
Edit the `DB_CONFIG` dict near the top of `etl_streaming_titles.py` if your host, port, user, password, or database name are different.

Edit `CSV_FILES` list if your CSV file names or locations differ.

---
## 10. Quick Reference
| Action | Command |
|--------|---------|
| Test connection | `python data_wrangling/etl_streaming_titles.py --test-connection` |
| Dry run (sample 3) | `python data_wrangling/etl_streaming_titles.py --dry-run --sample-size 3` |
| Live run | `python data_wrangling/etl_streaming_titles.py --live-run` |

---
## 11. Need Help?
If something is unclear, share the exact command you ran and the message you saw so others can assist quickly.

---
Happy data loading!
