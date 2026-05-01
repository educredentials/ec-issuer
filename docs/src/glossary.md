# Glossary

Words, terms and acronyms used in context of the project. Domain language, or ubiquitous language.

## A

Achievement
	: A collection of information about the accomplishment recognized by the Assertion. Formerly known as _BadgeClass_

AchievementCredential
  : Specific variation of a Credential. A Credential that follows the OpenBadge specification for its content.
  
Actor
  : The entity performing an action. This is currently either a _Subject_ or an _Issuer_.
  
## B

## C

Credential
  : A credential is a set of attributes that are issued by an issuer and can be verified by a verifier.

## D

## E

EC
  : _E_du_C_redentials. Prefix used in the EduCredentials project, services, and products.

EC-achievements
  : Service that manages and provides Achievements

EC-authorization
  : Service that manages access to resources. In context of Educredentials Issuer, it allows us to check what _Actor_ may _Issue_ what _Achievement_ to what _Subject_.

EC-issuer, Educredentials Issuer
  : This service. The software in this repo.

## F

## G

## H

## I

Issuer
  : The entity (usually a person) that signs a verifiable credential. In practice this is either a staff, teacher or other person when a _Credential_ is issued to a _Subject_. Or it is a student who issues a previously received Credential into their wallet. TODO: Differentiate between the Issuer whose signature is used, and the Person who initialized the Issuance in terminology

Issuer Agent (aka Issuer-agent)
  : The software that is used by an issuer to create and sign a verifiable credential. Current implementation uses the ssi-agent, also known as _Unime-Core_ for this.

## J

## K

## L

## M

## N

## O

Open Badges (aka OpenBadgeCredential, OBv3)
  : Open Badges is an [open standard](https://www.imsglobal.org/spec/ob/v3p0) for digital badges. It is a specification for the issuance and verification of digital badges.

## P

## P

## Q

## R

Revocation
  : The process of invalidating a verifiable credential. Since verifiable credentials are decentralized and immutable, they cannot be deleted. Instead, they are revoked by adding them to a [revocation - aka status- list](https://datatracker.ietf.org/doc/draft-ietf-oauth-status-list/)).

## S

Subject
  : The entity (usually a person) that receives a verifiable credential.

Staff
  : Deprecated, see _Issuer_ instead.
Student
  : Deprecated, see _Subject_ instead.

## T

Teacher
  : Deprecated, see _Issuer_ instead.

## U

## V

## W

Wallet
  : A digital wallet is a software application that stores verifiable credentials and other digital assets. It is used to get credentials from issuers, store them securely, manage and present these credentials to verifiers.

Wrapper
  : This ec-issuer service is a wrapper. It wraps the functionality of existing open source issuance software. It abstracts the functionality of the wrapped software and exposes it in domain terms and in a way that is easy to use.

## V

Verifier
  : The entity that verifies a credential. This can be software or a person using this software. Software will typically be a service that returns "valid" or "invalid" for a given credential. A person will typically be a human that can visually inspect a credential and decide if it is valid or not and interpret the content of the verified attributes.

Verifiable Credential, (aka VCDM)
  : A verifiable credential is a tamper-evident credential that has authorship that can be cryptographically verified. It is an [open standard](https://www.w3.org/TR/vc-data-model/).

## X

## Y

## Z
