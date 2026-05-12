# Glossary

Words, terms and acronyms used in context of the project. Domain language, or ubiquitous language.

## A

Achievement
  : A collection of information about the accomplishment recognized by the Assertion. Formerly known as _BadgeClass_

AchievementCredential
  : Specific variation of a Credential. A Credential that follows the Open Badges 3.0 specification for its content.

Award
  : An Achievement that has been coupled to a user. Plain text. when signed, it becomes a credential. Identified by AwardId
  
Actor
  : The entity performing an action. This is currently either a _Subject_ or an _Issuer_.
  
## B

Backpack
  : TODO: Define this term. Found in: docs/src/features.md

## C

Credential Offer
  : TODO: Define this term. Found in: OpenAPI specification, docs/src/features.md

Credential
  : A credential is a set of attributes that are issued by an issuer and can be verified by a verifier.

## D

DID
  : TODO: Define this term. Found in: docs/src/import_in_wallet.md

Deferred Credential
  : TODO: Define this term. Found in: OpenAPI specification, docs/src/features.md

## E

ELM
  : TODO: Define this term. Found in: README.md, docs/src/features.md. See also: European Learner Model.

European Learner Model
  : TODO: Define this term. Found in: README.md, docs/src/glossary.md

eSeal
  : TODO: Define this term. Found in: docs/src/features.md

EC
  : _E_du_C_redentials. Prefix used in the EduCredentials project, services, and products.

EC-achievements
  : Service that manages and provides Achievements

EC-authorization
  : Service that manages access to resources. In context of EC-issuer, it allows us to check what _Actor_ may _Issue_ what _Achievement_ to what _Subject_.

EC-issuer
  : This service. The software in this repo. Also known as Educredentials Issuer.

## F

## G

## H

## I

Issuer
  : The entity (usually a person) that signs a verifiable credential. In practice this is either a staff, teacher or other person when a _Credential_ is issued to a _Subject_. Or it is a student who issues a previously received Credential into their wallet. TODO: Differentiate between the Issuer whose signature is used, and the Person who initialized the Issuance in terminology


## J

## K

## L

## M

Mock SSI-Agent
  : A fake, static version of the _SSI-Agent_. Stands in for the concrete implementation of the OID4VCI service, in our tests. Offers deterministic, controllable responses that mimick the responses of the _SSI-Agent_.

## N

## O


OID4VCI
  : Abbreviation of OpenID for Verifiable Credentials Issuance.

OID4VCI Agent
  : The software that is used by an issuer to create and sign a verifiable credential. OID4VCI Agent was previously called "Issuance Agent".

OID4VP
  : TODO: Define this term. Found in: docs/src/features.md

Open Badges 3.0 (aka OpenBadgeCredential, OBv3)
  : Open Badges is an [open standard](https://www.imsglobal.org/spec/ob/v3p0) for digital badges. It is a specification for the issuance and verification of digital badges.

OpenID for Verifiable Credential Issuance
  : OpenID for Verifiable Credentials (OID4VCI) is a specification for the issuance and verification of verifiable credentials. It is based on the OpenID Connect protocol. See [OID4VCI](https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html) for more information.

## P

## Q

## R

Revocation
  : The process of invalidating a verifiable credential. Since verifiable credentials are decentralized and immutable, they cannot be deleted. Instead, they are revoked by adding them to a [revocation - aka status- list](https://datatracker.ietf.org/doc/draft-ietf-oauth-status-list/)).

## S

SD-JWT
  : TODO: Define this term. Found in: docs/src/features.md

SSI-Agent
  : Concrete implementation of the _OID4VCI Agent_. Built by Impierce, also known as _Unime-Core_.
    We integrate, configure and build this service using [https://github.com/educredentials/ssi-agent-build].
    See also _Mock SSI-Agent_.

Subject
  : The entity (usually a person) that receives a verifiable credential.

Staff
  : Deprecated, see _Issuer_ instead.
Student
  : Deprecated, see _Subject_ instead.

## T

Teacher
  : Deprecated, see _Issuer_ instead.

Transaction ID
  : TODO: Define this term. Found in: OpenAPI specification, docs/src/import_in_wallet.md

## U

Unime
  : TODO: Define this term. Found in: docs/src/features.md, docs/src/import_in_wallet.md

## V

Verifiable Credential
  : A verifiable credential is a tamper-evident credential that has authorship that can be cryptographically verified. It is an [open standard](https://www.w3.org/TR/vc-data-model/). Also known as VCDM (Verifiable Credential Data Model).

Verifier
  : The entity that verifies a credential. This can be software or a person using this software. Software will typically be a service that returns "valid" or "invalid" for a given credential. A person will typically be a human that can visually inspect a credential and decide if it is valid or not and interpret the content of the verified attributes.

VCDM
  : TODO: Define this term. Found in: docs/src/glossary.md. See also: Verifiable Credential.
## W

Wallet
  : A digital wallet is a software application that stores verifiable credentials and other digital assets. It is used to get credentials from issuers, store them securely, manage and present these credentials to verifiers.

Wrapper
  : This EC-issuer service works alongside existing issuer services such as ssi-agent. It orchestrates and integrates the issuance process, manages templates and configurations, and exposes a simple, pragmatic API while delegating actual credential issuance to the underlying issuer service.


## X

## Y

## Z
