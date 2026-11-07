import argparse
from getpass import getpass

from sqlalchemy import select

from evalworks.auth import hash_password
from evalworks.db import SessionLocal
from evalworks.models import User, Workspace


def create_admin(name: str, email: str) -> None:
    normalized_email = email.strip().casefold()
    password = getpass("Admin password (minimum 14 characters): ")
    confirmation = getpass("Confirm password: ")
    if len(password) < 14:
        raise SystemExit("Password must be at least 14 characters")
    if password != confirmation:
        raise SystemExit("Passwords do not match")
    with SessionLocal.begin() as db:
        if db.scalar(select(User.id).where(User.email == normalized_email)):
            raise SystemExit("An account with that email already exists")
        workspace = Workspace(name=name.strip())
        db.add(workspace)
        db.flush()
        db.add(
            User(
                workspace_id=workspace.id,
                email=normalized_email,
                password_hash=hash_password(password),
                role="admin",
                is_active=True,
            )
        )
    print(f"Created workspace and administrator {normalized_email}")


def reset_password(email: str, *, disable_mfa: bool = False, session_factory=SessionLocal) -> None:
    normalized_email = email.strip().casefold()
    password = getpass("New password (minimum 14 characters): ")
    confirmation = getpass("Confirm new password: ")
    if len(password) < 14:
        raise SystemExit("Password must be at least 14 characters")
    if password != confirmation:
        raise SystemExit("Passwords do not match")
    with session_factory.begin() as db:
        user = db.scalar(select(User).where(User.email == normalized_email))
        if not user:
            raise SystemExit("No account with that email exists")
        user.password_hash = hash_password(password)
        user.session_version += 1
        if disable_mfa:
            user.mfa_enabled = False
            user.mfa_secret_ciphertext = None
            user.mfa_recovery_hashes = []
    print(f"Password updated and existing sessions revoked for {normalized_email}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="evalworks")
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create-admin", help="Create a workspace and its first admin")
    create.add_argument("--workspace", required=True)
    create.add_argument("--email", required=True)
    reset = subparsers.add_parser("reset-password", help="Reset a user password from the host")
    reset.add_argument("--email", required=True)
    reset.add_argument(
        "--disable-mfa",
        action="store_true",
        help="Also disable MFA when the user has lost their authenticator and recovery codes",
    )
    args = parser.parse_args()
    if args.command == "create-admin":
        create_admin(args.workspace, args.email)
    elif args.command == "reset-password":
        reset_password(args.email, disable_mfa=args.disable_mfa)


if __name__ == "__main__":
    main()
