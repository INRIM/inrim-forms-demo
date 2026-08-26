# Demo stack

Demo di [INRIM/service-app](https://github.com/INRIM/service-app) 3.0
(`ozon-env-app`: backend multi-tenant, plugin su `/plugins/<app_code>`,
autenticazione Keycloak). Il plugin `demo` porta la form "Modulo Dati Persona"
della vecchia 2.4
([`web-client/demo/demo`](https://github.com/INRIM/service-app/tree/2.4/web-client/demo/demo)).

Avvia in un colpo solo: Keycloak + Mongo + `ozon-env-app` (con companion
service) + web-client, con il plugin `demo` caricato e 4 utenti di test
(`admin`, `user`, `operator`, `manager`).

## Quickstart

```bash
demo/run_demo.sh up      # installa e avvia tutto (idempotente, ri-eseguibile)
demo/run_demo.sh status  # stato dei container
demo/run_demo.sh down    # ferma i container (i dati restano nei volumi)
demo/run_demo.sh reset   # ferma e cancella anche i dati (mongo/keycloak)
demo/clean_demo.sh       # pulizia totale: container/volumi/immagini/orfani +
                         # .env generati + segreti locali — riparti da un
                         # checkout pulito con demo/run_demo.sh up
```

Richiede Docker Desktop attivo piu' `git`, `curl`, `jq`, `openssl`
(`run_demo.sh` li verifica prima di toccare qualsiasi cosa).

### Cosa fa `run_demo.sh up`, in ordine

1. **prerequisiti** — binari presenti, `docker compose` v2, demone Docker su;
2. **checkout di service-app** — se `demo/../service-app` (root di questo
   repo, gitignorato) non esiste lo clona
   (`git clone --branch 3.0 --single-branch https://github.com/INRIM/service-app.git`);
   se esiste lo aggiorna con `fetch` + `merge --ff-only`. L'aggiornamento e'
   best-effort: con modifiche locali, senza rete, su un altro branch o con
   storia divergente si va avanti col checkout che c'e' su disco (avviso su
   stderr, nessun clobber). Poi verifica che ci siano
   `backend/docker-compose.yml` e `app/docker-compose.client.example.yml`.
   Override: `SERVICE_APP_DIR`, `SERVICE_APP_REPO`, `SERVICE_APP_REF`;
3. **env** — genera `service-app/backend/.env` e `service-app/app/.env` dai
   template `.env.demo` / `.env.client-demo`, sostituendo i segnaposto coi
   segreti locali (vedi sotto);
4. **up del backend** — `backend/docker-compose.yml` + `docker-compose.demo.yml`;
5. **attesa Keycloak**;
6. **provisioning Keycloak** — realm, client web, client M2M, utenti; i due
   client secret finiscono nel `.env` generato e in `demo/.env.secrets`;
7. **ricreazione `app` + `calendar-scheduler`** coi secret, poi `bootstrap.py`
   (plugin + admin) e `seed_groups.py` (gruppi);
8. **up del web-client**.

Al termine:

| Cosa | URL | Credenziali |
|---|---|---|
| Web app | http://localhost:4200 | vedi sotto |
| Backend API | http://localhost:7999 | — |
| Keycloak admin console | http://localhost:8082 | `admin` / password generata (stampata a fine run, salvata in `demo/.env.secrets`) |

Utenti demo (realm Keycloak `backend`), **username = password**:
`admin`, `user`, `operator`, `manager`. Sono mappati nei rispettivi gruppi
(`admin-demo`, `user-demo`, `operator-demo`, `manager-demo`) nella collection
`group_users` per `app_code=demo`.

## Cosa contiene questa cartella

```
demo/
├── plugin/
│   ├── config.json           manifest del plugin (module_name, schema, datas)
│   ├── schema/components.json  la form "Modulo Dati Persona" portata dalla 2.4
│   └── data/
│       ├── menu_group.json   card dashboard "Modulo Dati Persona"
│       └── action.json       le 6 action di default della form
├── .env.demo                 template env del backend (reso in ../service-app/backend/.env)
├── .env.client-demo          template env del web-client (reso in ../service-app/app/.env)
├── .env.secrets              segreti locali generati (gitignorato, creato al 1o run)
├── docker-compose.demo.yml   override: Keycloak + plugin/ in /plugins/demo
├── provision_keycloak.sh     realm + client web + client M2M calendar-scheduler
│                             + utenti Keycloak (idempotente)
├── seed_groups.py            aggiunge user/operator/manager ai gruppi group_users
│                             + il service account calendar-scheduler al gruppo admin
├── run_demo.sh               orchestratore: fa tutto quanto sopra in ordine
├── clean_demo.sh             pulizia totale
└── tests/                    test dello script di provisioning (unittest)
```

`docker-compose.demo.yml` e' l'unico override e fa due cose:

- **aggiunge Keycloak**: `backend/docker-compose.yml` di service-app 3.0
  dichiara il volume `keycloak_data` ma non il servizio; la demo gira in
  `AUTH_MODE=keycloak`, quindi l'IdP se lo porta dietro lei
  (`quay.io/keycloak/keycloak:26.0` in `start-dev`, H2 embedded — comodo per
  la demo, non per la produzione);
- **monta il plugin** in `/plugins/demo` e la cartella `models/` sui
  companion service.

I path dei volumi sono assoluti (`${DEMO_DIR}/...`, esportata da
`run_demo.sh`): la project directory di compose e' quella del *primo* `-f`,
cioe' `service-app/backend/`, quindi un path relativo finirebbe dentro il
checkout di service-app invece che qui.

Il resto (sorgente immagini, rete, porte) usa direttamente
`backend/docker-compose.yml` e `app/docker-compose.client.example.yml`, coi
default GHCR (nessun override `OZON_*_IMAGE` nei template `.env`).

## Come funziona il porting (per chi tocca il plugin)

Il nuovo `ozon-env-app` scopre i plugin guardando dentro `/plugins/<nome>/`:
se c'e' un `config.json` lo carica (vedi `app/plugins/__init__.py` +
`app/services/plugin_installer.py` nell'immagine `ozon-env-app`). Il manifest
minimo e':

```json
{
  "module_name": "demo",
  "schema": "/schema/components.json",
  "datas": [
    { "menu_group": "/data/menu_group.json" },
    { "action": "/data/action.json" }
  ],
  "depends": []
}
```

`schema` punta a un file di *component* (le form/i modelli, stesso formato
della 2.4) che viene upsertato nella collection `component` a ogni avvio
(salvo `no_update: true`). `datas` e' una lista di `{collection: path}` per
seed aggiuntivi, upsertati per `rec_name` allo stesso modo.

**Differenze rispetto al file 2.4 originale** (non e' un porting 1:1):
- `config.json` della 2.4 aveva un sacco di chiavi runtime
  (`internal_port`, `port`, `web_concurrency`, `theme`, `report_*`...) che
  appartenevano al vecchio modello "un deployment = un'app". Nel backend
  multi-tenant quelle chiavi non esistono piu': il manifest e' stato ridotto
  a quello che `plugin_installer.py` legge davvero.
- Il record component `modulo_dati_persona` aveva `"app_code": []` (lista
  vuota) invece di `""` (stringa) — tollerato dal vecchio modello, respinto
  dalla validazione Pydantic del nuovo. Va patchato a stringa vuota (fatto
  in `plugin/schema/components.json`).
- **La 2.4 aveva `"datas": []`** — nel vecchio monolite (un deployment =
  un'app) bastava il component per vedere la form. Nel nuovo backend
  multi-tenant, senza un `menu_group` + le `action` la form esiste nel DB ma
  non compare da nessuna parte nell'interfaccia.
  `plugin/data/menu_group.json` + `plugin/data/action.json` coprono questo
  gap — non stavano nella 2.4 originale.

### Il menu dashboard della form, gia' pronto al primo avvio

Quando si salva un component dal builder con `create_menu_dashboard`, il
backend genera da solo la card della dashboard e le action di default
(`Service._make_default_actions_for_component`): un `menu_group` con
`rec_name` = nome del model e le 6 action clonate dai template `sys` del
plugin `base` (`*_action` → `*_<model>`).

I seed della demo **riproducono esattamente quel risultato**, cosi' la
dashboard mostra la card gia' al primo `run_demo.sh up`, senza passare dal
builder:

| File | Record |
|---|---|
| `data/menu_group.json` | `modulo_dati_persona` — label "Modulo Dati Persona", `parent: ""`, `admin: false`, `apps: ["demo"]` |
| `data/action.json` | `list_` (menu/list), `new_` (window/form), `form_form_` (window/form), `submit_` (save), `copy_`, `delete_` — tutte su `modulo_dati_persona` |

Dettagli che contano (se tocchi questi file, la card sparisce):

- la card nasce dal `menu_group`, ma compare solo se **almeno una action non
  `sys`** punta a quel `menu_group` (`_get_basic_menu_list`);
- i bottoni della card arrivano solo dalle action con
  `component_type` in `form`/`resource`/`layout`: qui `list_` e `new_`. Le
  altre restano raggiungibili dentro la form, non sulla card;
- il `menu_group` deve avere `admin: false` e `parent: ""`, altrimenti
  finisce nel menu admin in alto o dentro una card-cartella;
- `apps: ["demo"]` fa lo scoping multi-tenant (`_default_query` filtra i
  `menu_group` per `app_code`);
- rispetto alla generazione automatica (che mette `groups: ["operator"]`,
  `user_function: "user"`) i seed usano i 4 gruppi della demo
  (`admin`/`user`/`operator`/`manager`), altrimenti la card la vedrebbe solo
  l'operator.

Le action generate dal builder avrebbero gli stessi `rec_name`: rifare il
salvataggio dal builder aggiorna gli stessi record, non li duplica.

## Login: come e' collegato tutto

Il web-client (`ozon-app-web`, nginx + Angular) sta su una sola origin
(`:4200`) e fa da reverse proxy verso il backend per `/api/*`, `/login`,
`/logout`, `/auth/*`: niente CORS, cookie di sessione single-origin.

Il backend implementa solo login **Keycloak** (Authorization Code, pattern
BFF): `/login` reindirizza a Keycloak, `/auth/callback` scambia il code,
crea la sessione e reimposta il cookie `ozon_session`. Non esiste un login
utente/password locale — per questo servono un realm, un client e utenti
Keycloak veri, provisionati da `provision_keycloak.sh`.

`is_admin` e i ruoli **non** vengono da Keycloak (nessun client role
richiesto): vengono da `group_users` in Mongo, keyed per `<group>-<app_code>`.
`bootstrap.py` (nell'immagine) seeda solo il gruppo `admin`; `seed_groups.py`
copre `user`/`operator`/`manager`.

### calendar-scheduler: anche lui via Keycloak (M2M)

`calendar-scheduler` non e' un utente umano: chiama l'endpoint
`/client/run/calendar_tasks/*` del backend come client `client_credentials`
(machine-to-machine). Serve quindi un secondo client Keycloak, service
account, separato dal client web (`provision_keycloak.sh` lo crea:
`calendar-scheduler`, `serviceAccountsEnabled: true`). Il suo utente
`service-account-calendar-scheduler` deve stare nel gruppo `admin` per
`app_code=demo` altrimenti l'ACL nega le scritture — `seed_groups.py` lo
aggiunge. L'override della demo imposta `OZON_TOKEN_AUDIENCE=demo` sul
backend e `SCHEDULER_OAUTH_AUDIENCE=demo` sullo scheduler. Il provisioning
Keycloak configura quindi, in modo idempotente, un audience mapper `demo`
sia sul client web sia sul client M2M: entrambi i token contengono
`demo` nel claim `aud`.

## Problemi noti

- **Campo "phoneNumber" non supportato**: `ModelMaker` del nuovo backend non
  ha un `add_phoneNumber`, quindi quel campo del form viene loggato come
  errore catturato all'avvio (`Error creation model object map: phoneNumber`)
  e ignorato — il resto del form funziona normalmente. E' una lacuna del
  motore, non uno sbaglio del porting.
- **Immagini da GHCR**: `backend/docker-compose.yml` e
  `app/docker-compose.client.example.yml` puntano di default a
  `ghcr.io/inrim/ozon-env-app/*` / `ghcr.io/inrim/ozon-formio`
  ([pacchetti INRIM](https://github.com/orgs/INRIM/packages?repo_name=ozon-env-app)),
  pubblici — nessun `docker login` richiesto. `demo/.env.demo` e
  `demo/.env.client-demo` non hanno override delle variabili `OZON_*_IMAGE`:
  se serve puntare a un'immagine locale o a un tag diverso, valorizzale li'.
- **nginx e IP stale**: `ozon-app-web` risolve l'IP del backend all'avvio e
  non lo aggiorna. Se ricrei il container `app` (es. dopo aver cambiato
  `KEYCLOAK_CLIENT_SECRET`) mentre il web-client e' gia' su, va ricreato
  anche lui — `run_demo.sh` lo fa gia' sempre all'ultimo step.
- **Keycloak assente in service-app 3.0**: `backend/docker-compose.yml` a
  monte dichiara il volume `keycloak_data` ma non il servizio `keycloak`.
  Finche' resta cosi', l'IdP lo aggiunge `docker-compose.demo.yml`; se
  service-app tornera' a definirlo, il blocco `keycloak:` di questo override
  va rimosso (il merge dei due compose lo terrebbe comunque, ma duplicato).

## Segreti

I file versionati (`.env.demo`, `.env.client-demo`) sono **template con
segnaposto**:

- `__GENERATE__` → `MONGO_PASS`, `SESSION_SECRET`, `KEYCLOAK_ADMIN_PASSWORD`:
  generati (`openssl rand -hex 16`) al primo `run_demo.sh up` e persistiti in
  `demo/.env.secrets` (gitignorato). Vengono riusati a ogni run: i volumi di
  Mongo e Keycloak sono gia' inizializzati con quelle credenziali,
  rigenerarle romperebbe il login;
- `__PROVISION__` → `KEYCLOAK_CLIENT_SECRET`,
  `SCHEDULER_OAUTH_CLIENT_SECRET`: li stampa `provision_keycloak.sh`, li
  scrive `run_demo.sh` nel `.env` generato e in `demo/.env.secrets`.

Gli `.env` operativi (`service-app/backend/.env`, `service-app/app/.env`)
sono copie locali rigenerate a ogni `run_demo.sh up` e stanno dentro il
checkout di service-app clonato nella root del repo (`./service-app`,
gitignorato), non qui.

Per ripartire con segreti nuovi: `demo/clean_demo.sh` (cancella
`.env.secrets` insieme ai volumi). Per buttare i container ma tenere i
segreti: `demo/clean_demo.sh --keep-secrets`.
