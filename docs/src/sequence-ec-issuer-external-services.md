---
title: "EC-Issuer — Component and External Services Interaction"
---

# EC-Issuer External Services Interaction

## Sequence diagram

```mermaid
sequenceDiagram
    autonumber

    participant Client as Client
    participant Api as HttpApiAdapter
    participant Service as OfferService
    participant Acl as AccessControlPort
    participant Awards as AwardsClientPort
    participant Converter as CredentialConverterPort
    participant Ssi as OffersClientPort
    participant Repo as OffersRepositoryPort
    participant AwardsSvc as Awards Service
    participant SsiSvc as SSI Agent
    participant Pg as PostgreSQL

    Note over Client: External
    Note over AwardsSvc,Pg: External

    Client->>Api: POST /api/v1/offers
    Api->>Api: Validate bearer token
    Api->>Service: create_offer(award_id, token, type)

    Service->>Acl: may_import(token, award_id)
    alt permitted
        Acl-->>Service: true
    else forbidden
        Acl-->>Service: false
        Service-->>Api: PermissionDeniedError
        Api-->>Client: 403
    end

    Service->>Awards: get_ob3(award_id, token)
    Awards->>AwardsSvc: GET /awards/{award_id}
    AwardsSvc-->>Awards: Award data / 404 / 403
    Awards-->>Service: OB3Award / AwardNotFound

    alt credential_type == "edc"
        Service->>Converter: convert(ob3_award)
        Converter->>Converter: encode → POST → decode
        Converter-->>Service: ELM/EDC credential dict
        Service->>Ssi: create_edc(offer_id, edc_credential)
    else credential_type == "ob3"
        Service->>Ssi: create_ob3(offer_id, award)
    end

    Ssi->>SsiSvc: POST /v0/credentials
    SsiSvc-->>Ssi: Created
    Ssi->>SsiSvc: POST /v0/offers
    SsiSvc-->>Ssi: offer URI
    Ssi-->>Service: offer_uri

    Service->>Repo: store(offer)
    Repo->>Pg: INSERT offers

    Service-->>Api: Offer {offer_id, uri}
    Api-->>Client: 201 {offer_id, uri}
```

**Visual distinction:** `Note` annotations mark external participants. See architecture diagram below for color-coded grouping.

## Architecture view

```mermaid
classDiagram
    direction TB

    class Client {
        <<external>>
        +POST /api/v1/offers
    }

    class HttpApiAdapter {
        <<Adapter>>
        +POST /api/v1/offers
    }
    class OfferService {
        <<Service>>
        +create_offer()
        +get_offer()
    }
    class AccessControlPort {
        <<Port>>
        +may_import()
    }
    class HardcodedAccessControlAdapter {
        <<Adapter>>
        +may_import()
    }
    class AwardsClientPort {
        <<Port>>
        +get_ob3()
    }
    class HttpAwardsClientAdapter {
        <<Adapter>>
        +get_ob3()
    }
    class CredentialConverterPort {
        <<Port>>
        +convert()
    }
    class HttpCredentialConverterAdapter {
        <<Adapter>>
        +convert()
    }
    class OffersClientPort {
        <<Port>>
        +create_ob3()
        +create_edc()
        +get()
    }
    class SsiAgentOffersClientAdapter {
        <<Adapter>>
        +create_ob3()
        +create_edc()
        +get()
    }
    class OffersRepositoryPort {
        <<Port>>
        +store()
        +get()
    }
    class PostgreSQLOffersRepositoryAdapter {
        <<Adapter>>
        +store()
        +get()
    }
    class Offer {
        <<Entity>>
        +offer_id
        +award_id
        +uri
    }

    class AwardsService {
        <<External>>
        +GET /awards/\:id
    }
    class SsiAgent {
        <<External>>
        +POST /v0/credentials
        +POST /v0/offers
    }
    class PostgreSQL {
        <<External>>
        +offers table
    }

    Client --> HttpApiAdapter : REST
    HttpApiAdapter --> OfferService : orchestrates
    OfferService --> AccessControlPort : permission gate
    OfferService --> AwardsClientPort : fetch award
    OfferService --> CredentialConverterPort : convert OB3→EDC
    OfferService --> OffersClientPort : issue credential
    OfferService --> OffersRepositoryPort : persist

    AccessControlPort ..> HardcodedAccessControlAdapter : implements
    AwardsClientPort ..> HttpAwardsClientAdapter : implements
    CredentialConverterPort ..> HttpCredentialConverterAdapter : implements
    OffersClientPort ..> SsiAgentOffersClientAdapter : implements
    OffersRepositoryPort ..> PostgreSQLOffersRepositoryAdapter : implements

    HttpAwardsClientAdapter --> AwardsService : HTTP
    SsiAgentOffersClientAdapter --> SsiAgent : HTTP
    PostgreSQLOffersRepositoryAdapter --> PostgreSQL : TCP
```

## Legend

| Style | Meaning |
|-------|---------|
| `<<Adapter>>` | Adapter (concrete implementation of a port) |
| `<<Port>>` | Port (interface the service depends on) |
| `<<Service>>` | Domain service (business logic) |
| `<<Entity>>` | Domain entity |
| `<<External>>` | Service outside ec-issuer |
| `-->` solid | Direct call / dependency |
| `..>` dotted | Implements (port → adapter) |

## External services

| Service | Protocol | Purpose | Port / Adapter |
|---------|----------|---------|----------------|
| **Awards Service** | HTTP REST | Fetch award/achievement data | `AwardsClientPort` → `HttpAwardsClientAdapter` |
| **SSI Agent** | HTTP REST (OID4VCI) | Create credentials and offers | `OffersClientPort` → `SsiAgentOffersClientAdapter` |
| **PostgreSQL** | TCP/Postgres wire | Persist offers | `OffersRepositoryPort` → `PostgreSQLOffersRepositoryAdapter` |
| **Credential Converter** | HTTP REST | Convert OB3 → ELM/EDC | `CredentialConverterPort` → `HttpCredentialConverterAdapter` |
| **Access Control** | In-process | Verify caller permissions | `AccessControlPort` → `HardcodedAdapter` |

## Flow summary

1. Client sends `POST /api/v1/offers` with `award_id` and `credential_type`
2. **Access Control** checks if the caller may import the award
3. **Awards Service** is queried to fetch the award data
4. If `credential_type == "edc"`, the **Credential Converter** translates OB3 → ELM/EDC
5. **SSI Agent** receives the credential and creates an offer, returning an offer URI
6. The offer is persisted in **PostgreSQL**
7. The client receives a `201 Created` response with the offer ID and URI