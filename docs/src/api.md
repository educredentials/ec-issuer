# API Examples

With a running instance of the service, you can interact with the API using the following examples.

TODO: differentiate between admin and issuance via subdomains or via paths? admin.example.com and issuer.example.com vs issuer.example.com/admin and issuer.example.com/

## Admin

All administrative endpoints require admin access token.
All these endpoints fall under /admin/v1/. Versioned in path.

## Issue an Achievement as Credential, aka Create Offer

```bash
curl -X POST http://issuer.example.com/admin/v1/offers  \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "achievement_id": "achievement-1",
  }'
```

Response:

```json
{
  "uri": "openid-credential-offer://?credential_offer_uri=https://issuer.example.com/offers/550e8400-e29b-41d4-a716-446655440000",
  "offer_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Public endpoints

* All endpoints for oid4vci flows are public by default
* Some allow no authorization as per spec (e.g. well-known)
* Some require authorization as per spec (e.g. credentials endpoint)

* public endpoints are not versioned in path.
* public endpoints are not scoped in path (e.g. /public/). Due to requirements in e.g. the oid4vci spec.

### Get Metadata

```bash
curl http://issuer.example.com/.well-known/openid-credential-issuer
```

Other endpoints:

get /.well-known/did-configuration.json
get /.well-known/did.json
get /.well-known/oauth-authorization-server
get /.well-known/openid-credential-issuer

Response (see https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-metadata)

```json
{
  "credential_issuer": "https://issuer.example.com",
  "authorization_servers": ["https://authn.example.com"],
  "credential_configurations_supported": {},
}
```

### Get an offer 

AKA Dereference offer from credential_offer_uri

Location not specced. But for consistency, under /offers

```bash
curl http://issuer.example.com/offers/550e8400-e29b-41d4-a716-446655440000
```

[Offer Response](https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-credential-offer-response)

```json
{
  "credential_issuer": "https://issuer.example.com",
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

### Get a credential (OpenId for VCI authorization code flow)

Location specced and defaults to /credentials. Will be included in metadata. For
simplicity and consistency we use this default.

Get the credential. A reference to deferred endpoint is always returned.

See [OIDvVCI Credential Request](https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-credential-request)

```bash
curl -X POST http://issuer.example.com/credentials \
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

### Get Deferred Credential

Get the credential at the [deferred endpoint](https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-deferred-credential-endpoin).

Request:
```bash
curl -X POST http://issuer.example.com/deferred_credential
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
curl -X DELETE http://issuer.example.com/admin/v1/credentials/550e8400-e29b-41d4-a716-446655440000 \
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
curl http://issuer.example.com/health
```

Response: `200 OK`

## Error Responses

TODO: design and describe all errors.

See
* https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-credential-error-response
* https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-deferred-credential-error-r
