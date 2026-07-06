from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import platform
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Offline license signature key.
# This prevents casual editing of license.mcs. For maximum commercial protection,
# use asymmetric signing and keep the private key outside of the customer build.
_LICENSE_SECRET = b"MCS4-Monitor-Offline-License-Key-v1-Change-Before-Public-Release"

APP_NAME = "MCS-4 Professional Monitor"
LICENSE_FILE_NAME = "license.mcs"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def license_path() -> Path:
    env_path = os.environ.get("MCS4_LICENSE_FILE")
    if env_path:
        return Path(env_path)
    return app_dir() / LICENSE_FILE_NAME


def _windows_machine_guid() -> str | None:
    if platform.system().lower() != "windows":
        return None
    try:
        import winreg  # type: ignore
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
            value, _ = winreg.QueryValueEx(key, "MachineGuid")
            return str(value)
    except Exception:
        return None


def raw_machine_fingerprint() -> str:
    parts = [
        platform.system(),
        platform.node(),
        platform.machine(),
        platform.processor(),
        _windows_machine_guid() or "",
        str(uuid.getnode()),
    ]
    return "|".join(parts)


def machine_id() -> str:
    digest = hashlib.sha256(("MCS4|" + raw_machine_fingerprint()).encode("utf-8", errors="ignore")).hexdigest().upper()
    # readable but still strong enough for matching
    return "-".join([digest[i:i+8] for i in range(0, 32, 8)])


def canonical_payload(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sign_payload(payload: dict) -> str:
    sig = hmac.new(_LICENSE_SECRET, canonical_payload(payload), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode("ascii").rstrip("=")


def verify_signature(payload: dict, signature: str) -> bool:
    expected = sign_payload(payload)
    return hmac.compare_digest(expected, signature)


@dataclass
class LicenseStatus:
    valid: bool
    reason: str
    payload: dict | None = None
    days_left: int = 0
    path: Path | None = None

    @property
    def customer(self) -> str:
        if not self.payload:
            return "-"
        return str(self.payload.get("customer", "-"))

    @property
    def license_type(self) -> str:
        if not self.payload:
            return "-"
        return str(self.payload.get("license_type", "-"))

    @property
    def expires_at(self) -> str:
        if not self.payload:
            return "-"
        return str(self.payload.get("expires_at", "-"))


class LicenseManager:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or license_path()

    def validate(self) -> LicenseStatus:
        if not self.path.exists():
            return LicenseStatus(False, f"License file not found: {self.path}", path=self.path)
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            payload = data.get("payload")
            signature = data.get("signature")
            if not isinstance(payload, dict) or not isinstance(signature, str):
                return LicenseStatus(False, "Invalid license file format", path=self.path)
            if not verify_signature(payload, signature):
                return LicenseStatus(False, "Invalid license signature", payload=payload, path=self.path)

            expected_machine = str(payload.get("machine_id", "")).strip().upper()
            current_machine = machine_id().upper()
            if expected_machine and expected_machine != current_machine:
                return LicenseStatus(False, "License is bound to a different PC", payload=payload, path=self.path)

            expires = _parse_dt(str(payload.get("expires_at")))
            now = _utc_now()
            if now > expires:
                return LicenseStatus(False, "License has expired", payload=payload, path=self.path)

            days_left = max(0, int((expires - now).total_seconds() // 86400))
            return LicenseStatus(True, "License valid", payload=payload, days_left=days_left, path=self.path)
        except Exception as exc:
            return LicenseStatus(False, f"License check failed: {exc}", path=self.path)


def create_license(customer: str, days: int, machine: str | None = None, license_type: str = "Demo", version: str = "2.x", modules: list[str] | None = None, output: Path | None = None) -> Path:
    now = _utc_now()
    payload = {
        "product": APP_NAME,
        "customer": customer,
        "license_type": license_type,
        "version": version,
        "issued_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + timedelta(days=int(days))).isoformat().replace("+00:00", "Z"),
        "machine_id": (machine or machine_id()).strip().upper(),
        "modules": modules or ["RS422", "Recorder", "Player", "Analyzer", "Export"],
        "serial": hashlib.sha1(f"{customer}|{now.isoformat()}|{machine or machine_id()}".encode("utf-8")).hexdigest()[:16].upper(),
    }
    lic = {"payload": payload, "signature": sign_payload(payload)}
    out = output or license_path()
    out.write_text(json.dumps(lic, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def main_cli() -> int:
    parser = argparse.ArgumentParser(description="MCS4 Monitor license utility")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("machine-id", help="Print current PC machine ID")

    p_create = sub.add_parser("create", help="Create a signed PC-bound license")
    p_create.add_argument("--customer", required=True)
    p_create.add_argument("--days", type=int, default=30)
    p_create.add_argument("--machine", default="current", help="Machine ID or 'current'")
    p_create.add_argument("--type", default="Demo")
    p_create.add_argument("--version", default="2.x")
    p_create.add_argument("--output", default=str(license_path()))

    sub.add_parser("check", help="Validate local license")

    args = parser.parse_args()
    if args.cmd == "machine-id":
        print(machine_id())
        return 0
    if args.cmd == "create":
        mid = machine_id() if args.machine.lower() == "current" else args.machine
        out = create_license(args.customer, args.days, mid, args.type, args.version, output=Path(args.output))
        print(f"License created: {out}")
        print(f"Customer: {args.customer}")
        print(f"Machine ID: {mid}")
        print(f"Valid for: {args.days} days")
        return 0
    if args.cmd == "check":
        st = LicenseManager().validate()
        print(st.reason)
        print(f"Path: {st.path}")
        print(f"Machine ID: {machine_id()}")
        if st.payload:
            print(json.dumps(st.payload, indent=2, ensure_ascii=False))
        return 0 if st.valid else 1
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main_cli())
