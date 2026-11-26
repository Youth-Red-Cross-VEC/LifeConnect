"""Exercise the operator CLI with two clusters created solely for this test."""
import asyncio
from contextlib import contextmanager
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.models.audit import AdminAuditLog
from app.models.privacy import ErasureFile
from tests.helpers import insert_admin, insert_donor, insert_request
from tests.test_migrations import _run_alembic

ROOT = Path(__file__).resolve().parents[1]
CLI = [sys.executable, str(ROOT / "scripts/recovery_bundle.py")]


def invoke(argv, env, success=True):
    result = subprocess.run(argv, env=env, cwd=ROOT, capture_output=True, text=True, timeout=120)
    if success:
        assert result.returncode == 0, f"Isolated {Path(argv[0]).name} failed (exit {result.returncode})"
    else:
        assert result.returncode != 0
    return result.stdout


@contextmanager
def cluster(folder):
    if not shutil.which("initdb"):
        pytest.skip("PostgreSQL server and client tools are required on PATH")
    folder.mkdir()
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = {k: v for k, v in os.environ.items() if not k.startswith("PG")}
    env.update(PGHOST="127.0.0.1", PGPORT=str(port), PGUSER="dr_test", PGPASSWORD=secrets.token_hex(24))
    pwfile = folder / "init.key"
    pwfile.write_text(env["PGPASSWORD"], encoding="ascii")
    data = str(folder / "pgdata")
    try:
        invoke(["initdb", "-D", data, "-U", env["PGUSER"], "--auth=scram-sha-256",
                "--encoding=UTF8", "--locale=C", "--pwfile", str(pwfile)], env)
    finally:
        pwfile.unlink()
    # A Windows postmaster can inherit pg_ctl's capture pipes and keep the test blocked.
    subprocess.run(["pg_ctl", "-D", data, "-l", str(folder / "server.log"), "-o",
                    f"-h 127.0.0.1 -p {port}", "-w", "start"], env=env, check=True,
                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
    try:
        yield env
    finally:
        invoke(["pg_ctl", "-D", data, "-m", "fast", "-w", "stop"], env)


def sql(env, database, statement, success=True):
    return invoke(["psql", "-XAt", "-v", "ON_ERROR_STOP=1", "-d", database, "-c", statement], env, success).strip()


def test_paired_backup_and_restore(tmp_path):
    files = tmp_path / "source-files"
    files.mkdir()
    name = f"lc-{uuid4().hex}_20261126_120000_certificate.txt"
    (files / name).write_bytes(b"Synthetic certificate")
    (files / ".lc-cert-unused.tmp").write_bytes(b"unfinished")
    os.utime(files / name, (1750000000, 1750000000))
    bundle = tmp_path / "bundle"
    target = tmp_path / "recovered"
    backup = [*CLI, "backup", "--writers-stopped", "--database", "source", "--certificates", str(files),
              "--output", str(bundle)]
    restore = [*CLI, "restore", "--isolated-cluster", "--bundle", str(bundle), "--output", str(target)]

    with cluster(tmp_path / "source-cluster") as source, cluster(tmp_path / "target-cluster") as dest:
        invoke(["createdb", "source"], source)
        url = (f"postgresql+asyncpg://dr_test:{source['PGPASSWORD']}@127.0.0.1:"
               f"{source['PGPORT']}/source")
        migration = _run_alembic(url, "upgrade", "head")
        assert migration.returncode == 0, "Disposable source migration failed"

        async def seed():
            engine = create_async_engine(url)
            try:
                async with async_sessionmaker(engine, expire_on_commit=False)() as session:
                    await insert_admin(session)
                    await insert_donor(session)
                    await insert_request(session)
                    session.add(AdminAuditLog(admin_id="ADM-1", action="certificate.generate",
                                              entity_type="certificate", entity_id=name, detail="donor_id=DON-1"))
                    session.add(ErasureFile(filename=name))
                    await session.commit()
            finally:
                await engine.dispose()
        asyncio.run(seed())
        invoke(backup, source)
        invoke(backup, source, success=False)
        output = invoke(restore, dest)
        database = re.search(r"lc_recovery_[0-9a-f]{32}", output).group()
        assert sql(dest, database, "SELECT version_num FROM alembic_version") == sql(source, "source", "SELECT version_num FROM alembic_version")
        assert sql(dest, database, """SELECT count(*) FROM blood_request_details b
            JOIN hospital_details h ON b.hospital_id=h.id JOIN response_details r ON b.response_id=r.id""") == "1"
        assert sql(dest, database, """SELECT count(*) FROM admin_audit_log a JOIN admin_details u ON a.admin_id=u.id
            JOIN erasure_files e ON e.filename=a.entity_id JOIN donor_details d ON a.detail='donor_id=' || d.id""") == "1"
        sql(dest, database, "UPDATE blood_request_details SET hospital_id='absent'", success=False)
        assert sql(dest, database, "SELECT count(*) FROM blood_request_details WHERE hospital_id='HOSP-1'") == "1"
        recovered = target / "certificates" / name
        assert recovered.read_bytes() == (files / name).read_bytes()
        assert recovered.stat().st_mtime_ns == (files / name).stat().st_mtime_ns
        assert len(list(recovered.parent.iterdir())) == 1
        invoke(restore, dest, success=False)

        # Tampered content is refused before a destination is allocated.
        restore[-1] = str(tmp_path / "rejected")
        (bundle / "certificates" / name).write_bytes(b"tampered")
        invoke(restore, dest, success=False)
        assert not Path(restore[-1]).exists()
        assert sql(dest, "postgres", "SELECT count(*) FROM pg_database WHERE datname LIKE 'lc_recovery_%'") == "1"
