# Quick Database Deployment Guide

This guide shows how to quickly restore the database using the pre-populated SQL dump file.

## Using the SQL Dump (Fastest Method)

The `streaming_media_db_dump.sql` file contains both the database schema and all the data, allowing for instant deployment without running the ETL process.

### Prerequisites
- MySQL Server installed and running
- MySQL command-line client or MySQL Workbench

### Method 1: Using MySQL Command Line

```bash
# Restore the database
mysql -u root -p < streaming_media_db_dump.sql
```

Or if your MySQL is in a custom location:
```bash
/usr/local/mysql/bin/mysql -u root -p < streaming_media_db_dump.sql
```

**Note:** You'll be prompted for your MySQL root password.

### Method 2: Using MySQL Workbench

1. Open MySQL Workbench
2. Connect to your MySQL server
3. Go to **Server** → **Data Import**
4. Select **Import from Self-Contained File**
5. Browse and select `streaming_media_db_dump.sql`
6. Under **Default Target Schema**, select **New** and name it `streaming_media_db`
7. Click **Start Import**

### Method 3: Using MySQL Command Line (Step by Step)

```bash
# Connect to MySQL
mysql -u root -p

# In MySQL prompt, create and use the database
CREATE DATABASE IF NOT EXISTS streaming_media_db;
USE streaming_media_db;

# Exit MySQL
exit;

# Import the dump
mysql -u root -p streaming_media_db < streaming_media_db_dump.sql
```

### Verification

After importing, verify the data was loaded:

```sql
USE streaming_media_db;
SELECT COUNT(*) FROM title;
SELECT COUNT(*) FROM movie;
SELECT COUNT(*) FROM tv_show;
SELECT COUNT(*) FROM streaming_availability;
```

Expected counts:
- Titles: ~22,558
- Movies: ~16,142
- TV Shows: ~6,426
- Streaming Availability Records: ~22,981

## When to Use This Method

✅ **Use the dump file when:**
- Setting up the database on a new machine
- Need to quickly restore after dropping tables
- Want to skip the ETL process (saves ~5-10 minutes)
- Deploying to production/staging environments

❌ **Use the ETL process when:**
- You've updated the CSV files and need fresh data
- You want to modify the ETL logic
- You need to test the ETL pipeline

## Updating the Dump File

If you make changes to the database and want to create a new dump:

```bash
mysqldump -u root -p --single-transaction --routines --triggers streaming_media_db > streaming_media_db_dump.sql
```

**Note:** The dump file is large (~13MB) and contains all data. Consider adding it to `.gitignore` if you're using version control, or use Git LFS for large files.

