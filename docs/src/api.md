# API Examples

With a running instance of the service, you can interact with the API using the following examples.

## Get Metadata

```bash
curl http://localhost:3000/.well-known/openid-credential-issuer
```

Other endpoints:

get /.well-known/did-configuration.json
get /.well-known/did.json
get /.well-known/oauth-authorization-server
get /.well-known/openid-credential-issuer

Response (see https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-metadata)

```json
{
  "credential_issuer": "https://example.com",
  "authorization_servers": ["https://authn.example.com"],
  "credential_configurations_supported": {},
}
```

## Issue an Achievement as Credential, aka Create Offer

```bash
curl -X POST http://localhost:3000/api/v1/offers  \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "achievement_id": "achievement-1",
  }'
```

Response:

```json
{
  "uri": "openid-credential-offer://?credential_offer_uri=https://example.com/api/v1/offers/550e8400-e29b-41d4-a716-446655440000",
  "offer_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

Get the offer

```bash
curl http://localhost:3000/api/v1/offers/550e8400-e29b-41d4-a716-446655440000
```

Response (see https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-credential-offer-response):

```json
{
  "credential_issuer": "https://credential-issuer.example.com",
  "credential_configuration_ids": [
    "UniversityDegreeCredential"
  ],
  "grants": {
    "authorization_code": {
      "issuer_state": "eyJhbGciOiJSU0Et...FYUaBy"
    }
  }
}
```

## Get a credential (OpenId for VCI authorization code flow)

See get Metadata

Get the credential. A reference to deferred endpoint is always returned.

Request:
https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-credential-request

```bash
curl -X POST http://localhost:3000/api/v1/credentials \
  -H "Authorization: Bearer TokenAsReturnedFromAuthServer" \
  -H "Content-Type: application/json" \
  -d '{
    "credential_configuration_id": "UniversityDegreeCredential",
    "proofs": {
        "jwt": [
            "eyJraWQiOiJkaWQ6ZXhhbXBsZTplYmZlYjFmNzEyZWJjNmYxYzI3NmUxMmVjMjEva2V5cy8x IiwiYWxnIjoiRVMyNTYiLCJ0eXAiOiJKV1QifQ"
        ]
    }
}`
```

Response:
```
{
  "transaction_id": "8xLOxBtZp8",
  "interval" : 3600
}
```


Get the credential at the deferred endpoint (https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-deferred-credential-endpoin)

Request:
```bash
curl -X POST http://localhost:3000/api/v1/deferred_credential
  -H "Authorization: Bearer TokenAsReturnedFromAuthServer" \
  -H "Content-Type: application/json" \
  -d '{ "transaction_id": "8xLOxBtZp8" }'
```

Response (once the credential is ready):
```json
{
  "credentials": [
    {
      "credential": "LUpixVCWJk0eOt4CXQe1NXK....WZwmhmn9OQp6YxX0a2L"
    }
  ]
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

See
* https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-credential-error-response
*  https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-deferred-credential-error-r

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
