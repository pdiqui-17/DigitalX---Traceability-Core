"""dbtools.py — kết nối dùng chung cho run_scenarios.py và smoke_test.py.

- SQLite: CSDL trong bộ nhớ, nạp schema + trigger + view.
- PostgreSQL: chạy qua `psql` (không cần cài thư viện Python). Đọc cấu hình từ
  db/.env (xem db/.env.example). Database kiểm thử bị XÓA và TẠO LẠI mỗi lần chạy,
  nên tên bắt buộc kết thúc bằng "_test".
- Log: setup_log(path) ghi toàn bộ output ra file UTF-8 (tránh lỗi font khi
  chuyển hướng bằng PowerShell).

Chạy riêng để kiểm tra kết nối PostgreSQL:
    python dbtools.py
"""
import os, sys, glob, shutil, sqlite3, subprocess, pathlib

HERE = pathlib.Path(__file__).parent
SEP_FIELD = "|#|"          # dấu phân cách cột trong output psql (ASCII, hiếm gặp)
NULL_MARK = "<<NULL>>"     # đánh dấu NULL để phân biệt với chuỗi rỗng


class DBError(Exception):
    pass


# ───────────────────────────── output / log ─────────────────────────────
class _Tee:
    def __init__(self, *streams):
        self.streams = streams
    def write(self, s):
        for st in self.streams:
            st.write(s)
    def flush(self):
        for st in self.streams:
            st.flush()


def setup_output(argv):
    """Bật UTF-8 cho console; nếu có `--log <file>` thì ghi thêm ra file UTF-8.
    Trả về argv đã bỏ phần --log."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    argv = list(argv)
    if "--log" in argv:
        i = argv.index("--log")
        if i + 1 >= len(argv):
            sys.exit("Thiếu tên file sau --log")
        path = pathlib.Path(argv[i + 1])
        path.parent.mkdir(parents=True, exist_ok=True)
        f = open(path, "w", encoding="utf-8", newline="\n")
        sys.stdout = _Tee(sys.stdout, f)
        sys.stderr = _Tee(sys.stderr, f)
        del argv[i:i + 2]
    return argv


# ───────────────────────────── SQLite ─────────────────────────────
class SQLite:
    name = "sqlite"

    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys = ON")
        for f in ("schema.sql", "triggers_sqlite.sql", "views_sqlite.sql"):
            self.db.executescript((HERE / f).read_text(encoding="utf-8"))

    def load(self, path):
        self.db.executescript(pathlib.Path(path).read_text(encoding="utf-8"))

    def query(self, sql):
        """Trả (cột, dòng)."""
        try:
            cur = self.db.execute(sql)
            cols = [d[0] for d in cur.description] if cur.description else []
            return cols, [tuple(r) for r in cur.fetchall()]
        except (sqlite3.IntegrityError, sqlite3.OperationalError) as e:
            raise DBError(str(e))

    def run(self, sql):
        return self.query(sql)[1]

    def tables(self):
        return {r[0] for r in self.run("SELECT name FROM sqlite_master WHERE type='table'")}


# ───────────────────────────── PostgreSQL ─────────────────────────────
def load_env():
    """Đọc db/.env (KEY=VALUE). Biến môi trường đã đặt sẵn được ưu tiên."""
    env = dict(os.environ)
    p = HERE / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if v and not os.environ.get(k):
                env[k] = v
    env.setdefault("PGDATABASE", "traceability_test")
    env["PGCLIENTENCODING"] = "UTF8"
    return env


def find_psql(env):
    cand = env.get("PSQL") or shutil.which("psql")
    if cand and (pathlib.Path(cand).exists() or shutil.which(cand)):
        return cand
    hits = sorted(glob.glob("C:/Program Files/PostgreSQL/*/bin/psql.exe"))
    if hits:
        return hits[-1]
    sys.exit("Không tìm thấy psql. Đặt PSQL=<đường dẫn psql> trong db/.env")


class Postgres:
    """convert_numbers=True: chuỗi số trả về được đổi sang int/float (giống SQLite).
    smoke_test giữ False để so sánh như cũ."""
    name = "postgres"

    def __init__(self, convert_numbers=False):
        self.env = load_env()
        self.psql = find_psql(self.env)
        self.convert = convert_numbers
        self.dbname = self.env["PGDATABASE"]
        if not self.dbname.endswith("_test"):
            sys.exit(f"PGDATABASE='{self.dbname}' phải kết thúc bằng '_test' "
                     "(database này bị xóa và tạo lại mỗi lần chạy).")
        maint = self.env.get("PGMAINTDB", "postgres")
        self._psql(maint, f'DROP DATABASE IF EXISTS "{self.dbname}"')
        self._psql(maint, f"CREATE DATABASE \"{self.dbname}\" ENCODING 'UTF8' TEMPLATE template0")
        for f in ("schema.sql", "triggers_postgres.sql", "views_postgres.sql"):
            self.load(HERE / f)

    def _psql(self, dbname, sql=None, file=None):
        cmd = [self.psql, "-X", "-q", "-v", "ON_ERROR_STOP=1", "-d", dbname,
               "-tA", "-F", SEP_FIELD, "-P", f"null={NULL_MARK}"]
        if file:
            cmd += ["-f", str(file)]
        r = subprocess.run(cmd, input=sql, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=self.env)
        if r.returncode != 0:
            msg = r.stderr.strip()
            if "password authentication failed" in msg or "no password supplied" in msg:
                sys.exit("PostgreSQL từ chối đăng nhập — kiểm tra PGUSER/PGPASSWORD trong db/.env")
            if "could not connect" in msg or "Connection refused" in msg:
                sys.exit("Không kết nối được PostgreSQL — kiểm tra PGHOST/PGPORT và dịch vụ đang chạy\n" + msg)
            raise DBError(msg)
        return r.stdout

    def load(self, path):
        try:
            self._psql(self.dbname, file=path)
        except DBError as e:
            sys.exit(f"Lỗi khi nạp {pathlib.Path(path).name} vào PostgreSQL:\n{e}")

    def _value(self, v):
        if v == NULL_MARK:
            return None
        if self.convert:
            try:
                return int(v)
            except ValueError:
                try:
                    return float(v)
                except ValueError:
                    return v
        return v

    def run(self, sql):
        out = self._psql(self.dbname, sql)
        return [tuple(self._value(v) for v in line.split(SEP_FIELD))
                for line in out.splitlines() if line != ""]

    def query(self, sql):
        """Trả (cột, dòng). Tên cột chỉ dùng để hiển thị ở chế độ --raw."""
        rows = self.run(sql)
        cols = []
        body = sql.strip().rstrip(";")
        if body.upper().startswith(("SELECT", "WITH")):
            try:
                cmd = [self.psql, "-X", "-q", "-d", self.dbname, "-A", "-F", SEP_FIELD,
                       "-P", "footer=off"]
                r = subprocess.run(cmd, input=f"SELECT * FROM ({body}) _q LIMIT 0",
                                   capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", env=self.env)
                first = r.stdout.splitlines()[0] if r.returncode == 0 and r.stdout else ""
                cols = first.split(SEP_FIELD) if first else []
            except (OSError, IndexError):
                cols = []
        return cols, rows

    def tables(self):
        return {r[0] for r in self.run(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")}


def connect(dialect, convert_numbers=False):
    if dialect in ("sqlite", None):
        return SQLite()
    if dialect in ("postgres", "pg", "postgresql"):
        return Postgres(convert_numbers=convert_numbers)
    sys.exit(f"Không rõ hệ CSDL '{dialect}' (dùng sqlite hoặc postgres)")


if __name__ == "__main__":
    setup_output(sys.argv)
    pg = Postgres()
    n = pg.run("SELECT (SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'),"
               " (SELECT count(*) FROM information_schema.views WHERE table_schema='public'),"
               " (SELECT count(DISTINCT trigger_name) FROM information_schema.triggers WHERE trigger_schema='public')")[0]
    print(f"PostgreSQL OK ({pg.dbname}): {n[0]} bảng, {n[1]} view, {n[2]} trigger")
