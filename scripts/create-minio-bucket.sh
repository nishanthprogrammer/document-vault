#!/bin/sh
set -e

echo "Waiting for MinIO..."
until mc alias set local http://minio:9000 "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}"; do
  echo "MinIO not ready, retrying in 2s..."
  sleep 2
done

echo "Creating bucket '${S3_BUCKET}' if it does not exist..."
mc mb --ignore-existing "local/${S3_BUCKET}"

echo "Bucket '${S3_BUCKET}' is ready."
