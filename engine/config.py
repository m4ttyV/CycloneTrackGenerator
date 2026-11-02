"""Read the legacy positional connection config without changing its format."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConnectionConfig:
    db_host: str
    db_port: str
    db_name: str
    db_user: str
    db_password: str
    smb_host: str
    smb_username: str
    smb_password: str
    smb_share: str


def load_config(path: str = "confing.conf") -> ConnectionConfig:
    """Read up to nine non-empty lines in the historical field order.

    The filename and current-working-directory lookup intentionally match the
    existing CLI. Configuration should not be committed to version control.
    """
    values = [line for line in Path(path).read_text(encoding="utf-8").splitlines() if line]
    if len(values) < 5:
        raise ValueError(f"Expected at least five database settings in {path}")
    values = (values + [""] * 9)[:9]
    return ConnectionConfig(*values)
