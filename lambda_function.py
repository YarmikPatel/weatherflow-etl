
import csv
import io
import json
import logging
import os
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def transform_record(row):
    """Clean and validate one weather record."""

    record_id = (row.get("record_id") or "").strip()
    city = (row.get("city") or "").strip().title()
    observation_time = (row.get("observation_time") or "").strip()

    if not record_id or not city or not observation_time:
        raise ValueError("Missing required field")

    # Validate the observation timestamp.
    datetime.fromisoformat(observation_time)

    # Convert numeric values.
    temperature_c = float(row["temperature_c"])
    humidity = int(row["humidity_percent"])

    # Validate weather measurements.
    if not -90 <= temperature_c <= 60:
        raise ValueError("Invalid temperature")

    if not 0 <= humidity <= 100:
        raise ValueError("Invalid humidity")

    # Derived field: Celsius to Fahrenheit.
    temperature_f = (temperature_c * 9 / 5) + 32

    return {
        "record_id": record_id,
        "city": city,
        "observation_time": observation_time,
        "temperature_c": Decimal(str(temperature_c)),
        "temperature_fahrenheit": Decimal(
            str(round(temperature_f, 2))
        ),
        "humidity_percent": humidity,
    }


def process_csv(csv_text):
    """Transform CSV records and return audit counts."""

    clean_records = []
    rejected_records = 0

    reader = csv.DictReader(io.StringIO(csv_text))

    for row in reader:
        try:
            clean_records.append(transform_record(row))
        except (ValueError, TypeError, KeyError) as error:
            rejected_records += 1
            logger.warning(
                "Rejected record %s: %s",
                row.get("record_id"),
                error,
            )

    return clean_records, rejected_records


def lambda_handler(event, context):
    """Read CSV from S3 and load clean records into DynamoDB."""

    import boto3

    s3 = boto3.client("s3")
    dynamodb = boto3.resource("dynamodb")

    table_name = os.environ["DYNAMODB_TABLE"]
    table = dynamodb.Table(table_name)

    total_input = 0
    inserted_records = 0
    rejected_records = 0

    for item in event["Records"]:
        bucket = item["s3"]["bucket"]["name"]
        key = item["s3"]["object"]["key"]

        if not key.startswith("raw/") or not key.endswith(".csv"):
            logger.info("Skipping file: %s", key)
            continue

        response = s3.get_object(Bucket=bucket, Key=key)
        csv_text = response["Body"].read().decode("utf-8-sig")

        clean_records, rejected = process_csv(csv_text)

        # Count data rows, excluding the CSV header.
        total_input += len(clean_records) + rejected
        rejected_records += rejected

        with table.batch_writer() as batch:
            for record in clean_records:
                batch.put_item(Item=record)
                inserted_records += 1

    audit = {
        "total_input_records": total_input,
        "inserted_records": inserted_records,
        "rejected_records": rejected_records,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    logger.info("ETL_AUDIT %s", json.dumps(audit))
    return audit
