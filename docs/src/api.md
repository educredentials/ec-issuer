# API Examples

With a running instance of the services, you can interact with the APIs using the following examples.

**Service Architecture**: This documentation covers two separate but integrated services:
- **ec-issuer** (`ec-issuer.example.com`): Administrative service that manages templates, credential configurations, and creates offers. Handles business logic and orchestration.
- **ssi-agent** (`oid4vci-agent.example.com`): Handles the OpenID4VCI protocol flow, including credential issuer metadata, credential offers, and credential requests. Performs the actual credential signing and delivery.

## ec-issuer: Admin

All administrative endpoints require admin access token.
All these endpoints fall under `/admin/v1/`. Versioned in path.

### Create Credential and Offer

The ec-issuer creates a credential configuration on the ssi-agent and then creates an offer there.

```bash
curl -X POST https://ec-issuer.example.com/admin/v1/offers \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "achievement_id": "achievement-1",
  }'
```

Response:

```json
{
  "uri": "openid-credential-offer://?credential_offer_uri=https://oid4vci-agent.example.com/offers/550e8400-e29b-41d4-a716-446655440000",
  "offer_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Revoke a Credential

```bash
curl -X DELETE https://ec-issuer.example.com/admin/v1/credentials/550e8400-e29b-41d4-a716-446655440000 \
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

### Health Check

```bash
curl https://ec-issuer.example.com/health
```

Response: `200 OK`

## ssi-agent: OID4VCI Public Endpoints

All OID4VCI endpoints are public by default as per the OpenID4VCI specification.
These endpoints are served by the ssi-agent directly, not proxied through ec-issuer.

* Public endpoints are not versioned in path
* Public endpoints are not scoped in path (e.g., `/public/`) due to OID4VCI spec requirements

### Get Credential Issuer Metadata

```bash
curl https://oid4vci-agent.example.com/.well-known/openid-credential-issuer
```

Other available well-known endpoints:

- `/.well-known/did-configuration.json`
- `/.well-known/did.json`
- `/.well-known/oauth-authorization-server`
- `/.well-known/openid-credential-issuer`

Response (see [OID4VCI Metadata](https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-metadata)):

```json
{
  "credential_issuer": "https://oid4vci-agent.example.com",
  "authorization_servers": ["https://authn.example.com"],
  "credential_configurations_supported": {}
}
```

### Get a Credential Offer

AKA Dereference offer from `credential_offer_uri`.

Location: `/offers/{offer_id}`

```bash
curl https://oid4vci-agent.example.com/offers/550e8400-e29b-41d4-a716-446655440000
```

[Offer Response](https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-credential-offer-response)

```json
{
  "credential_issuer": "https://oid4vci-agent.example.com",
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

### Get a Credential (OID4VCI Authorization Code Flow)

Location: `/credentials` (specified by OID4VCI, included in metadata).

Get the credential. A reference to deferred endpoint is always returned.

See [OID4VCI Credential Request](https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-credential-request)

```bash
curl -X POST https://oid4vci-agent.example.com/credentials \
  -H "Authorization: Bearer TokenAsReturnedFromAuthServer" \
  -H "Content-Type: application/json" \
  -d '{
    "credential_configuration_id": "UniversityDegreeCredential",
    "proofs": {
        "jwt": [
            "eyJraWQiOiJkaWQ6ZXhhbXBsZTplYmZlYjFmNzEyZWJjNmYxYzI3NmUxMmVjMjEva2V5cy8x IiwiYWxnIjoiRVMyNTYiLCJ0eXAiOiJKV1QifQ"
        ]
    }
}'
```

Response:
```json
{
  "transaction_id": "8xLOxBtZp8",
  "interval": 3600
}
```

### Get Deferred Credential

Get the credential at the [deferred endpoint](https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-deferred-credential-endpoint).

Request:
```bash
curl -X POST https://oid4vci-agent.example.com/deferred_credential
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

## Error Responses

TODO: design and describe all errors.

See
* [OID4VCI Credential Error Response](https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-credential-error-response)
* [OID4VCI Deferred Credential Error Response](https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-deferred-credential-error-r)
