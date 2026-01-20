# API Examples

## Setup

Start the service:

```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost/credentials
cargo run
```

The service will be available at `http://localhost:3000`

## Issue a Credential

```bash
curl -X POST http://localhost:3000/api/v1/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "did:example:alice123",
    "subject_name": "Alice Smith",
    "subject_email": "alice@example.com",
    "achievement_id": "achievement-1",
    "issuer_id": "issuer-1",
    "expires_at": "2025-12-31T23:59:59Z"
  }'
```

Response:

```json
{
  "credential": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "credential_subject": {
      "id": "did:example:alice123",
      "name": "Alice Smith",
      "email": "alice@example.com"
    },
    "achievement": {
      "id": "https://example.com/achievements/1",
      "name": "Digital Literacy Certificate",
      "description": "Demonstrates proficiency in digital literacy skills"
    },
    "issuer": {
      "id": "https://example.com/issuers/1",
      "name": "Example University"
    },
    "status": "active",
    "issued_at": "2025-12-05T10:30:00Z",
    "proof": {
      "type": "Ed25519Signature2020",
      "proofValue": "mock-signature-..."
    }
  }
}
```

## Revoke a Credential

```bash
curl -X POST http://localhost:3000/api/v1/credentials/550e8400-e29b-41d4-a716-446655440000/revoke \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Credential no longer valid"
  }'
```

Response:

```json
{
  "credential": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "revoked",
    "revocation_info": {
      "revoked_at": "2025-12-05T11:00:00Z",
      "reason": "Credential no longer valid"
    }
  }
}
```

## Health Check

```bash
curl http://localhost:3000/health
```

Response: `200 OK`

## Error Responses

### Validation Error

```bash
curl -X POST http://localhost:3000/api/v1/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "",
    "achievement_id": "achievement-1",
    "issuer_id": "issuer-1"
  }'
```

Response: `400 Bad Request`

```json
{
  "error": "ValidationError",
  "field": "credentialSubject.id",
  "message": "Subject ID cannot be empty"
}
```

### Not Found Error

```bash
curl http://localhost:3000/api/v1/credentials/00000000-0000-0000-0000-000000000000
```

Response: `404 Not Found`

```json
{
  "error": "CredentialNotFound",
  "id": "00000000-0000-0000-0000-000000000000",
  "message": "Credential not found: 00000000-0000-0000-0000-000000000000"
}
```

### Already Revoked Error

```bash
# Try to revoke an already revoked credential
curl -X POST http://localhost:3000/api/v1/credentials/{id}/revoke \
  -H "Content-Type: application/json" \
  -d '{"reason": "test"}'
```

Response: `409 Conflict`

```json
{
  "error": "CredentialAlreadyRevoked",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Credential already revoked: 550e8400-e29b-41d4-a716-446655440000"
}
```

## Testing with HTTPie

If you have HTTPie installed, the syntax is more concise:

```bash
# Issue credential
http POST localhost:3000/api/v1/credentials \
  subject_id=did:example:bob456 \
  subject_name="Bob Jones" \
  achievement_id=achievement-1 \
  issuer_id=issuer-1

# Revoke credential
http POST localhost:3000/api/v1/credentials/{id}/revoke \
  reason="No longer applicable"
```

## Testing with Postman

Import the following collection:

1. **Issue Credential**
   - Method: POST
   - URL: `http://localhost:3000/api/v1/credentials`
   - Body (JSON):
     ```json
     {
       "subject_id": "did:example:test",
       "achievement_id": "achievement-1",
       "issuer_id": "issuer-1"
     }
     ```

5. **Revoke Credential**
   - Method: POST
   - URL: `http://localhost:3000/api/v1/credentials/{{credential_id}}/revoke`
   - Body (JSON):
     ```json
     {
       "reason": "Testing revocation"
     }
     ```
