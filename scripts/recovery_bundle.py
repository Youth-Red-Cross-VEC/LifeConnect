"""Create or restore a paired LifeConnect recovery bundle. See docs/DISASTER_RECOVERY.md."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
from uuid import uuid4


class RecoveryError(Exception):
    pass


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def private_file(path):
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or
            getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
        raise RecoveryError("Unexpected file type or link. Inspect the private volume offline.")
    return info


def directory(path):
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        raise RecoveryError("Expected a private directory without links.")


def certificates(source, destination=None):
    """Fingerprint names, content and modification times. Preserve the retention clock."""
    directory(source)
    fingerprint = hashlib.sha256()
    count = 0
    if destination is not None:
        destination.mkdir(mode=0o700)
    for entry in sorted(source.iterdir(), key=lambda item: item.name):
        info = private_file(entry)
        if entry.name == ".gitkeep" or re.fullmatch(r"\.lc-cert-[A-Za-z0-9_-]+\.tmp", entry.name):
            continue
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,120}_[0-9]{8}_[0-9]{6}(?:_[0-9a-f]{8})?_certificate\.(png|txt)", entry.name):
            raise RecoveryError("Unrecognized certificate volume entry. Review before continuing.")
        if destination is not None:
            target = destination / entry.name
            with entry.open("rb") as reader, target.open("xb") as writer:
                shutil.copyfileobj(reader, writer)
            os.utime(target, ns=(info.st_atime_ns, info.st_mtime_ns))
        fingerprint.update(json.dumps([entry.name, info.st_mtime_ns, digest(entry)],
                                      separators=(",", ":")).encode() + b"\n")
        count += 1
    return {"count": count, "sha256": fingerprint.hexdigest()}


def pg(command, *args):
    # pg tool diagnostics may include row values, connection details or certificate filenames.
    result = subprocess.run([command, "--no-password", *args], stdin=subprocess.DEVNULL,
                            capture_output=True, timeout=7200, check=False)
    if result.returncode:
        raise RecoveryError(f"{command} failed (exit {result.returncode}). Keep the attempt isolated.")
    return result.stdout.decode("utf-8").strip()


def revision(database):
    value = pg("psql", "-XAt", "-v", "ON_ERROR_STOP=1", "-d", database, "-c",
               "SELECT version_num FROM public.alembic_version")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", value):
        raise RecoveryError("Expected one LifeConnect Alembic revision.")
    return value


def database_defaults(database):
    # PG16 and later expose provider-specific locale fields under different names.
    value = pg("psql", "-XAt", "-v", "ON_ERROR_STOP=1", "-d", database, "-c",
               """SELECT json_build_array(pg_encoding_to_char(encoding), datcollate, datctype,
                      datlocprovider, coalesce(to_jsonb(d)->>'datlocale', to_jsonb(d)->>'daticulocale'),
                      to_jsonb(d)->>'daticurules', datcollversion)
                  FROM pg_database d WHERE datname=current_database()""")
    return json.loads(value)


def disjoint(first, second):
    first, second = first.resolve(), second.resolve()
    if first.is_relative_to(second) or second.is_relative_to(first):
        raise RecoveryError("Source and destination must be separate directory trees.")


def backup(args):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", args.database):
        raise RecoveryError("Pass a database name without credentials or connection options.")
    directory(args.certificates)
    disjoint(args.certificates, args.output)
    version = revision(args.database)
    args.output.mkdir(mode=0o700)  # Exclusive. Never reuse a prior attempt.
    dump = args.output / "database.dump"
    pg("pg_dump", "--format=custom", "--lock-wait-timeout=30s", "--file", str(dump), "-d", args.database)
    inventory = certificates(args.certificates, args.output / "certificates")
    if inventory != certificates(args.output / "certificates"):
        raise RecoveryError("Certificate copy failed verification.")
    metadata = {"format": 1, "revision": version, "database_defaults": database_defaults(args.database), "database_sha256": digest(dump), "certificates": inventory}
    # The manifest is the completion marker. A partial manifest fails verification.
    with (args.output / "manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(metadata, stream)
    print("Paired backup created. Verify a restore before accepting the recovery point.")


def restore(args):
    disjoint(args.bundle, args.output)
    directory(args.bundle)
    manifest = args.bundle / "manifest.json"
    if private_file(manifest).st_size > 4096:
        raise RecoveryError("Invalid recovery manifest.")
    metadata = json.loads(manifest.read_text(encoding="utf-8"))
    dump = args.bundle / "database.dump"
    private_file(dump)
    if (not isinstance(metadata, dict) or metadata.get("format") != 1
            or digest(dump) != metadata.get("database_sha256")
            or certificates(args.bundle / "certificates") != metadata.get("certificates")):
        raise RecoveryError("Bundle verification failed.")
    args.output.mkdir(mode=0o700)
    if certificates(args.bundle / "certificates", args.output / "certificates") != metadata["certificates"]:
        raise RecoveryError("Restored certificate verification failed.")
    name = "lc_recovery_" + uuid4().hex
    # Fail on any collision. The caller cannot select an existing database as restore target.
    pg("createdb", "--maintenance-db=postgres", "--template=template0", name)
    print(f"Created isolated recovery database {name}", flush=True)
    if database_defaults(name) != metadata.get("database_defaults"):
        raise RecoveryError("New recovery database has incompatible locale defaults.")
    pg("pg_restore", "--single-transaction", "--exit-on-error", "--no-owner", "--no-acl",
       "--no-tablespaces", "-d", name, str(dump))
    if revision(name) != metadata["revision"]:
        raise RecoveryError("Restored schema revision mismatch.")
    print("Paired restore verified. Keep application traffic and scheduled jobs disabled.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("backup")
    create.add_argument("--database", required=True)
    create.add_argument("--certificates", type=Path, required=True)
    create.add_argument("--output", type=Path, required=True)
    create.add_argument("--writers-stopped", required=True, action="store_true",
                        help="Confirm all database and certificate writers have drained and stopped")
    recover = commands.add_parser("restore")
    recover.add_argument("--bundle", type=Path, required=True)
    recover.add_argument("--output", type=Path, required=True)
    recover.add_argument("--isolated-cluster", required=True, action="store_true",
                         help="Confirm PGHOST and PGPORT identify a separate isolated recovery cluster")
    args = parser.parse_args()
    os.umask(0o077)
    try:
        if not all(os.environ.get(key) for key in ("PGHOST", "PGPORT", "PGUSER")):
            raise RecoveryError("Set PGHOST, PGPORT and PGUSER explicitly.")
        if args.command == "backup":
            backup(args)
        else:
            restore(args)
    except RecoveryError as exc:
        parser.exit(1, f"{exc}\n")
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, f"Recovery operation failed ({type(exc).__name__}). Inspect private storage and permissions.\n")


if __name__ == "__main__":
    main()
