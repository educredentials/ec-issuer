# Import in Wallet

Technical details for the [Import In Wallet Feature](./features.md#wallet).

```mermaid
sequenceDiagram
    autonumber
    actor EndUser
    participant Wallet

    box
      participant RecipientPortal
      participant ec-issuer
      participant ec-award
      participant ec-authentication
      participant ec-access-control
      participant ec-achievement
      participant ec-user

      participant ec-key
      participant ec-status
      participant ec-notification
    end

    EndUser->>RecipientPortal: Import in Wallet (AwardId)
    RecipientPortal->>ec-issuer: Create Offer(AwardId)
    ec-issuer->>ec-access-control: May import(AwardId)
    ec-access-control->>ec-issuer: Yes
    ec-issuer->>ec-issuer: Create and Store Offer(OfferId, AwardId)
    ec-issuer-->>ec-notification: Publish OfferCreated event
    ec-issuer->>RecipientPortal: Offer
    RecipientPortal->>EndUser: Offer as QR

    rect rgba(0, 0, 255, .05)
        EndUser->>Wallet: Scan Offer QR
        note Right of Wallet: OID4VCI Authorization Code flow<br/>with deferred Credential endpoint

        Wallet->>ec-issuer: Obtain Credential Issuer Metadata
        Wallet->>ec-authentication: Authentication Request (OfferId)
        ec-authentication->>Wallet: Authentication Response (code)
        Wallet->>ec-authentication: Token Request (code)
        ec-authentication->>Wallet: Token Response (AccessToken, State<OfferId>)
        Wallet->>ec-issuer: Credential Request (AccessToken, Proofs)
        ec-issuer->>ec-issuer: Get Offer (OfferId)
        ec-issuer->>ec-authentication: Authenticate(AccessToken, OfferId)
        ec-authentication->>ec-issuer: OK
        ec-issuer->>Wallet: Credential Response (TransactionId)
    end

    ec-issuer->>ec-award: Get Award(AwardId)
    ec-award->>ec-issuer: Award
    ec-issuer->>ec-status: Get Unused Index
    ec-status->>ec-issuer: index
    ec-issuer->>ec-issuer: Turn Award into Credential for (Format, HolderDID, IssuerDID, index)
    ec-issuer->>ec-key: Sign (Credential)
    ec-key->>ec-issuer: Verifiable Credential


    rect rgba(0, 0, 255, .05)
      Wallet->>ec-issuer: Deferred Credential (TransactionId)
      ec-issuer->>Wallet: Verifiable Credential
      Wallet->>EndUser: Success(Verifiable Credential)
    end

    ec-issuer-->>ec-notification: Publish CredentialIssued event
```

In this diagram, the following actions take place:

1. *EndUser* requests to import award in wallet via *RecipientPortal*
1. *RecipientPortal* creates offer for the award on *Issuer*
1. *Issuer* checks permission on *Access Control*
1. *Access Control* returns Yes when permission is allowed
1. *Issuer* creates and stores the offer
1. *Issuer* publishes offer created event on *Notification Service*
1. *Issuer* returns offer to *RecipientPortal*
1. *RecipientPortal* presents offer as QR code to *EndUser*
1. *EndUser* scans QR code with *Wallet*
1. *Wallet* obtains credential issuer metadata from *ec-issuer*
1. *Wallet* sends authentication request to *ec-authentication*
1. *ec-authentication* returns code to *Wallet*
1. *Wallet* requests token with code from *ec-authentication*
1. *ec-authentication* returns access token and state to *Wallet*
1. *Wallet* sends credential request with access token and proofs to *ec-issuer*
1. *ec-issuer* retrieves offer from its storage
1. *ec-issuer* authenticates token and offer on *ec-authentication*
1. *ec-authentication* confirms authentication to *ec-issuer*
1. *ec-issuer* sends credential response with transaction ID to *Wallet*
1. *ec-issuer* requests award details from *ec-award*
1. *ec-award* returns award to *ec-issuer*
1. *ec-issuer* gets unused index from *ec-status*
1. *ec-status* returns index to *ec-issuer*
1. *ec-issuer* converts award to credential
1. *ec-issuer* requests signature from *ec-key*
1. *ec-key* returns signed verifiable credential to *ec-issuer*
1. *Wallet* requests deferred credential from *ec-issuer*
1. *ec-issuer* sends verifiable credential to *Wallet*
1. *Wallet* notifies *EndUser* of success with verifiable credential
1. *ec-issuer* publishes credential issued event on *Notification Service*

[Diagram taken from Backstage docs](https://backstage.sdp.surf.nl/docs/default/component/educredentials-service/educredentials_services_architecture/#sequence-diagrams-work-in-progress)
