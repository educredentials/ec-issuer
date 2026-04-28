# Keys

The keys in this directory are used in test suites and should be considered
compromised and insecure.

- wallet_holder_* are keys for the wallet. Used to generate proof.
- issuer_* are keys for the issuer.

## Eddsa, aka ed25519

Generate with openssl (and not with ssh-keygen!):

```
openssl genpkey -algorithm ed25519 -out tests/e2e/keys/wallet_holder_eddsa.priv
openssl pkey -in tests/e2e/keys/wallet_holder_eddsa.priv -pubout -out  tests/e2e/keys/wallet_holder_eddsa.pub
```
