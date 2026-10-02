import argparse
import json
import stat
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    check: str
    status: str
    detail: str
    recommendation: str


def read_global_ssh_options(path: Path) -> dict[str, str]:
    options: dict[str, str] = {}
    if not path.is_file():
        return options
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        key = parts[0].lower()
        if key == "match":
            break
        if len(parts) == 2:
            options.setdefault(key, parts[1].split("#", 1)[0].strip().lower())
    return options


def audit_root(root: str | Path) -> list[Finding]:
    base = Path(root).expanduser()
    ssh_path = base / "etc" / "ssh" / "sshd_config"
    findings: list[Finding] = []
    if not ssh_path.is_file():
        findings.append(Finding("sshd_config", "WARN", "Configuration file was not found in the audit root.", "Provide the correct system root or inspect the host manually."))
    else:
        options = read_global_ssh_options(ssh_path)
        expected = {
            "permitrootlogin": ("no", "Set PermitRootLogin no unless a documented exception is required."),
            "passwordauthentication": ("no", "Prefer key-based authentication and set PasswordAuthentication no."),
        }
        for key, (secure_value, recommendation) in expected.items():
            actual = options.get(key)
            label = "PermitRootLogin" if key == "permitrootlogin" else "PasswordAuthentication"
            if actual is None:
                findings.append(Finding(label, "WARN", "No explicit global value was found before any Match block.", recommendation))
            elif actual == secure_value:
                findings.append(Finding(label, "PASS", f"Configured as {actual}.", "No action required."))
            else:
                findings.append(Finding(label, "FAIL", f"Configured as {actual}.", recommendation))

    checks = [
        ("etc/shadow", 0o044, "shadow_permissions", "Remove group/other read permissions from /etc/shadow."),
        ("etc/passwd", 0o022, "passwd_permissions", "Remove group/other write permissions from /etc/passwd."),
    ]
    for relative, forbidden_bits, name, recommendation in checks:
        target = base / Path(relative)
        if not target.is_file():
            findings.append(Finding(name, "WARN", f"{relative} was not found in the audit root.", "Provide the correct system root or inspect the host manually."))
            continue
        mode = stat.S_IMODE(target.stat().st_mode)
        if mode & forbidden_bits:
            findings.append(Finding(name, "FAIL", f"{relative} has mode {mode:04o}.", recommendation))
        else:
            findings.append(Finding(name, "PASS", f"{relative} has mode {mode:04o}.", "No action required."))
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only Linux SSH and account-file configuration audit")
    parser.add_argument("--root", default="/", help="Root directory to inspect; files are never changed")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    findings = audit_root(args.root)
    if args.format == "json":
        print(json.dumps([asdict(item) for item in findings], indent=2))
    else:
        for item in findings:
            print(f"[{item.status}] {item.check}: {item.detail}\n  Recommendation: {item.recommendation}")
    raise SystemExit(1 if any(item.status == "FAIL" for item in findings) else 0)


if __name__ == "__main__":
    main()
