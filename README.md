
# Data Pipeline Project

## Overview
This project contains three Spark-based data pipeline scripts designed to process, analyze, and store retail sales data sourced from Amazon S3. The scripts utilize PySpark to handle data ingestion, transformation, analysis, and storage. These scripts are:
1. **data_pipeline_sql.py**: SQL-based analysis of the retail sales dataset.
2. **data_pipeline_autopilot.py**: Automated data processing with train-test split.
3. **data_pipeline.py**: Comprehensive data processing and aggregation.

## Prerequisites
Before running the scripts, ensure you have the following set up:

- **Apache Spark** (version 3.3.2 or compatible)
- **Hadoop AWS package** (version 3.3.2 or compatible) 
- **AWS credentials** with access to the S3 bucket containing the retail sales dataset.
- **Python 3.7+** with required libraries (PySpark, AWS SDKs, etc.).

Ensure AWS credentials are properly configured, either via environment variables, configuration files, or IAM roles.

---

## Scripts Breakdown

### 1. **data_pipeline_sql.py**
This script ingests retail sales data from an S3 bucket, transforms it, and performs SQL-based analytical queries on it.

#### Key Features
- **Data Ingestion**: Reads CSV from S3 using PySpark.
- **Data Transformation**: Extracts 'Year' and 'Month' from the 'transaction_date'.
- **SQL Queries**: Executes 5 SQL queries:
  1. **Top-Performing Regions** - Identifies customer locations with the highest revenue.
  2. **Month-over-Month Revenue Growth** - Analyzes revenue growth over time.
  3. **Most Popular Product Categories** - Determines the top 5 most-sold product categories.
  4. **Top 5 Customers** - Identifies top customers by total transaction value.
  5. **Most Used Payment Methods** - Tracks revenue and usage count for different payment methods.

#### Usage
```
spark-submit data_pipeline_sql.py
```

---

### 2. **data_pipeline_autopilot.py**
This script ingests, processes, and splits the retail sales dataset into training and testing datasets for further machine learning applications.

#### Key Features
- **Data Ingestion**: Reads CSV from S3.
- **Data Transformation**: Extracts 'Year', 'Month', and 'Hour' from 'transaction_date'.
- **Data Aggregation**: Computes key metrics for six-hour batch intervals, including revenue, customer demographics, and product category counts.
- **Data Split**: Splits the processed data into **train (75%)** and **test (25%)** datasets.
- **Data Export**: Saves train and test datasets back to S3.

#### Usage
```
spark-submit data_pipeline_autopilot.py
```

---

### 3. **data_pipeline.py**
This script processes and aggregates the retail sales dataset to generate insights on customer locations, spending trends, and customer transaction data.

#### Key Features
- **Data Ingestion**: Reads CSV from S3 using PySpark.
- **Data Transformation**: Extracts 'Year' and 'Month' from 'transaction_date'.
- **Data Aggregation**: Performs the following analysis:
  - **Total Revenue by Customer Location**
  - **Monthly Spending Trends**
  - **Top 10 Customers by Transaction Value**
- **Data Export**: Saves aggregated datasets (Total Revenue, Monthly Spending Trends, Top 10 Customers) back to S3.

#### Usage
```
spark-submit data_pipeline.py
```

---

## Project Structure
```
project-folder/
├── data_pipeline_sql.py           # SQL-based analysis pipeline
├── data_pipeline_autopilot.py     # Auto-processing with train-test split
├── data_pipeline.py               # Comprehensive data processing
└── README.md                      # Project documentation
```

---

## Execution Instructions

1. **Setup Environment**
   - Install Spark and Hadoop libraries.
   - Configure AWS credentials.

2. **Run the Scripts**
   - Run one of the scripts using the following command:
     ```bash
     spark-submit <script_name>.py
     ```

3. **Monitor the Process**
   - View logs in the console to verify successful data ingestion, processing, and storage.

4. **Check S3 Outputs**
   - Verify that processed data is saved to the S3 output directory as CSV files.

---

## Configuration
The following paths can be modified within each script to suit your environment:
- **S3 Input Path**: Location of the raw input file.
- **S3 Output Path**: Destination for processed files.
- **Batch Intervals**: Time intervals used for aggregation.

---

## Error Handling
Each script has an `Exception` handler to catch and print any errors encountered during data ingestion, transformation, or writing to S3.

---

## Contact
For further information or queries regarding the project, please contact the project maintainer.
