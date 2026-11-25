#!/bin/bash
# Nạp v0.5 vào PostgreSQL tạm (dùng để kiểm tra). Tham số: các file SQL thêm (tùy chọn)
B=/usr/lib/postgresql/16/bin
su postgres -c "$B/pg_ctl -D /tmp/pg/data -o '-k /tmp/pg -p 5544 -h \"\"' -l /tmp/pg/log -w start" >/dev/null 2>&1
P="psql -h /tmp/pg -p 5544 -U postgres -d postgres"
$P -q -c "drop schema public cascade; create schema public;" >/dev/null 2>&1
cd "$(dirname "$0")"
$P -v ON_ERROR_STOP=1 -q -f schema.sql -f triggers_postgres.sql -f views_postgres.sql "${@/#/-f}" || exit 1
$P -tAc "select 'PostgreSQL OK: '||(select count(*) from information_schema.tables where table_schema='public' and table_type='BASE TABLE')||' bảng, '||(select count(*) from information_schema.views where table_schema='public')||' view, '||(select count(distinct trigger_name) from information_schema.triggers where trigger_schema='public')||' trigger'"
