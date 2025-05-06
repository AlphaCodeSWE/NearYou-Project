FROM metabase/metabase:latest

# Copia l’entrypoint e rendilo eseguibile
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Copia le definizioni di cards e dashboard
COPY definitions /appsota/definitions

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
