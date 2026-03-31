---
name: backend-file-upload-and-media
description: >
  Handle S3 file uploads, presigned URLs, image processing, and media management.
  Use when building or modifying endpoints that deal with file uploads, image URLs,
  thumbnails, cropped images, or S3 operations.
---

# Backend File Upload and Media

## When to use

- Endpoint generates S3 presigned URLs for uploads.
- Endpoint processes uploaded images (cropping, cover photo).
- Endpoint manages image URLs on records.
- Endpoint deletes files from S3.

## When NOT to use

- Endpoint only reads/writes database records -> use [backend-endpoint-crud](.cursor/skills/backend-endpoint-crud/SKILL.md) or [backend-write-operations](.cursor/skills/backend-write-operations/SKILL.md).

## Checklist

1. **Validate the request** (record exists, user has permission).
2. **Generate a unique S3 key** using `uuid.uuid4()`.
3. **Generate presigned URL** with `boto3`.
4. **Return the URL and key** to the client.
5. **After client uploads**, update the record's image field.
6. **Invalidate cache** for the affected record.

## Existing patterns in the codebase

The repo has these upload endpoints:
- `api/cities/__id__/upload-photo/post.py`
- `api/cities/__id__/upload-cropped-image/post.py`
- `api/experiences/__id__/upload-image/post.py`
- `api/experiences/__id__/upload-cropped-image/post.py`
- `api/experiences/__id__/delete-image/put.py`
- `api/experiences/__id__/set-cover/put.py`
- `api/lists/__id__/upload-image/post.py`
- `api/lists/__id__/delete-image/delete.py`
- `api/sections/upload-icon/post.py`
- `api/transportations/__id__/upload-photo/post.py`

## S3 presigned URL generation

```python
import boto3
import uuid

@klug()
def lambda_handler(event, context):
    record_id = event.path("id")
    if not event.validate_uuid(record_id, "id"):
        return event.error_response(400, 'Invalid ID format')

    body = event.body()
    file_type = body.get('file_type', 'image/jpeg')

    s3_client = boto3.client('s3', region_name='eu-west-3')
    bucket = os.environ.get('S3_BUCKET')
    key = f"uploads/{record_id}/{uuid.uuid4()}"

    presigned_url = s3_client.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': bucket,
            'Key': key,
            'ContentType': file_type,
        },
        ExpiresIn=600,
    )

    return {
        'upload_url': presigned_url,
        'key': key,
    }
```

## Thumbnail generation

Use `generate_thumbnail_url()` from `experience_utils.py`:

```python
from experience_utils import generate_thumbnail_url

thumbnail_url = generate_thumbnail_url(image_key, size='200x200', uploads_cdn=cdn_base)
```

This builds a path like `{first_part}_thumbnails/{size}/{rest}`.

## Image URL management

Updating image URLs on a record:
```python
response = event.supabase.table("experiences").update({
    'image_urls': updated_urls
}).eq("id", record_id).execute()
```

## Input validation for uploads

- Validate `file_type` against an allowlist: `['image/jpeg', 'image/png', 'image/webp']`.
- Validate `file_size` if provided (reject files over a reasonable limit).
- Never accept raw file content in the Lambda body for large files.
- Sanitize the S3 key: no user-controlled path components.

## Common mistakes

- Accepting arbitrary file types without validation.
- Using user-provided strings in S3 keys (path traversal risk).
- Forgetting to update the database record after generating the presigned URL.
- Not invalidating cache after updating image fields.
- Setting presigned URL expiry too long (use 300-900 seconds).

## Definition of done

- Record existence and ownership validated.
- S3 key uses `uuid.uuid4()`, not user input.
- Presigned URL expiry is 300-900 seconds.
- File type validated against allowlist.
- Database record updated with the new key.
- Cache invalidated for the affected record.
- Reuse first: existing code was reviewed before writing; no duplicated logic.
- File discipline followed (see backend-invariants).
