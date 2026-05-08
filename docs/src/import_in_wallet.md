# Import in Wallet

Technical details for the [Import In Wallet Feature](./features.md#wallet).

```mermaid
sequenceDiagram
    autonumber
    actor EndUser
    participant Wallet

    box ec-issuer
      participant RecipientPortal
      participant ec-issuer
      participant ec-authentication
      participant ec-access-control
      participant ec-notification
    end

    box ssi-agent
      participant oid4vci-agent
    end

    EndUser->>RecipientPortal: Import in Wallet (AwardId)
    RecipientPortal->>ec-issuer: Create Credential and Offer(AwardId)
    ec-issuer->>ec-access-control: May import(AwardId)
    ec-access-control->>ec-issuer: Yes
    ec-issuer->>oid4vci-agent: Create Offer
    oid4vci-agent->>ec-issuer: Offer
    ec-issuer->>ec-notification: Publish OfferCreated event
    ec-issuer->>RecipientPortal: Offer
    RecipientPortal->>EndUser: Offer as QR

    rect rgba(0, 0, 255, .05)
        EndUser->>Wallet: Scan Offer QR
        note Right of Wallet: OID4VCI Authorization Code flow<br/>with deferred Credential endpoint

        Wallet->>oid4vci-agent: Obtain Credential Issuer Metadata
        Wallet->>ec-authentication: Authentication Request (OfferId)
        ec-authentication->>Wallet: Authentication Response (code)
        Wallet->>ec-authentication: Token Request (code)
        ec-authentication->>Wallet: Token Response (AccessToken, State<OfferId>)
        Wallet->>oid4vci-agent: Credential Request (AccessToken, Proofs)
        oid4vci-agent->>oid4vci-agent: Verify and Process Request
        oid4vci-agent->>Wallet: Credential Response (TransactionId)
    end

    oid4vci-agent->>ec-issuer: CredentialSigned event
    ec-issuer->>ec-notification: Publish CredentialIssued event

    rect rgba(0, 0, 255, .05)
      Wallet->>oid4vci-agent: Deferred Credential (TransactionId)
      oid4vci-agent->>Wallet: Verifiable Credential
      Wallet->>EndUser: Success(Verifiable Credential)
    end
```

In this diagram, the following actions take place:

1. *EndUser* requests to import award in wallet via *RecipientPortal*
1. *RecipientPortal* creates credential and offer for the award on *ec-issuer*
1. *ec-issuer* checks permission on *Access Control*
1. *Access Control* returns Yes when permission is allowed
1. *ec-issuer* creates offer on *oid4vci-agent*
1. *oid4vci-agent* returns offer to *ec-issuer*
1. *ec-issuer* publishes offer created event on *Notification Service*
1. *ec-issuer* returns offer to *RecipientPortal*
1. *RecipientPortal* presents offer as QR code to *EndUser*
1. *EndUser* scans QR code with *Wallet*
1. *Wallet* obtains credential issuer metadata from *oid4vci-agent*
1. *Wallet* sends authentication request to *ec-authentication*
1. *ec-authentication* returns code to *Wallet*
1. *Wallet* requests token with code from *ec-authentication*
1. *ec-authentication* returns access token and state to *Wallet*
1. *Wallet* sends credential request with access token and proofs to *oid4vci-agent*
1. *oid4vci-agent* verifies and processes the request
1. *oid4vci-agent* sends credential response with transaction ID to *Wallet*
1. *oid4vci-agent* sends CredentialSigned event to *ec-issuer*
1. *ec-issuer* publishes CredentialIssued event on *Notification Service*
1. *Wallet* requests deferred credential from *oid4vci-agent*
1. *oid4vci-agent* sends verifiable credential to *Wallet*
1. *Wallet* notifies *EndUser* of success with verifiable credential

[Diagram adapted from Backstage docs](https://backstage.sdp.surf.nl/docs/default/component/educredentials-service/educredentials_services_architecture/#sequence-diagrams-work-in-progress)
