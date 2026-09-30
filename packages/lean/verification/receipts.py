"""Receiver-local receipt authentication. Imported JSON never grants authority.

The signing key belongs to the trusted receiver process, outside build roots.
This is local authentication, not a public signature or cross-receiver identity.
"""

import hashlib
import hmac
import json
import os
from pathlib import Path
import stat

import rfc8785

FORMAT = "slean-local-receipt/0.1-draft.1"
POLICY = "reviewed-source/0.1-draft.1"
UNREVIEWED_POLICY = "unreviewed-contribution/0.1-draft.1"
SUPPORTED_POLICIES = {POLICY, UNREVIEWED_POLICY}


class ReceiptStore:
    def __init__(self, directory, *, create=False):
        self.directory = Path(directory).absolute()
        if create:
            self.directory.mkdir(parents=True, mode=0o700, exist_ok=True)
        info = self.directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError("Receipt store must be a private receiver-owned directory")
        key_path = self.directory / "receiver.key"
        if create and not key_path.exists():
            descriptor = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(os.urandom(32))
        info = key_path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError("Receipt key must be a private receiver-owned file")
        self._key = key_path.read_bytes()
        if len(self._key) != 32:
            raise ValueError("Invalid receiver key")
        self.issuer = hashlib.sha256(self._key).hexdigest()

    def _signature(self, body):
        return hmac.new(self._key, (FORMAT + "\n").encode() + rfc8785.dumps(body), hashlib.sha256).hexdigest()

    def _record_checked(self, verification):
        """Internal: only the receiver verifier calls this after its checks pass."""
        if verification["status"] != "passed" or verification["policy"] not in SUPPORTED_POLICIES:
            raise ValueError("Only completed supported receiver checks can issue local receipts")
        body = {"format": FORMAT, "issuer": self.issuer, "verification": verification}
        receipt = {**body, "authentication": self._signature(body)}
        data = rfc8785.dumps(receipt) + b"\n"
        path = self.directory / (hashlib.sha256(data).hexdigest() + ".json")
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            if path.is_symlink() or path.read_bytes() != data:
                raise ValueError("Receipt collision")
        else:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
        return receipt

    def accept(self, receipt, *, module, component, statement, policy, context=None):
        """Read-only authentication plus exact subject, statement and policy match."""
        if not isinstance(receipt, dict) or set(receipt) != {"format", "issuer", "verification", "authentication"}:
            return None
        if receipt["format"] != FORMAT or receipt["issuer"] != self.issuer or policy not in SUPPORTED_POLICIES:
            return None
        body = {k: receipt[k] for k in ("format", "issuer", "verification")}
        try:
            if not hmac.compare_digest(self._signature(body), receipt["authentication"]):
                return None
        except (TypeError, ValueError):
            return None
        result = receipt["verification"]
        if (result.get("status") != "passed" or result.get("policy") != policy
                or result.get("subject") != {"module": module, "id": component}
                or result.get("statement_fingerprint") != statement
                or result.get("context") != ({} if context is None else context)):
            return None
        # The environment and exact artifact list are inside the authenticated body.
        if not result.get("environment_fingerprint") or not result.get("artifacts"):
            return None
        return json.loads(json.dumps(result))
