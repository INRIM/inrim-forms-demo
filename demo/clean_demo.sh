#!/usr/bin/env bash
# Pulizia completa della demo: ferma e rimuove TUTTI i container, volumi e
# immagini (mongo, keycloak, app, companion, web-client), i container orfani
# del progetto, gli .env generati nel checkout di service-app e i segreti
# locali (demo/.env.secrets) — cosi' la prossima demo/run_demo.sh up riparte
# identica a un checkout pulito.
#
# Diverso da "run_demo.sh reset" (che ferma solo cio' che e' definito nei
# compose correnti): questo rimuove anche eventuali container/volumi orfani
# rimasti da run precedenti con nomi/servizi diversi.
#
# Il checkout ./service-app NON viene toccato: e' codice, non stato della
# demo. Per buttarlo via: rm -rf service-app
#
# Uso: demo/clean_demo.sh [--keep-secrets]
set -euo pipefail

DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$DEMO_DIR")"
cd "$ROOT_DIR"
export DEMO_DIR

# demo/../service-app, cioe' la root di questo repo.
SERVICE_APP_DIR="${SERVICE_APP_DIR:-$ROOT_DIR/service-app}"
PROJECT=ozon-demo
BACKEND_COMPOSE="$SERVICE_APP_DIR/backend/docker-compose.yml"
CLIENT_COMPOSE="$SERVICE_APP_DIR/app/docker-compose.client.example.yml"
BACKEND_ENV="$SERVICE_APP_DIR/backend/.env"
CLIENT_ENV="$SERVICE_APP_DIR/app/.env"
SECRETS_FILE="$DEMO_DIR/.env.secrets"

KEEP_SECRETS=0
if [[ "${1:-}" == "--keep-secrets" ]]; then
    KEEP_SECRETS=1
fi

step() { printf '\n\033[1;36m==> %s\033[0m\n' "$1"; }

if [[ -f "$BACKEND_COMPOSE" && -f "$BACKEND_ENV" ]]; then
    step "Arresto e rimuovo web-client (container + volumi + immagini + orfani)"
    docker compose -p "$PROJECT" -f "$CLIENT_COMPOSE" --env-file "$CLIENT_ENV" \
        down -v --rmi all --remove-orphans 2>/dev/null || true

    step "Arresto e rimuovo backend (container + volumi + immagini + orfani)"
    docker compose -p "$PROJECT" -f "$BACKEND_COMPOSE" -f "$DEMO_DIR/docker-compose.demo.yml" \
        --env-file "$BACKEND_ENV" down -v --rmi all --remove-orphans 2>/dev/null || true
else
    step "Nessun compose/.env generato in $SERVICE_APP_DIR: pulisco solo per nome"
fi

step "Rimuovo eventuali container demo rimasti orfani per nome"
# I nomi arrivano dai template (dalla 3.0 i container_name sono variabili
# obbligatorie dei compose); i default coprono chi ha girato prima.
get_name() {  # file key default
    local val
    val="$(grep -E "^${2}=" "$1" 2>/dev/null | tail -1 | cut -d= -f2- || true)"
    printf '%s' "${val:-$3}"
}
docker rm -f \
    "$(get_name "$DEMO_DIR/.env.demo" OZON_ENV_APP_CONTAINER_NAME ozon-env-app)" \
    "$(get_name "$DEMO_DIR/.env.demo" OZON_ENV_APP_DB_CONTAINER_NAME ozon-env-app-db)" \
    "$(get_name "$DEMO_DIR/.env.demo" KEYCLOAK_CONTAINER_NAME ozon-env-keycloak)" \
    "$(get_name "$DEMO_DIR/.env.demo" OZON_MAIL_SENDER_CONTAINER_NAME ozon-env-mail-sender)" \
    "$(get_name "$DEMO_DIR/.env.demo" OZON_CALENDAR_SCHEDULER_CONTAINER_NAME ozon-env-calendar-scheduler)" \
    "$(get_name "$DEMO_DIR/.env.demo" OZON_IDENTITY_MANAGER_CONTAINER_NAME ozon-env-identity-manager)" \
    "$(get_name "$DEMO_DIR/.env.client-demo" OZON_APP_WEB_CONTAINER_NAME demo-web)" \
    2>/dev/null || true

step "Rimuovo i volumi del progetto rimasti orfani"
docker volume rm -f \
    "${PROJECT}_mdbdata" "${PROJECT}_plugins" "${PROJECT}_uploads" \
    "${PROJECT}_scheduler_data" "${PROJECT}_keycloak_data" 2>/dev/null || true

step "Rimuovo gli .env generati ($BACKEND_ENV, $CLIENT_ENV)"
rm -f "$BACKEND_ENV" "$CLIENT_ENV"

if [[ "$KEEP_SECRETS" -eq 1 ]]; then
    step "Tengo i segreti locali ($SECRETS_FILE) — --keep-secrets"
else
    step "Rimuovo i segreti locali ($SECRETS_FILE, rigenerati al prossimo run)"
    rm -f "$SECRETS_FILE"
fi

echo
echo "Demo pulita. Per ripartire da zero: demo/run_demo.sh up"
