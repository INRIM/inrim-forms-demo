#!/usr/bin/env bash
# Avvia (o ferma) lo stack demo completo: keycloak + mongo + ozon-env-app +
# companion services + web-client, col plugin "demo" montato in /plugins/demo.
#
# Questo repo contiene SOLO la demo: i compose del backend e del web-client
# stanno in INRIM/service-app (branch 3.0). Lo script se ne occupa da solo:
# clona in demo/../service-app (root del repo, gitignorato) se non c'e', lo
# aggiorna (fast-forward) se c'e'. Non scrive niente fuori dalla root del
# repo e non serve avere niente dello stack preinstallato.
#
# Uso:
#   demo/run_demo.sh up      installa (clone incluso) e avvia tutto  [default]
#   demo/run_demo.sh down    ferma e rimuove i container (i volumi restano)
#   demo/run_demo.sh reset   come down, ma cancella anche i volumi (mongo/keycloak)
#   demo/run_demo.sh status  stato dei container della demo
#
# Env override:
#   SERVICE_APP_DIR   checkout di service-app (default: demo/../service-app,
#                     cioe' nella root di questo repo)
#   SERVICE_APP_REPO  URL da clonare (default: https://github.com/INRIM/service-app.git)
#   SERVICE_APP_REF   branch/tag da clonare/aggiornare (default: 3.0)
set -euo pipefail

DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$DEMO_DIR")"
cd "$ROOT_DIR"
export DEMO_DIR   # i path dei volumi in docker-compose.demo.yml sono assoluti

# demo/../service-app, cioe' la root di questo repo. ROOT_DIR = dirname(DEMO_DIR).
SERVICE_APP_DIR="${SERVICE_APP_DIR:-$ROOT_DIR/service-app}"
SERVICE_APP_REPO="${SERVICE_APP_REPO:-https://github.com/INRIM/service-app.git}"
SERVICE_APP_REF="${SERVICE_APP_REF:-3.0}"

PROJECT=ozon-demo
BACKEND_COMPOSE="$SERVICE_APP_DIR/backend/docker-compose.yml"
CLIENT_COMPOSE="$SERVICE_APP_DIR/app/docker-compose.client.example.yml"
BACKEND_ENV="$SERVICE_APP_DIR/backend/.env"
CLIENT_ENV="$SERVICE_APP_DIR/app/.env"
SECRETS_FILE="$DEMO_DIR/.env.secrets"

step() { printf '\n\033[1;36m==> %s\033[0m\n' "$1"; }
die()  { printf '\033[1;31mErrore:\033[0m %s\n' "$1" >&2; exit 1; }

# --- helper env ---------------------------------------------------------
get_env_var() { grep -E "^${2}=" "$1" 2>/dev/null | tail -1 | cut -d= -f2- || true; }

set_env_var() {  # file key value
    local file="$1" key="$2" val="$3"
    touch "$file"
    if grep -qE "^${key}=" "$file"; then
        sed -i.bak -e "s|^${key}=.*|${key}=${val}|" "$file"
        rm -f "${file}.bak"
    else
        printf '%s=%s\n' "$key" "$val" >> "$file"
    fi
}

# I nomi container sono anche hostname sulla rete Docker: gli URL interni
# vanno riscritti in base ai nomi, altrimenti rinominare un container lascia
# MONGO_URL/SCHEDULER_RUN_BASE_URL/BACKEND_UPSTREAM a puntare nel vuoto
# ("Name or service not known").
host_of() {  # url_o_hostport -> hostname
    local v="${1#*://}"
    v="${v%%/*}"
    printf '%s' "${v%%:*}"
}

replace_host() {  # url_o_hostport nuovo_host -> stesso valore con host sostituito
    local value="$1" new_host="$2" scheme="" rest path=""
    if [[ "$value" == *"://"* ]]; then
        scheme="${value%%://*}://"
        value="${value#*://}"
    fi
    if [[ "$value" == */* ]]; then
        path="/${value#*/}"
        value="${value%%/*}"
    fi
    local port=""
    [[ "$value" == *:* ]] && port=":${value##*:}"
    printf '%s%s%s%s' "$scheme" "$new_host" "$port" "$path"
}

sync_host() {  # file key nuovo_host
    local file="$1" key="$2" new_host="$3" current
    current="$(get_env_var "$file" "$key")"
    [[ -z "$current" || -z "$new_host" ]] && return 0
    if [[ "$(host_of "$current")" != "$new_host" ]]; then
        set_env_var "$file" "$key" "$(replace_host "$current" "$new_host")"
    fi
}

ensure_secret() {  # key -> stampa il valore, generandolo/persistendolo se serve
    local key="$1" val
    val="$(get_env_var "$SECRETS_FILE" "$key")"
    if [[ -z "$val" || "$val" == __* ]]; then
        val="$(openssl rand -hex 16)"
        set_env_var "$SECRETS_FILE" "$key" "$val"
    fi
    printf '%s' "$val"
}

# --- prerequisiti e checkout di service-app -----------------------------
check_prereqs() {
    local missing=()
    for bin in git curl jq openssl docker; do
        command -v "$bin" >/dev/null 2>&1 || missing+=("$bin")
    done
    [[ ${#missing[@]} -eq 0 ]] || die "comandi mancanti: ${missing[*]}"
    docker compose version >/dev/null 2>&1 || die "serve 'docker compose' (plugin v2)"
    docker info >/dev/null 2>&1 || die "il demone Docker non risponde: avvia Docker Desktop"
}

ensure_service_app() {
    if [[ ! -e "$SERVICE_APP_DIR" ]]; then
        step "clono service-app ($SERVICE_APP_REF) in $SERVICE_APP_DIR"
        git clone --branch "$SERVICE_APP_REF" --single-branch \
            "$SERVICE_APP_REPO" "$SERVICE_APP_DIR"
    elif [[ -d "$SERVICE_APP_DIR/.git" ]]; then
        update_service_app
    fi
    # Il check e' sui file che servono davvero, non sul branch: chi punta
    # SERVICE_APP_DIR su un checkout suo (altro branch, altro remote) resta
    # padrone del suo.
    [[ -f "$BACKEND_COMPOSE" ]] || die "manca $BACKEND_COMPOSE — $SERVICE_APP_DIR non sembra un checkout di service-app (SERVICE_APP_DIR per puntarne un altro)"
    [[ -f "$CLIENT_COMPOSE" ]]  || die "manca $CLIENT_COMPOSE"
    echo "service-app: $SERVICE_APP_DIR ($(git -C "$SERVICE_APP_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'no git'))"
}

update_service_app() {
    # Aggiornamento best-effort: la demo non deve morire se non c'e' rete o
    # se il checkout e' stato modificato a mano. In quei casi si va avanti
    # con quello che c'e' gia' su disco.
    local branch
    branch="$(git -C "$SERVICE_APP_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"

    if [[ -n "$(git -C "$SERVICE_APP_DIR" status --porcelain 2>/dev/null)" ]]; then
        echo "ATTENZIONE: $SERVICE_APP_DIR ha modifiche locali, salto l'aggiornamento" >&2
        return 0
    fi

    step "aggiorno service-app ($branch) in $SERVICE_APP_DIR"
    if ! git -C "$SERVICE_APP_DIR" fetch --quiet origin "$SERVICE_APP_REF" 2>/dev/null; then
        echo "ATTENZIONE: fetch di $SERVICE_APP_REF fallito (rete?), uso il checkout attuale" >&2
        return 0
    fi
    if [[ "$branch" != "$SERVICE_APP_REF" ]]; then
        echo "ATTENZIONE: $SERVICE_APP_DIR e' su '$branch', non su '$SERVICE_APP_REF': non faccio merge" >&2
        return 0
    fi
    if git -C "$SERVICE_APP_DIR" merge --ff-only FETCH_HEAD >/dev/null 2>&1; then
        echo "aggiornato a $(git -C "$SERVICE_APP_DIR" rev-parse --short HEAD)"
    else
        echo "ATTENZIONE: merge fast-forward non possibile (checkout divergente), uso il checkout attuale" >&2
    fi
}

diagnose_backend() {
    echo >&2
    echo "--- stato container del progetto $PROJECT ---" >&2
    compose_backend ps >&2 || true
    echo "--- ultime righe di log: app ---" >&2
    docker logs --tail 25 "$(get_env_var "$BACKEND_ENV" OZON_ENV_APP_CONTAINER_NAME)" 2>&1 | tail -25 >&2 || true
    echo "--- ultime righe di log: db ---" >&2
    local db_log
    db_log="$(docker logs --tail 10 "$(get_env_var "$BACKEND_ENV" OZON_ENV_APP_DB_CONTAINER_NAME)" 2>&1 | tail -10 || true)"
    echo "$db_log" >&2
    if [[ "$db_log" == *"known incompatibility"* ]]; then
        echo >&2
        echo "CAUSA PROBABILE: mongod non parte sul kernel di questa VM Docker (>= 6.19, SERVER-121912)." >&2
        echo "  Rimedio: scommenta OZON_ENV_APP_DB_IMAGE=mongo:8.2 in demo/.env.demo," >&2
        echo "  poi demo/clean_demo.sh && demo/run_demo.sh up" >&2
    fi
    echo >&2
}

compose_backend() { docker compose -p "$PROJECT" -f "$BACKEND_COMPOSE" -f "$DEMO_DIR/docker-compose.demo.yml" --env-file "$BACKEND_ENV" "$@"; }
compose_client()  { docker compose -p "$PROJECT" -f "$CLIENT_COMPOSE" --env-file "$CLIENT_ENV" "$@"; }

# --- comandi ------------------------------------------------------------
cmd="${1:-up}"

case "$cmd" in
    down|reset)
        check_prereqs
        [[ -f "$BACKEND_ENV" ]] || die "manca $BACKEND_ENV: lo stack non e' mai stato avviato (demo/run_demo.sh up)"
        step "Arresto web-client"
        compose_client down 2>/dev/null || true
        step "Arresto backend stack"
        if [[ "$cmd" == "reset" ]]; then
            compose_backend down -v
        else
            compose_backend down
        fi
        echo "Fatto."
        exit 0
        ;;
    status)
        [[ -f "$BACKEND_ENV" ]] || die "manca $BACKEND_ENV: lo stack non e' mai stato avviato (demo/run_demo.sh up)"
        compose_backend ps
        # il compose del client dichiara ozon-network external: se il backend
        # e' giu' la rete non c'e' e "ps" esce in errore — non e' fatale qui.
        compose_client ps || true
        exit 0
        ;;
    up) ;;
    *)  echo "Uso: $0 [up|down|reset|status]" >&2; exit 1 ;;
esac

step "1/8 prerequisiti"
check_prereqs

step "2/8 checkout di service-app (clone se manca, pull se c'e' gia')"
ensure_service_app

step "3/8 genero $BACKEND_ENV e $CLIENT_ENV dai template demo"
# I segreti locali vivono in demo/.env.secrets (gitignorato) e vengono
# riusati a ogni run: il volume mongo e quello di keycloak sono gia'
# inizializzati con quelle credenziali, rigenerarle romperebbe il login.
# Segreti e volumi vivono insieme: se MONGO_PASS va rigenerato ma il volume
# mongo del progetto e' ancora li', e' stato inizializzato con la password
# vecchia e l'app non riuscirebbe piu' a connettersi (errore opaco).
if [[ -z "$(get_env_var "$SECRETS_FILE" MONGO_PASS)" ]] \
   && docker volume inspect "${PROJECT}_mdbdata" >/dev/null 2>&1; then
    die "manca demo/.env.secrets ma il volume ${PROJECT}_mdbdata esiste: e' stato inizializzato con credenziali che non ho piu'. Esegui demo/clean_demo.sh con Docker avviato, oppure 'docker volume rm ${PROJECT}_mdbdata'"
fi

cp "$DEMO_DIR/.env.demo" "$BACKEND_ENV"
for key in MONGO_PASS SESSION_SECRET KEYCLOAK_ADMIN_PASSWORD; do
    set_env_var "$BACKEND_ENV" "$key" "$(ensure_secret "$key")"
done
for key in KEYCLOAK_CLIENT_SECRET OZON_M2M_CLIENT_SECRET; do
    val="$(get_env_var "$SECRETS_FILE" "$key")"
    if [[ -n "$val" ]]; then
        set_env_var "$BACKEND_ENV" "$key" "$val"
    fi
done
cp "$DEMO_DIR/.env.client-demo" "$CLIENT_ENV"

# Unica fonte di verita' per gli hostname interni: i nomi container.
APP_CONTAINER="$(get_env_var "$BACKEND_ENV" OZON_ENV_APP_CONTAINER_NAME)"
APP_CONTAINER="${APP_CONTAINER:-ozon-env-app}"
DB_CONTAINER="$(get_env_var "$BACKEND_ENV" OZON_ENV_APP_DB_CONTAINER_NAME)"
DB_CONTAINER="${DB_CONTAINER:-ozon-env-app-db}"
KC_CONTAINER="$(get_env_var "$BACKEND_ENV" KEYCLOAK_CONTAINER_NAME)"
KC_CONTAINER="${KC_CONTAINER:-keycloak}"

sync_host "$BACKEND_ENV" MONGO_URL "$DB_CONTAINER"
sync_host "$BACKEND_ENV" SCHEDULER_RUN_BASE_URL "$APP_CONTAINER"
sync_host "$CLIENT_ENV"  BACKEND_UPSTREAM "$APP_CONTAINER"
echo "hostname interni: mongo=$(get_env_var "$BACKEND_ENV" MONGO_URL) backend=$(get_env_var "$CLIENT_ENV" BACKEND_UPSTREAM)"

mkdir -p "$DEMO_DIR/models"

step "4/8 avvio backend (keycloak + db + app + companion services)"
compose_backend up -d

# shellcheck disable=SC1091
set -a; source "$BACKEND_ENV"; set +a

step "5/8 attendo Keycloak (${KEYCLOAK_SERVER_URL})"
for i in $(seq 1 60); do
    if curl -fs -o /dev/null "${KEYCLOAK_SERVER_URL}/realms/master"; then
        break
    fi
    [[ $i -eq 60 ]] && die "Keycloak non risponde dopo 60 tentativi"
    sleep 2
done
echo "Keycloak pronto."

step "6/8 provisioning Keycloak (realm/client web + client M2M condiviso + utenti demo)"
# shellcheck disable=SC1091
set -a; source "$CLIENT_ENV"; set +a
PROVISION_OUT="$("$DEMO_DIR/provision_keycloak.sh")"
echo "$PROVISION_OUT" >&2
SECRET="$(echo "$PROVISION_OUT" | grep '^KEYCLOAK_CLIENT_SECRET=' | cut -d= -f2-)"
M2M_SECRET="$(echo "$PROVISION_OUT" | grep '^OZON_M2M_CLIENT_SECRET=' | cut -d= -f2-)"
[[ -n "$SECRET" && -n "$M2M_SECRET" ]] || die "provisioning Keycloak senza secret in output"

# I secret vanno solo nel .env generato e in demo/.env.secrets (gitignorato),
# mai nel template demo/.env.demo che e' versionato.
for pair in "KEYCLOAK_CLIENT_SECRET=$SECRET" "OZON_M2M_CLIENT_SECRET=$M2M_SECRET"; do
    set_env_var "$BACKEND_ENV" "${pair%%=*}" "${pair#*=}"
    set_env_var "$SECRETS_FILE" "${pair%%=*}" "${pair#*=}"
done

step "7/8 riavvio app + calendar-scheduler coi secret aggiornati, poi bootstrap plugin e gruppi"
compose_backend up -d --force-recreate app calendar-scheduler

for i in $(seq 1 60); do
    if curl -fs -o /dev/null -w '%{http_code}' "http://localhost:${OZON_APP_PORT:-7999}/login" | grep -q 302; then
        break
    fi
    [[ $i -eq 60 ]] && { diagnose_backend; die "backend non risponde dopo 60 tentativi su http://localhost:${OZON_APP_PORT:-7999}/login"; }
    sleep 2
done
echo "Backend pronto."

# bootstrap plugin + gruppi demo (admin M2M, user/operator/manager).
# Il nome del container arriva dal .env generato: dalla 3.0 i container_name
# dei compose sono variabili obbligatorie, niente piu' nomi fissi.
APP_CONTAINER="${OZON_ENV_APP_CONTAINER_NAME:-ozon-env-app}"
docker exec "$APP_CONTAINER" uv run python bootstrap.py --admin admin
docker cp "$DEMO_DIR/seed_groups.py" "$APP_CONTAINER:/app/seed_groups.py"
docker exec "$APP_CONTAINER" uv run python seed_groups.py

step "8/8 avvio web-client"
# --force-recreate: nginx risolve l'IP di "app" all'avvio e non lo aggiorna;
# se app e' stato ricreato allo step 7/8 con web-client gia' su, serve un
# riavvio anche qui altrimenti nginx resta agganciato all'IP vecchio (502).
compose_client up -d --force-recreate

step "Demo pronta"
cat <<EOF

  Web app:   ${SITE_URL:-http://localhost:4200}
  Keycloak:  ${KEYCLOAK_SERVER_URL} (admin / ${KEYCLOAK_ADMIN_PASSWORD})
  Backend:   http://localhost:${OZON_APP_PORT:-7999}

  Utenti demo (username = password): admin, user, operator, manager
  Segreti locali generati: demo/.env.secrets (gitignorato, non cancellarlo
  se vuoi riavviare la demo sugli stessi volumi)

  Stato: demo/run_demo.sh status
  Stop:  demo/run_demo.sh down
  Reset: demo/run_demo.sh reset   (cancella anche i dati mongo/keycloak)
EOF
