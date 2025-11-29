# Proposed Project Objective

The objective of this project is to develop a cloud-based analytical dashboard that integrates movie and TV show catalogs from multiple major streaming services—including Netflix, Amazon Prime Video, Hulu, and Disney+—into a unified, normalized database. The dashboard will enable users to explore the combined catalog or filter by specific streaming service, providing the ability to compare platforms and analyze content patterns across dimensions such as genre, country of origin, release year, content type (movie vs. TV show), and overall catalog composition.

A central goal of the application is to answer at least eight analytical questions using SQL queries executed on an AWS-hosted relational database, with results presented through visualizations and interactive components in a Python-based dashboard. These analytical questions will support business-oriented insights such as comparing catalog size across platforms, identifying genre coverage and concentration patterns, evaluating geographic diversity, and examining temporal trends in content releases and platform additions. Through these descriptive and comparative analyses, the dashboard will summarize the landscape of available streaming content and highlight meaningful trends across services.

The system is also designed with flexibility for future (or current) enhancements, including possible **recommendation features (aka a recommendation model)**, expanded filtering tools, or additional analytics modules, ensuring that the project can adapt to team preferences while demonstrating the full end-to-end database development process required by the course.

# Tech Stack

The following technology stack is proposed for implementing the streaming analytics dashboard and supporting the full end-to-end database development workflow required for the MIS 686 term project. This stack emphasizes clarity, maintainability, compatibility with course expectations, and ease of group collaboration.

## **1. Database Layer — AWS Cloud Database (MySQL/PostgreSQL)**

**Platform:**

- **AWS RDS (Amazon Relational Database Service)**
- **Database Engine:** *MySQL or PostgreSQL (Free Tier-compatible)*

**Rationale:**

- RDS provides a managed relational database environment suitable for implementing the project’s ERD, relational schema, constraints, views, triggers, stored procedures, and user roles.
- Both MySQL and PostgreSQL fully satisfy the assignment requirements and support standard SQL as well as advanced features.
- The cloud-hosted DB ensures group members can access the same instance remotely and provides a realistic enterprise-grade environment.

**Responsibilities:**

- Host normalized tables for Titles, Streaming Services, Genres, Countries, Persons, and linking tables.
- Support analytical SQL queries, indexes, triggers, and stored procedures.
- Serve as the backend for dashboard queries executed from the Python application.

---

## **2. Data Processing Layer — Python + Pandas**

**Technologies:**

- **Python 3.11+**
- **Pandas** (data loading, cleaning, preprocessing)
- **mysql-connector-python / psycopg2** (for DB connectivity)
- **python-dotenv** (secure credential handling)

**Rationale:**

- **mysql-connector-python** connectors provide stable, secure DB ingestion pipelines.

**Responsibilities:**

- Read and write data to and from the existing database (see /documents/DATABASE_SCHEMA.md in existing codebase)

---

## **3. Application & Dashboard Layer — Streamlit (Python)**

**Framework:**

- **Streamlit**, a modern Python framework for building interactive data applications.

**Rationale:**

- Streamlit requires minimal boilerplate and integrates directly with Pandas, Matplotlib, and Plotly, making it ideal for analytical dashboards.
- Low friction for group collaboration—no need to manage HTML templates or advanced routing.
- Supports rapid prototyping of interactive filtering, visualizations, and user-driven analytics.

**Responsibilities:**

- Provide interactive UI components such as dropdowns, multiselect filters, sliders, and text search.
- Connect to the AWS database and execute SQL queries to populate tables, charts, metrics, and insights.
- Display visualizations (Matplotlib, Plotly) answering the required analytical questions.
- Implement user-selected input flows for optional recommendation features (e.g., user picks favorite titles → similarity-based suggestions).

---

## **4. Visualization & Analytics Layer — Python Libraries**

**Libraries:**

- **Pandas** — tabular analytics, SQL result handling
- **Matplotlib** — core visualizations (satisfying assignment requirements)
- **Plotly Express** — interactive charts (hover, zoom, filtering)
- **NumPy** — numerical computation support
- **scikit-learn** (optional) — for recommendation or clustering models

**Rationale:**

These libraries support both required descriptive analysis and optional modeling components (e.g., text similarity, genre clustering). They integrate seamlessly with Streamlit and AWS via Python.

**Responsibilities:**

- Produce visualizations directly answering the eight required analytical questions.
- Implement optional ML-based insights such as content similarity, genre prediction, or clustering of titles.
- Provide user-friendly displays within the dashboard (charts, metrics, tables).

---

## **5. Deployment & Access**

**Database Deployment:**

- **AWS RDS (MySQL)** — remote group access, stable hosting
- Security groups configured for team access (restricted IPs)

**Application Deployment (options):**

- **Local Streamlit execution** (default and simplest)
- **Streamlit Community Cloud** (optional stretch goal)

**Code Repository:**

- **GitHub** for version control and collaboration
- Includes all Python scripts, `requirements.txt`, ERD diagrams, SQL files, and documentation

# Data Model

See /documents/DATABASE_SCHEMA.md for details on data model for existing database.

# Analytical Questions Answered by Dashboard

### **1. Platform Comparison**

1. How many titles does each streaming service offer?
2. How does the movie/TV show ratio differ across platforms?

### **2. Genre & Content Mix**

1. What are the most common genres overall and by service?
2. Which genres are most unique or exclusive to individual platforms?

### **3. Geographic Trends**

1. How many countries are represented per service?
2. Which countries contribute the most titles across all platforms?

### **4. Temporal Trends**

1. How does the distribution of titles by release year differ across services?
2. What are the trends in content addition (based on `date_added`) per service?

### **5. (Optional Enhancement; will be implemented at a later time) Recommendation Support**

1. For a chosen title, what similar titles exist across the combined catalog?

# User Interface Components

The UI will support exploration of the combined streaming catalog and provide visual and tabular answers to the selected analytical questions regarding platform comparison, genre and country distributions, and temporal trends. An optional enhancement will provide a simple similarity-based recommendation for a chosen title.

## 1. Overall Layout & Navigation

**UI-1: Layout**

- The dashboard will use a **left sidebar** for global filters and user input controls.
- The **main content area** will be organized into sections reflecting the main analytical themes:
    - **Overview & Summary**
    - **Platform Comparison**
    - **Genres & Countries**
    - **Temporal Trends**
    - **Optional: Similar Titles / Recommendations**

**UI-2: Navigation**

- Sections may be implemented as **tabs** or clearly separated subsections with headings so that each area maps cleanly onto the analytical questions in Option Set E.

---

## 2. Global Filters & Controls (Sidebar)

Global filters will allow users to restrict the analysis to specific subsets of the catalog, and these filters will apply consistently across views.

**UI-3: Streaming Service Filter**

- **Component:** Multi-select dropdown
- **Function:** Allow users to choose one or more services (Netflix, Prime, Hulu, Disney+).
- **Relevant Questions:**
    - Q1: Titles per service
    - Q2: Movie/TV ratio per platform
    - Q3–Q6: Genre and country distributions per service
    - Q7–Q8: Temporal trends by service

**UI-4: Content Type Filter (Movie vs TV Show)**

- **Component:** Radio buttons or multi-select (Movies, TV Shows, Both)
- **Function:** Filter all analyses by content type.
- **Relevant Questions:**
    - Q2 (movie/TV show ratio)
    - All charts where type matters.

**UI-5: Genre Filter**

- **Component:** Multi-select dropdown
- **Function:** Focus analyses on one or more genres (e.g., “Drama”, “Comedy”).
- **Relevant Questions:**
    - Q3–Q4 (genre distributions and uniqueness)
    - Optional similarity view (Q9).

**UI-6: Country Filter**

- **Component:** Multi-select dropdown
- **Function:** Filter titles by country of origin.
- **Relevant Questions:**
    - Q5–Q6 (countries represented, top contributing countries).

**UI-7: Release Year / Time Range Filter**

- **Component:** Range slider (min–max release year)
- **Function:** Restrict analyses to titles released within a specific time window.
- **Relevant Questions:**
    - Q7 (distribution of titles by release year and service).

**UI-8: Date Added Range Filter (if available)**

- **Component:** Date range picker or year/month slider (aggregated)
- **Function:** Focus temporal analyses of catalog additions on a selected period.
- **Relevant Questions:**
    - Q8 (trends in content addition over time).

**UI-9: Title Search / Selection (for Optional Similarity Question)**

- **Component:** Searchable dropdown or text + dropdown combination
- **Function:** Let the user select a specific title from the filtered catalog for the “similar titles” question.
- **Relevant Questions:**
    - Q9 (optional enhancement: similar titles across catalog).

---

## 3. Main Content Views / Panels

### 3.1 Overview & Summary

**UI-10: Key Metrics / KPIs**

- **Components:** Metric cards / text blocks (e.g., `st.metric`)
- **Metrics:**
    - Total number of titles in the current filter set
    - Titles per selected service (topline counts)
    - Number of distinct genres and countries in the filtered data
- **Mapped Questions:**
    - Q1 (titles per service) – at least in summarized form.

**UI-11: Catalog Composition Chart**

- **Component:** Grouped or stacked bar chart (Matplotlib or Plotly)
- **Example:** Titles per service with bars differentiated by content type (movies vs TV shows).
- **Mapped Questions:**
    - Q1 (titles per service)
    - Q2 (movie vs TV show ratio across platforms).

---

### 3.2 Platform Comparison View

**UI-12: Titles per Service Chart**

- **Component:** Simple bar chart (x-axis: service, y-axis: number of titles).
- **Function:** Directly answer “How many titles does each streaming service offer?”
- **Mapped Questions:**
    - Q1.

**UI-13: Movie vs TV Show Ratio Chart**

- **Component:** Stacked bar or grouped bar chart by service (movies vs TV shows).
- **Mapped Questions:**
    - Q2: How does the movie/TV ratio differ across platforms?

**UI-14: Service Comparison Table**

- **Component:** Interactive data table (sortable)
- **Columns:** Service, total titles, # movies, # TV shows, movie %, TV %
- **Mapped Questions:**
    - Q1, Q2 (shows numeric detail behind charts).

---

### 3.3 Genres & Countries View

**UI-15: Genre Distribution by Service**

- **Component:**
    - Option A: Stacked bar chart of genre counts per service.
    - Option B: Faceted bar charts per service (if using Plotly).
- **Function:** Show which genres are most common overall and for each platform.
- **Mapped Questions:**
    - Q3: Most common genres overall and by service.

**UI-16: Exclusive / Unique Genres Indicator**

- **Component:**
    - Bar or table highlighting genres that appear predominantly on a single service (e.g., high percentage of titles in that genre on one platform vs others).
- **Function:** Identify “near-exclusive” or strongly associated genres for each service.
- **Mapped Questions:**
    - Q4: Which genres are most unique/exclusive to individual platforms?

**UI-17: Country Representation Chart**

- **Component:** Bar chart (x-axis: country, y-axis: number of titles; optionally top N countries).
- **Function:** Show which countries contribute the most titles overall and by filter.
- **Mapped Questions:**
    - Q5: How many countries are represented per service?
    - Q6: Which countries contribute the most titles?

**UI-18: Country-by-Service Table**

- **Component:** Table or pivot-style summary.
- **Columns:** Country, total titles, titles per service (Netflix/Prime/Hulu/Disney+).
- **Mapped Questions:**
    - Q5–Q6 (numeric, detailed breakdown).

---

### 3.4 Temporal Trends View

**UI-19: Release Year Distribution**

- **Component:** Histogram or line chart (x-axis: release year, y-axis: count of titles), optionally colored by service.
- **Function:** Show how the distribution of titles by release year differs across services.
- **Mapped Questions:**
    - Q7: Differences in release year distribution by platform.

**UI-20: Titles Added Over Time (Date Added)**

- **Component:** Line or area chart, aggregated by month/year of `date_added` per service.
- **Function:** Show trends in content additions over time for each platform.
- **Mapped Questions:**
    - Q8: Trends in content addition based on `date_added`.

---

### 3.5 Optional: Similar Titles / Recommendations View (Enhancement for Q9)

**UI-21: Title Selection for Similarity**

- **Component:** Searchable dropdown (see UI-9).
- **Function:** Let users pick a single title as the “anchor” for similarity.

**UI-22: Similar Titles Results Table**

- **Component:** Table showing a ranked list of similar titles.
- **Columns:** Title, service(s), genres, release year, similarity score (optional), country.
- **Mapped Questions:**
    - Q9: For a chosen title, what similar titles exist across the combined catalog?

**UI-23: Similar Titles Summary Chart (Optional)**

- **Component:** Bar chart showing counts of similar titles by service or genre.
- **Function:** Provide a quick visual snapshot of where similar content is concentrated.

---

## 4. Data Table & Detail View

**UI-24: Filtered Titles Table**

- **Component:** Scrollable, sortable data table.
- **Columns:** Title, service(s), type, primary genre(s), country, release year, date added, description (truncated).
- **Function:** Allow users to directly inspect the underlying titles that feed the charts.

**UI-25: Title Detail Panel**

- **Component:** Expandable row, popup, or detail section when a title is selected.
- **Fields:** Full title, list of services, genres, countries, full description, cast/director info (if modeled).
- **Function:** Support exploratory analysis and help users understand specific data points behind the aggregate analytics.

---

## 5. Explanatory & Non-Interactive Elements

**UI-26: Section Descriptions**

- **Component:** Short explanatory text at the top of each section (Markdown headers).
- **Function:** Explain which analytical questions each view is addressing (e.g., “This section addresses Questions 1 and 2 by comparing catalog size and movie/TV ratios across platforms.”).

**UI-27: Chart Labels, Legends, and Tooltips**

- **Requirement:** All charts must include clear axis labels, legends for colors (e.g., services, content types), and, where applicable, hover tooltips (for Plotly charts) to show exact values.
- **Function:** Ensure interpretability of all visual outputs.