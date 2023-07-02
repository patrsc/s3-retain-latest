# s3-retain-latest

Automated script to retain the latest version of all objects in an [S3](https://en.wikipedia.org/wiki/Amazon_S3) bucket by regularly updating object lock times.

## Background

S3 object locking sets the expiration time of object retention at the **creation** of a new object version. This means that if the latest version of an object is not updated for a time longer than the retention period, it is not locked any more.

*Example:* A BLOB is created and never updated for 1.5 years and the retention period is set to 1 year. After slightly more that 1 year this blob could be deleted immediately, although it is the latest version.

## What this script does

To prevent this scenario, this script keeps the retention time of the latest version of every object updated. This script should be run regularly (e.g. every day) using an automatic background job (e.g. cron).

What this script does:
* get the default retention period of the given bucket (e.g. 90 days)
* iterate over all (current) objects in the bucket
  * if the latest version of the object has a retention time less than now + half of the default retention period (e.g. 45 days), then
    * set its retention time to now + the default retention period (e.g. 90 days)

Older or deleted object versions are not affected by this script. So, assuming this script is run frequently:
If an object is deleted or overwritten the previous version is retained for (at least half of) the default retention period **after deletion/overwriting** instead of after initial creation.

The factor (by default half = 0.5) is controlled by the variable `S3_RETAIN_FACTOR`, so updating is triggered by the rule
```
current_retention_time < now + factor * default_retain_period
```

## Usage

Prerequisites: [Git](https://git-scm.com) and [Docker](https://www.docker.com/) are installed.

Clone the repository:

```
cd ~
git clone <url>
cd s3-retain-latest
```

Let us create the configuration for an example bucket (you can change the name `example`):

```
BUCKET=example
```

Create a config file `$BUCKET.env`:

```
nano $BUCKET.env
```

and add the following content (adjust it according to your needs):

```
S3_ENDPOINT=https://<host>:<port>
S3_ACCESS_KEY=<key>
S3_ACCESS_SECRET=<secret>
S3_BUCKET=<bucekt_name>
S3_RETAIN_FACTOR=0.5
```

Build Docker image:

```
sudo docker build . -t s3-retain
```

Run image to test if it works successfully:

```
sudo docker run --env-file $BUCKET.env s3-retain
```

You can run it also with the script (this will create a log file `$BUCKET.log`):

```
sudo bash run.sh $BUCKET
```

Add a cron job:

```
sudo crontab -e
```

and add the following line to run the task daily (change path and bucket name accordingly):

```
@daily bash /home/user/s3-retain-latest/run.sh example
```
