"""Provision or reset an application account with a database-stored password hash."""
from __future__ import annotations

import argparse
import getpass
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.services.password_service import hash_password
from seed.demo_data import USERS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("user_id", help="Account ID, such as alice")
    parser.add_argument("--name", help="Display name; defaults to the synthetic demo profile")
    parser.add_argument("--role", choices=("employee", "manager", "hr_payroll", "hr_partner"))
    parser.add_argument("--department")
    parser.add_argument("--label")
    parser.add_argument("--password-stdin", action="store_true", help="Read one password line from standard input")
    parser.add_argument("--via-container", action="store_true", help="Provision through the running local PostgreSQL container")
    parser.add_argument("--generate-password", action="store_true", help="Generate and print a random password instead of prompting")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", args.user_id):
        parser.error("user_id must contain 1–128 letters, digits, underscores, or hyphens")
    defaults = USERS.get(args.user_id, {})
    name = args.name or defaults.get("name")
    role = args.role or defaults.get("role")
    department = args.department or defaults.get("department")
    label = args.label or defaults.get("label") or role
    if not all((name, role, department, label)):
        parser.error("New accounts require --name, --role, and --department")
    if args.generate_password and args.password_stdin:
        parser.error("Choose either --generate-password or --password-stdin")
    password = secrets.token_urlsafe(24) if args.generate_password else (sys.stdin.readline().rstrip("\r\n") if args.password_stdin else getpass.getpass("Password: "))
    if not 8 <= len(password) <= 1024:
        parser.error("Password must contain 8–1024 characters")
    password_hash = hash_password(password)
    if args.via_container:
        compose_file = Path(__file__).resolve().parents[1] / "docker-compose.pgvector.yml"
        variables = {"user_id": args.user_id, "name": name, "role": role, "department": department, "label": label, "password_hash": password_hash}
        command = ["docker", "compose", "-f", str(compose_file), "exec", "-T", "postgres", "psql", "-U", "postgres", "-d", "peoplevault", "-v", "ON_ERROR_STOP=1"]
        for key, value in variables.items():
            command.extend(("-v", f"{key}={value}"))
        sql = """INSERT INTO app_users (user_id, name, role, department, label, password_hash)
VALUES (:'user_id', :'name', :'role', :'department', :'label', :'password_hash')
ON CONFLICT (user_id) DO UPDATE SET
  name = EXCLUDED.name, role = EXCLUDED.role, department = EXCLUDED.department,
  label = EXCLUDED.label, password_hash = EXCLUDED.password_hash,
  active = true, updated_at = now();
"""
        subprocess.run(command, input=sql, text=True, check=True)
        print(f"Account {args.user_id} saved with a password hash.")
        if args.generate_password: print(f"Generated password for {args.user_id}: {password}")
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    except ImportError:
        pass
    db_password = os.environ.get("POSTGRES_PASSWORD")
    if not db_password:
        parser.error("POSTGRES_PASSWORD is required to provision accounts")
    import psycopg

    host = os.environ.get("PGVECTOR_DATABASE_HOST", "127.0.0.1")
    port = os.environ.get("PGVECTOR_DATABASE_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "peoplevault")
    url = f"postgresql://postgres:{quote(db_password, safe='')}@{host}:{port}/{quote(db, safe='')}"
    with psycopg.connect(url) as connection, connection.cursor() as cursor:
        cursor.execute(
            """INSERT INTO app_users (user_id, name, role, department, label, password_hash)
               VALUES (%s, %s, %s, %s, %s, %s)
               ON CONFLICT (user_id) DO UPDATE SET
                 name = EXCLUDED.name, role = EXCLUDED.role, department = EXCLUDED.department,
                 label = EXCLUDED.label, password_hash = EXCLUDED.password_hash,
                 active = true, updated_at = now()""",
            (args.user_id, name, role, department, label, password_hash),
        )
    print(f"Account {args.user_id} saved with a password hash.")
    if args.generate_password: print(f"Generated password for {args.user_id}: {password}")


if __name__ == "__main__":
    main()
