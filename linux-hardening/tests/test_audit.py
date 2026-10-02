import tempfile
import unittest
from pathlib import Path

from audit import audit_root, read_global_ssh_options


class LinuxAuditTests(unittest.TestCase):
    def test_reads_global_ssh_values_and_ignores_match_block(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sshd_config"
            path.write_text(
                "# PermitRootLogin yes\nPermitRootLogin no\nPasswordAuthentication no\n"
                "Match User legacy\n  PasswordAuthentication yes\n",
                encoding="utf-8",
            )
            options = read_global_ssh_options(path)
            self.assertEqual(options["permitrootlogin"], "no")
            self.assertEqual(options["passwordauthentication"], "no")

    def test_reports_unsafe_ssh_setting_without_changing_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ssh_path = root / "etc" / "ssh" / "sshd_config"
            ssh_path.parent.mkdir(parents=True)
            original = "PermitRootLogin yes\nPasswordAuthentication no\n"
            ssh_path.write_text(original, encoding="utf-8")
            findings = audit_root(root)
            root_login = next(item for item in findings if item.check == "PermitRootLogin")
            self.assertEqual(root_login.status, "FAIL")
            self.assertEqual(ssh_path.read_text(encoding="utf-8"), original)

    def test_missing_files_are_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            findings = audit_root(directory)
            self.assertTrue(findings)
            self.assertTrue(all(item.status == "WARN" for item in findings))


if __name__ == "__main__":
    unittest.main()
