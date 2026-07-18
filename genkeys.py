from py_vapid import Vapid01
from cryptography.hazmat.primitives import serialization
import base64

v = Vapid01()
v.generate_keys()

# Private key as PEM string (for the server to sign with)
private_pem = v.private_pem().decode("utf-8")

# Public key as URL-safe base64 (for the browser to subscribe with)
raw_public = v.public_key.public_bytes(
    serialization.Encoding.X962,
    serialization.PublicFormat.UncompressedPoint,
)
public_key = base64.urlsafe_b64encode(raw_public).rstrip(b"=").decode("utf-8")

print("=== VAPID_PUBLIC_KEY (put in settings) ===")
print(public_key)
print()
print("=== VAPID_PRIVATE_KEY PEM (see Step 2) ===")
print(private_pem)