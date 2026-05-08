# Features

User stories taken from [SURF Confluence](https://confluence.ia.surf.nl/spaces/EDUCRED/pages/297338250/Epics+and+user+stories+eduCredentials#EpicsanduserstorieseduCredentials-IssuanceOBv3andELM). The Confluence versions are leading and we should update, remove, change this document accordingly.

These user stories describe **the whole** platform of EduCredentials, not just the issuer part. We only show the stories that are relevant.

For each such story, one or more features for the issuer are derived.

## Wallet

As a learner, I want to store the credential in my personal mobile wallet.

Refer to [dedicated Import In Wallet](./import_in_wallet.md) for technical details.

### Import in wallet

As a student, when I have a badge in my backpack, and I have the unime app, then I want to be able to import the badge into this app as Verifiable Credential. So that I am the true owner of my badge credential. And so that I can use it to prove that I have met the requirements of the achievement the badge represents.

Features:

- [ ] OpenID for Verifiable Credential Issuance (OID4VCI) standards authorization code flow with a mobile wallet
  - [ ] Credential Issuer Metadata *(ADR003: needs re-implementation with ssi-agent as peer service)*
  - [ ] Credential Offer creation and delivery to user as QR code *(ADR003: needs re-implementation with ssi-agent as peer service)*
  - [ ] OpenID connect authentication flow started from wallet *(ADR003: needs re-implementation with ssi-agent as peer service)*
  - [ ] Credential Request with authorization token and proof of possession *(ADR003: needs re-implementation with ssi-agent as peer service)*
  - [ ] Credential Response with signed Verifiable Credential in Open Badges 3.0 format *(ADR003: needs re-implementation with ssi-agent as peer service)*
  - [ ] Deferred Credential response *(ADR003: needs re-implementation with ssi-agent as peer service)*

#### Edge Cases

As student Anna, when I have a badge in my backpack, and I import that in my wallet, then the device that has this wallet will 
require me to authenticate again. And when I authenticate there as Anna as well, I receive the credential in my wallet.

As student Anna, when I have a badge in my backpack, and Mallory scans this QR code, then the device that has his wallet will 
require him to authenticate again. And when he authenticate there as Mallory, he will receive an error instead of the wallet.
Or when he fails to authenticate there, the flow stops there and no request is made at all.

- [ ] In addition to the above-mentioned OID4VCI flow, the authorization token is checked to determine if the person logged in on their phone is the person that was logged in on backpack.
- [ ] Determine if we, the EC-issuer, handle the authorization, or if we defer it to the upstream issuer.
- [ ] Determine what attributes to match equivalence on - considering federative nature of eduids: the uuid for Anna-in-backpack may not be the uuid for Anna-on-the-phone.
- [ ] Consider if an authentication proxy is needed to handle the oidc flow around surfconext and eduid.


### Alternative wallets

As a student, when I have a badge in my backpack, and I do not have, nor want to use the unime app, then I can choose to use Paradyme or Sphereon app. Then I will be able to import the badge into this app as Verifiable Credential, but without guarantee that the app will be able to import, show, and verify the badge. So that I am the true owner of my badge credential in an app of my choice.

Features:

- [ ] Compliance with [DIIPv4 standards](https://fidescommunity.github.io/DIIP/v4)
  -  Credential format 	W3C VCDM 2.0 (20 March 2025) and SD-JWT VC (draft 08)
  - Signature scheme 	SD-JWT as specified in VC-JOSE-COSE (20 March 2025) and SD-JWT VC (draft 08)
  - Signature algorithm 	ES256 (RFC 7518 May 2015)
  - Identifying Issuers, Holders, and Verifiers 	did:jwk (Commit 8137ac4, Apr 14 2022) and did:web (31 July 2024)
  - Issuance protocol 	OpenID for Verifiable Credentials Issuance (OID4VCI) (Draft 15)
  - Presentation protocol 	OpenID for Verifiable Presentations (OID4VP) (Draft 28)
  - Revocation mechanism 	IETF Token Status List (Draft 10, 2025-04-16)
  
## ELM and Europass

As a student, when I have a badge in my backpack, and I want to download a ELM (Europass) version of the badge, then I want to be able to upload this file in the euro-pass environment so that this environment can verify the badge and show that the verification is valid.

Features: 
- [ ] Download signed Verifiable Credential file in ELM format.
- [ ] File can be uploaded in euro-pass environment and shows as partially verified. Our eSeal signature is not valid and is allowed to show as invalid in the euro-pass environment.


## Institution

As an institution, I want to hand a badge to a user, so that I can provide digital versions of certificates, diplomas and other achievements.

Such an institution is now an _issuer_.

### ELM and OBV3 compliance

As an institution, when I issue a badge to a user, then I want to be able to provide whether this badge will be available for importing in the unime app, and/or in the euro-pass environment, so that we can provide the appropriate attributes to comply with the standards for the unime app and/or euro-pass.

Features:
- [ ] Add an endpoint where services (e.g. issuance portal) can provide an achievement and see if this complies with OBV3 and/or ELM standards.

### Edit existing achievements

As an issuer, I want to edit or archive an achievement when no credentials are issued of this achievement.

TODO: Note, this seems a non-story. As this is not something the issuer *wants* but merely describes the current implementation.

### Digital credentials

As an issuer, I want to issue a digital credential to learners who are entitled to receive it.

 - [ ] [3.2 Assertion Issuance Without a Wallet](https://www.imsglobal.org/spec/ob/v3p0/#assertion-issuance-without-a-wallet)
    - [ ]  Implement Badge Connect API to deliver assertions to a backpack
    
### Revocation

As an issuer, I want to be able to revoke credentials, so that they cannot be verified any more.
  
TODO: research if, and how an [IETF-TOKEN-STATUS-LIST](https://fidescommunity.github.io/DIIP/v4#term:ietf-token-status-list) can be implemented as separate microservice from the issuance.
      research potential candidates for such a status list service.

### Status log

As an issuer, I want to see the status and history of the issuing and revoking of a credential.

TODO: Define the statuses of a credential
TODO: Define what events are needed for this "history"

### Usage Statistics

As an issuer, I want to see statistics about the credentials that have been issued from my organisation.

TODO: Define KPIs for issuers and consequently the events that need to be stored for this.
