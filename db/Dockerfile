FROM postgres:16

COPY init.sql /docker-entrypoint-initdb.d/
COPY init-postgres.sh /docker-entrypoint-initdb.d/
COPY init-pg-hba.sh /docker-entrypoint-initdb.d/
RUN chmod +x /docker-entrypoint-initdb.d/*.sh

ENV DB_REPL_USER=replicator
ENV DB_REPL_PASSWORD=NewPassword123
ENV POSTGRES_PASSWORD=NewPassword123

RUN mkdir -p /oracle/pg_data/archive /var/lib/postgresql/data /var/lib/postgresql/data/pg_log && \
    chown -R postgres:postgres /oracle/pg_data /var/lib/postgresql && \
    chmod 700 /var/lib/postgresql/data && \
    chmod 700 /var/lib/postgresql/data/pg_log

CMD ["postgres", "-c", "config_file=/var/lib/postgresql/data/postgresql.conf"]
