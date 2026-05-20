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

## Turn into a JWK for use in e.g. [./ssi-agent-mock.yaml]

```python
from cryptography.hazmat.primitives import serialization
import base64
import json

# Read the PEM file
with open("tests/e2e/keys/issuer_eddsa.pub", "rb") as f:
    pem_data = f.read()

# Load as Ed25519 public key
public_key = serialization.load_pem_public_key(pem_data)

# Extract raw 32-byte public key
raw_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw
)

# Verify it's 32 bytes
assert len(raw_bytes) == 32, f"Expected 32 bytes, got {len(raw_bytes)}"

# Convert to base64url for JWK
x_value = base64.urlsafe_b64encode(raw_bytes).decode('utf-8').rstrip('=')

# Output the JWK
jwk = {
    "kty": "OKP",
    "crv": "Ed25519",
    "x": x_value
}
print(json.dumps(jwk, indent=2))
```
