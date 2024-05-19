#!/bin/bash

echo "logging_collector = on" >> /var/lib/postgresql/data/postgresql.conf
echo "log_destination = 'stderr'" >> /var/lib/postgresql/data/postgresql.conf
echo "log_statement = 'all'" >> /var/lib/postgresql/data/postgresql.conf
echo "log_directory = 'pg_log'" >> /var/lib/postgresql/data/postgresql.conf

echo "wal_level = replica" >> /var/lib/postgresql/data/postgresql.conf
echo "archive_mode = on" >> /var/lib/postgresql/data/postgresql.conf
echo "archive_command = 'cp %p /oracle/pg_data/archive/%f'" >> /var/lib/postgresql/data/postgresql.conf
echo "max_wal_senders = 3" >> /var/lib/postgresql/data/postgresql.conf
echo "wal_keep_size = 16" >> /var/lib/postgresql/data/postgresql.conf
echo "hot_standby = on" >> /var/lib/postgresql/data/postgresql.conf

chmod 666 /var/lib/postgresql/data/postgresql.conf
