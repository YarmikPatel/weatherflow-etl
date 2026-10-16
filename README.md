
# WeatherFlow ETL

## Project Overview
WeatherFlow ETL is a beginner-friendly serverless data engineering project that cleans weather readings and prepares them for analytics.

## Dataset
The current sample dataset contains weather readings for Indian cities. It is stored in `sample_data/sample_raw_data.csv`.

## Architecture
CSV file -> Amazon S3 (raw/) -> AWS Lambda -> Amazon DynamoDB (clean_records) -> Amazon CloudWatch logs

CI/CD:
GitHub -> GitHub Actions
GitHub -> AWS CodePipeline -> AWS CodeBuild

## AWS Services
- Amazon S3: stores the raw CSV file.
- AWS Lambda: validates and transforms weather records.
- Amazon DynamoDB: stores cleaned records.
- AWS IAM: controls permissions.
- Amazon CloudWatch: stores execution logs.
- AWS CodePipeline and CodeBuild: validate the project build.

## ETL Rules
1. Reject records with missing required fields.
2. Standardize city names using title case.
3. Validate observation timestamps.
4. Reject temperatures outside the configured range.
5. Reject humidity outside 0-100%.
6. Calculate temperature in Fahrenheit.
7. Log input, inserted, and rejected record counts.

## DynamoDB Design
Table: `clean_records`

Partition key: `record_id` (String)

Each valid record has a unique record ID.

## Local Testing
Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Validate syntax:

```bash
python -m py_compile lambda_function.py
```

Test the sample data:

```bash
python -c "from lambda_function import process_csv; f=open('sample_data/sample_raw_data.csv', encoding='utf-8-sig'); records,rejected=process_csv(f.read()); assert len(records)==3 and rejected==3; print('ETL test passed')"
```

## GitHub Actions
The workflow in `.github/workflows/ci.yml` checks Python syntax and validates the sample ETL transformation on pushes and pull requests.

## AWS CodePipeline
The planned pipeline uses GitHub as its source and AWS CodeBuild to validate the Python project. Successful execution will be documented after the pipeline is configured and tested.

## Current Status
Local ETL transformation and Python syntax checks have passed. AWS deployment and integration tests are pending.
