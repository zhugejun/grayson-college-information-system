# Grayson College Schedule Synchronization System

An automated data pipeline for ingesting, transforming, normalizing, and reconciling schedule data between two heterogeneous systems.

This project demonstrates how to design and implement a reliable data ingestion and reconciliation workflow to keep data consistent across operational platforms with different schemas and update mechanisms.

---

## 🔍 Problem

The college maintained course schedules in two separate systems: 

* **CAMS** — the authoritative student information system (instructors and directors are not allowed to make schedule changes directly).
* **Scheduling App** — a web application used by instructors and directors to propose and manage schedule changes.

**Additional Challenges:**  
* Instructors and directors submitted schedule changes in multiple unstructured formats—plain text emails, Word documents, and PDFs—making manual data entry tedious, error-prone, and time-consuming. 
* CAMS data needed to be extracted, transformed, and loaded into the app to enable comparison—requiring a separate ETL pipeline. 

These systems: 
* Used different data formats and schemas. 
* Were updated independently by different users.
* Frequently drifted out of sync, causing inconsistencies and operational confusion. 

---

## 🎯 Solution

This system implements an automated **ETL + reconciliation pipeline** that: 

1. Extracts schedule data from CAMS and transforms it into a normalized format. 
2. Loads the normalized data into the app's database for comparison. 
3. Captures schedule change requests submitted by instructors and directors.
4. Compares the two datasets to detect differences and conflicts.
5. Stores reconciliation results and change history for audit and review. 
6. Supports human-in-the-loop correction when conflicts are detected.

---

## 🔄 How It Works

### Data Flow

1. **Extract, Transform, Load (ETL)**  
   - The [gcis-data](https://github.com/zhugejun/gcis-data) pipeline extracts raw schedule data from CAMS
   - Transforms it into a normalized format
   - Loads it into the app's **CAMS Schedule Database**

2. **User Input**  
   - Instructors and directors submit schedule changes through the web application
   - Changes are stored in a separate **Proposed Changes Database**

3. **Reconciliation**  
   - The app compares both databases to detect differences
   - Highlights additions, modifications, and deletions
   - Provides an interface for administrators to review and approve changes

### Two-Database Architecture

| Database | Purpose | Updated By |
|----------|---------|------------|
| **CAMS Schedule DB** | Source of truth from the student system | `gcis-data` ETL pipeline (periodic sync) |
| **Proposed Changes DB** | Instructor/director-submitted updates | Web app users |

**The app's core function:** Compare these two databases and surface the differences for review. 

---

## 🧱 Architecture

```
        +-------------------+
        |       CAMS        |
        | (Student System)  |
        +---------+---------+
                  |
                  | Extract raw data
                  v
        +-------------------+
        |    gcis-data      |
        |   ETL Pipeline    |
        | (Transform/Load)  |
        +---------+---------+
                  |
                  | Load normalized data
                  v
   +---------------------------+       +---------------------------+
   |   CAMS Schedule DB        |       |  Proposed Changes DB      |
   |  (Source of Truth)        |       |  (User Submissions)       |
   +-------------+-------------+       +-------------+-------------+
                 |                                   |
                 +----------------+------------------+
                                  |
                                  v
                       +--------------------+
                       | Comparison Engine  |
                       | (Diff Detection)   |
                       +---------+----------+
                                 |
                                 v
                       +--------------------+
                       | Reconciliation UI  |
                       | (Review & Approve) |
                       +--------------------+
```

---

## ⚙️ Key Components

* **[gcis-data ETL Pipeline](https://github.com/zhugejun/gcis-data)**  
  - Extracts raw schedule data from CAMS
  - Transforms it into a normalized, app-compatible format
  - Loads data into the CAMS Schedule Database on a periodic schedule

* **CAMS Schedule Database**  
  - Stores the authoritative schedule from the student information system
  - Updated automatically via the ETL pipeline

* **Proposed Changes Database**  
  - Stores schedule change requests submitted by instructors and directors
  - Captures changes that cannot be made directly in CAMS

* **Comparison & Reconciliation Engine**  
  - Detects additions, deletions, and modifications between both databases
  - Flags conflicts for administrative review

* **Web Interface**  
  - Allows instructors/directors to submit schedule changes
  - Provides administrators with a dashboard to review diffs and approve updates

---

## 🧪 Features

* Schema normalization across heterogeneous sources
* Change detection and diff generation
* Conflict identification
* Historical tracking of schedule changes
* Human-in-the-loop resolution

---

## 🛠 Tech Stack

* Python
* Django
* PostgreSQL (or equivalent relational DB)
* Heroku (deployment)
* GitHub (version control)

---

## 🎓 Skills Demonstrated

* **ETL Pipeline Design** — extracting, transforming, and loading data from heterogeneous sources
* **Schema Mapping & Normalization** — reconciling differences between system data models
* **Data Quality & Validation** — implementing business rules and conflict detection
* **Change Data Capture (CDC)** — tracking modifications and maintaining history
* **Operational Data Management** — ensuring consistency across live production systems

---

## 🚀 Future Improvements

* Add orchestration (Airflow/Dagster) for scheduling and retries
* Add automated data quality checks
* Add monitoring and metrics
* Containerize the pipeline
* Migrate to cloud-native storage

---

## 🧠 Lessons Learned

* Operational data rarely agrees across systems. 
* Schema mismatches are a primary source of errors.
* Reconciliation pipelines need both automation and human oversight.
* Reliability and observability are as important as correctness.

---

## 📌 What This Project Demonstrates

* Designing ETL pipelines for operational data
* Schema mapping and normalization
* Building reconciliation and validation logic
* Managing data consistency across systems
* Thinking about data reliability and auditability
