import re
import urllib.request
from base64 import b64decode

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.x509 import load_pem_x509_certificate

# AWS SNS certs are always served from this pattern of hostname.
# This regex guards against a forged SigningCertURL pointing elsewhere.
VALID_CERT_URL_PATTERN = re.compile(r"^https://sns\.[a-z0-9\-]+\.amazonaws\.com/")

# Fields that go into the signature, in this exact order, depending
# on message type. See AWS docs: "Verifying the signatures of Amazon SNS messages".
SIGNABLE_FIELDS_NOTIFICATION = [
    "Message",
    "MessageId",
    "Subject",
    "Timestamp",
    "TopicArn",
    "Type",
]

SIGNABLE_FIELDS_SUBSCRIPTION = [
    "Message",
    "MessageId",
    "SubscribeURL",
    "Timestamp",
    "Token",
    "TopicArn",
    "Type",
]


def _build_string_to_sign(payload: dict) -> bytes:
    if payload.get("Type") in ("SubscriptionConfirmation", "UnsubscribeConfirmation"):
        fields = SIGNABLE_FIELDS_SUBSCRIPTION
    else:
        fields = SIGNABLE_FIELDS_NOTIFICATION

    parts = []
    for field in fields:
        if field in payload:
            parts.append(field)
            parts.append(str(payload[field]))

    return ("\n".join(parts) + "\n").encode("utf-8")


def verify_sns_message(payload: dict) -> bool:
    """
    Verifies that an incoming SNS payload was genuinely signed by AWS.
    Returns True only if the signature is valid AND the cert URL is a
    real AWS SNS endpoint.
    """
    cert_url = payload.get("SigningCertURL", "")
    signature_b64 = payload.get("Signature", "")

    if not cert_url or not signature_b64:
        return False

    if not VALID_CERT_URL_PATTERN.match(cert_url):
        return False

    try:
        with urllib.request.urlopen(cert_url, timeout=5) as response:
            cert_pem = response.read()

        certificate = load_pem_x509_certificate(cert_pem)
        public_key = certificate.public_key()

        # AWS SNS always signs with RSA. Guard explicitly so type
        # checkers (and we, at runtime) know .verify() has the RSA signature.
        if not isinstance(public_key, RSAPublicKey):
            return False

        string_to_sign = _build_string_to_sign(payload)
        signature = b64decode(signature_b64)

        public_key.verify(
            signature,
            string_to_sign,
            padding.PKCS1v15(),
            hashes.SHA1(),
        )
        return True

    except (InvalidSignature, Exception):
        return False
