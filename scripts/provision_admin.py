#!/usr/bin/env python3
"""Provision, update, or disable administrator accounts in the configured database."""

import argparse
import getpass
import re
import sys

from sqlalchemy.exc import IntegrityError

from app import database
from app.auth import hash_password
from app.models import AdminSession, AdminUser


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    create = commands.add_parser("create", help="create an administrator account")
    create.add_argument("username")
    reset = commands.add_parser("set-password", help="change an account password")
    reset.add_argument("username")
    disable = commands.add_parser(
        "disable", help="disable an account and revoke sessions"
    )
    disable.add_argument("username")
    args = parser.parse_args()

    username = args.username.strip().casefold()
    if not re.fullmatch(r"[a-z0-9._@-]{1,100}", username):
        parser.error(
            "username may contain only letters, numbers, '.', '_', '@', and '-'"
        )

    database.create_tables()
    db = database.SessionLocal()
    try:
        if args.action in {"create", "set-password"}:
            password = getpass.getpass("New administrator password (12+ characters): ")
            confirmation = getpass.getpass("Confirm administrator password: ")
            if password != confirmation:
                print("Passwords do not match.", file=sys.stderr)
                return 1
            try:
                password_hash = hash_password(password)
            except ValueError as error:
                print(str(error), file=sys.stderr)
                return 1
            if args.action == "create":
                db.add(
                    AdminUser(
                        username=username, password_hash=password_hash, role="admin"
                    )
                )
                try:
                    db.commit()
                except IntegrityError:
                    db.rollback()
                    print("That account already exists.", file=sys.stderr)
                    return 1
                print(f"Administrator account {username!r} created.")
                return 0

            user = db.query(AdminUser).filter(AdminUser.username == username).first()
            if user is None:
                print("Account not found.", file=sys.stderr)
                return 1
            user.password_hash = password_hash
            db.query(AdminSession).filter(AdminSession.user_id == user.id).delete()
            db.commit()
            print(f"Password updated and sessions revoked for {username!r}.")
            return 0

        user = db.query(AdminUser).filter(AdminUser.username == username).first()
        if user is None:
            print("Account not found.", file=sys.stderr)
            return 1
        user.is_active = False
        db.query(AdminSession).filter(AdminSession.user_id == user.id).delete()
        db.commit()
        print(f"Account {username!r} disabled and its sessions revoked.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
