# zitio

[![CI](https://github.com/AlexCuenca99/zitio/actions/workflows/ci.yml/badge.svg?event=pull_request)](https://github.com/AlexCuenca99/zitio/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

API para encontrar y reservar estacionamientos en Riobamba.

Backend de Zitio: los conductores buscan estacionamientos cercanos y reservan un lugar; los
dueños publican sus estacionamientos y administran su capacidad. Expone una API REST sobre
Flask, persiste en Firestore y autentica con Firebase Authentication.

> **Estado:** en desarrollo. Disponibles: health check, usuarios y autenticación. El resto
> del alcance está en el [roadmap](#roadmap).

## Índice

- [Tecnologías](#tecnologías)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Contribuir](#contribuir)
- [Roadmap](#roadmap)
- [Licencia](#licencia)

## Tecnologías

- [Python 3.13](https://www.python.org/) y [Flask](https://flask.palletsprojects.com/)
- [Pydantic](https://docs.pydantic.dev/) y [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Google Cloud Firestore](https://cloud.google.com/firestore)
- [Firebase Authentication](https://firebase.google.com/docs/auth) (`firebase-admin`)
- [Google Cloud Logging](https://cloud.google.com/logging)
- [Docker](https://www.docker.com/) para los emuladores locales
- [pytest](https://docs.pytest.org/), [Ruff](https://docs.astral.sh/ruff/), [Bandit](https://bandit.readthedocs.io/) y [detect-secrets](https://github.com/Yelp/detect-secrets)

## Instalación

### Requisitos

- Python 3.13
- Docker con Docker Compose (para los emuladores de Firestore y Firebase Auth)

### Pasos

1. Clona el repositorio:

   ```sh
   git clone https://github.com/AlexCuenca99/zitio.git
   cd zitio
   ```

2. Crea un entorno virtual e instala las dependencias de desarrollo:

   ```sh
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

3. Instala los hooks de pre-commit:

   ```sh
   pre-commit install
   ```

4. Crea el archivo de entorno a partir del ejemplo:

   ```sh
   cp docker/local/prod/.env.example docker/local/prod/.env
   ```

## Configuración

La configuración se lee de variables de entorno con
[pydantic-settings](configs/config.py). En local también se lee
`docker/local/prod/.env`; las variables de entorno reales tienen prioridad sobre el archivo.

| Variable | Descripción | Default |
|---|---|---|
| `ENVIRONMENT` | `development` o `production`. En `production` los logs van a Cloud Logging. | `development` |
| `PROJECT_ID` | Proyecto de GCP/Firebase. También acepta `GOOGLE_CLOUD_PROJECT`. | — |
| `SERVICE_NAME` | Nombre del servicio en los logs. | `zitio` |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` o `CRITICAL`. | `INFO` |
| `SHOW_TRACEBACK` | Muestra el traceback en los logs. | `False` |
| `FLASK_DEBUG` / `FLASK_HOST` | Modo debug y host al correr con `python -m src.main`. | `False` / `127.0.0.1` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Service account para usar Firestore y Firebase reales. No hace falta con los emuladores. | — |
| `FIRESTORE_EMULATOR_HOST` | `host:port` del emulador de Firestore. | — |
| `FIREBASE_AUTH_EMULATOR_HOST` | `host:port` del emulador de Auth. **Nunca en producción.** | — |

Las variables `DOCKER_*` solo las usa Docker Compose (puertos y límites); están descritas en
[`.env.example`](docker/local/prod/.env.example).

## Uso

### Levantar el entorno local

1. Inicia los emuladores:

   ```sh
   docker compose -f docker/local/prod/docker-compose.prod.yaml up -d firestore-prod firebase-auth-prod
   ```

2. Apunta la app a los emuladores en `docker/local/prod/.env`:

   ```sh
   FIRESTORE_EMULATOR_HOST=localhost:8200
   FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
   ```

3. Corre la app (o usa `src/main.py` como configuración de ejecución en PyCharm):

   ```sh
   python -m src.main
   ```

   La API queda en `http://localhost:5000`. Para correr todo en Docker, incluida la app,
   usa `docker compose -f docker/local/prod/docker-compose.prod.yaml up -d`; la API queda
   en `http://localhost:8040`.

### Ejemplos

Health check (público):

```sh
curl -s http://localhost:5000/api/v1/health
```

```json
{"status": "ok", "services": {"firestore": true}, "meta": {"exec_seconds": 0.01}}
```

Los endpoints de usuarios requieren un token de Firebase. En local se obtiene del emulador
de Auth; el ciclo completo está en [docs/authentication.md](docs/authentication.md).

```sh
curl -s -X POST http://localhost:5000/api/v1/users \
  -H "Authorization: Bearer <idToken>" \
  -H "Content-Type: application/json" \
  -d '{"uid": "u1", "display_name": "Ana", "email": "ana@zitio.com", "role": "driver"}'
```

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/health` | Estado del servicio y de Firestore. Público. |
| `POST` | `/api/v1/users` | Crea un usuario. |
| `GET` | `/api/v1/users` | Lista los usuarios. |
| `GET` | `/api/v1/users/{uid}` | Obtiene un usuario. |

### Errores

Toda respuesta de error tiene el mismo formato:

```json
{
  "status": "fail",
  "error": {
    "type": "invalid_request_error",
    "code": "users.not_found",
    "message": "El(la) usuario con los parámetros de búsqueda uid: u9 no fue encontrado(a).",
    "param": "uid",
    "details": {"scope": "get", "search_params": {"uid": "u9"}},
    "request_id": "<trace id>"
  }
}
```

`code` es estable y sirve para que el cliente decida qué hacer. Todos los códigos posibles
están en el diccionario de errores, [`src/interactor/errors/catalog.py`](src/interactor/errors/catalog.py).

## Estructura del proyecto

```
├── configs/                 # Settings (pydantic-settings)
├── docker/local/prod/       # Docker Compose, emuladores y .env.example
├── docs/                    # Documentación extendida
├── src/
│   ├── app/                 # Flask: app, blueprints, autenticación y manejo de errores
│   ├── bootstrap/           # Arma la app y sus dependencias
│   ├── domain/entities/     # Entidades de negocio (Pydantic)
│   ├── infra/               # Firestore, Firebase Auth y logging
│   ├── interactor/          # Casos de uso, interfaces (puertos) y errores
│   └── main.py              # Punto de entrada (gunicorn: src.main:app)
└── tests/                   # Tests unitarios y de integración
```

## Contribuir

Las dudas y propuestas se manejan en los [issues](https://github.com/AlexCuenca99/zitio/issues).
Se aceptan pull requests siguiendo este flujo:

1. Crea una rama desde `stage`: `feature/<issue>-<descripcion>`.
2. Sincroniza con `rebase`, nunca con `merge`.
3. Abre el PR contra `stage`. A `master` solo llega `stage`.
4. El PR necesita los checks `static-analysis` y `test` en verde y la review del code owner.

### Convenciones

- Código, commits e issues en inglés.
- Docstrings estilo Google estricto; cada módulo empieza con
  `"""This module defines ..."""` en una sola línea.
- Errores con el código del catálogo:
  `raise NotFoundError("users.not_found", search_params={"uid": uid}, scope="get")`.
- La deuda técnica se registra como issue con la etiqueta `tech-debt`.

### Tests

```sh
pytest
```

Sin emulador, los tests de integración se saltan. Para correrlos, levanta el emulador de
Firestore e indica su host:

```sh
FIRESTORE_EMULATOR_HOST=localhost:8200 pytest --cov=src
```

### Análisis estático

Los hooks de pre-commit corren Ruff (lint y formato), Bandit y detect-secrets en cada commit.
Para correrlos sobre todo el repositorio:

```sh
pre-commit run --all-files
```

La CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) corre las mismas
herramientas y los tests, con el emulador de Firestore, en cada PR a `stage` y `master`.

## Roadmap

El alcance está en los [issues abiertos](https://github.com/AlexCuenca99/zitio/issues).
Próximos:

- Perfil de usuario ligado a Firebase (`/users/me`) y roles conductor/dueño
- Registro y búsqueda geoespacial de estacionamientos
- Reservas atómicas, check-in con QR y check-out con cobro
- Despliegue en Cloud Run

## Licencia

[Apache-2.0](LICENSE) © Alex Cuenca
