# Linux Server Hardening Audit

I built a read-only Python audit for selected SSH settings and sensitive account-file permissions. It reports `PASS`, `WARN`, or `FAIL` findings with remediation guidance; it never runs privileged commands or changes system files.

## Run

```bash
python audit.py --root / --format text
python audit.py --root / --format json
```

Use `--root` to inspect a mounted Linux filesystem or a test fixture. The audit checks global `PermitRootLogin` and `PasswordAuthentication` settings before the first `Match` block, plus read permissions on `etc/shadow` and write permissions on `etc/passwd`.

This is a focused baseline check, not a complete security certification. It does not resolve SSH `Include` directives, inspect every service, or modify configuration. Review findings and apply changes manually through your normal change-control process.

Run tests with `python -m unittest discover -s tests -v`.
