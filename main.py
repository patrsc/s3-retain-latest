import boto3
import datetime
import os
import logging


def main():
    t_start = datetime.datetime.now(datetime.timezone.utc)
    bucket = os.environ['S3_BUCKET']
    factor = float(os.environ['S3_RETAIN_FACTOR']) if 'S3_RETAIN_FACTOR' in os.environ else 0.5
    options = dict(
        endpoint_url=os.environ['S3_ENDPOINT'],
        aws_access_key_id=os.environ['S3_ACCESS_KEY'],
        aws_secret_access_key=os.environ['S3_ACCESS_SECRET'],
        aws_session_token=None,
        config=boto3.session.Config(signature_version='s3v4')
    )
    client = boto3.client('s3', **options)
    n_updated = 0
    n_total = 0

    now = datetime.datetime.now(datetime.timezone.utc)
    mode, retain_period = get_default_retention(client, bucket)
    t_threshold = now + factor * retain_period
    t_retain_until = now + retain_period

    objects = list_all_objects(client, bucket)
    for key in objects:
        obj = client.get_object_retention(Bucket=bucket, Key=key)
        t = obj['Retention']['RetainUntilDate']
        is_expired = t < t_threshold
        if is_expired:
            client.put_object_retention(
                Bucket=bucket,
                Key=key,
                Retention={
                    'Mode': mode,
                    'RetainUntilDate': t_retain_until
                }
            )
            t_new = client.get_object_retention(
                Bucket=bucket,Key=key)['Retention']['RetainUntilDate']
            if t_new != t_retain_until:
                raise ValueError(f'setting updated time failed for key {key}')
            n_updated += 1
        n_total += 1
    
    task_duration = datetime.datetime.now(datetime.timezone.utc) - t_start

    return n_updated, n_total, task_duration


def list_all_objects(client, bucket):
    max_keys = 1000
    is_truncated = True
    next_token = None
    while is_truncated:
        opts = dict(
            Bucket=bucket, MaxKeys=max_keys,
        )
        if next_token is not None:
            opts['ContinuationToken'] = next_token
        res = client.list_objects_v2(**opts)
        is_truncated = res['IsTruncated']
        next_token = res['NextContinuationToken'] if is_truncated else None
        for item in res['Contents']:
            key = item['Key']
            yield key


def get_default_retention(client, bucket):
    res = client.get_object_lock_configuration(Bucket=bucket)
    config = res['ObjectLockConfiguration']['Rule']['DefaultRetention']
    mode = config['Mode']
    days = config['Years'] * 365 if 'Years' in config else config['Days']
    period = datetime.timedelta(days=days)
    return mode, period


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
    try:
        n_updated, n_total, task_duration = main()
        logging.info(f's3-retain finished successfully and updated ' +
                     '{n_updated} out of {n_total} objects in {task_duration.total_seconds():.01f} seconds')
    except Exception as e:
        logging.error(f's3-retain failed with error: {type(e).__name__}: {e}')
