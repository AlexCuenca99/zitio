# Autenticación

Zitio usa [Firebase Authentication](https://firebase.google.com/docs/auth). El backend
**nunca maneja contraseñas ni sesiones**: Firebase administra las identidades y emite los
tokens; el backend solo verifica que cada token sea auténtico.

## Índice

- [Actores](#actores)
- [Ciclo de vida en producción](#ciclo-de-vida-en-producción)
- [Ciclo de vida en local](#ciclo-de-vida-en-local)
- [Obtener un token en local](#obtener-un-token-en-local)
- [Respuestas de error](#respuestas-de-error)

## Actores

| Papel | Producción | Local |
|---|---|---|
| App cliente | App web/móvil con el SDK de Firebase | Tú, con `curl`, Postman o el cliente HTTP del IDE |
| Firebase Auth | Servicio de Google | Emulador de Auth (servicio `firebase-auth-prod`, puerto 9099) |
| Backend | Cloud Run | PyCharm o el contenedor `app-prod` |
| Base de datos | Firestore | Emulador de Firestore (servicio `firestore-prod`, puerto 8200) |

## Ciclo de vida en producción

```
 App cliente                 Firebase Auth                    Backend zitio
     │                            │                                 │
 1.  │── signUp(email, pass) ────▶│ crea usuario, uid="abc123"      │
     │◀── ID token + refresh ─────│                                 │
 2.  │── POST /users/me ──────────┼── Authorization: Bearer <ID> ──▶│ verifica token → uid
     │◀───────────────────────────┼──────────────── perfil ─────────│ crea perfil en Firestore
 3.  │── GET /... ────────────────┼── Bearer <ID> ─────────────────▶│ verifica → uid → datos
 4.  │── refresh token ──────────▶│ (cada hora) nuevo ID token      │
 5.  │  signOut(): borra tokens   │                                 │
```

1. **Registro.** La app cliente crea el usuario con el SDK de Firebase. Firebase le asigna
   un `uid` permanente y devuelve dos tokens:
   - **ID token**: dura 1 hora y es el único que se envía a la API.
   - **Refresh token**: de larga duración; solo sirve para pedir ID tokens nuevos a
     Firebase. Nunca se envía a la API.
2. **Perfil de negocio.** El usuario de Firebase solo tiene la identidad. Los datos de
   Zitio (`display_name`, `role`, `vehicle_plate`...) viven en la colección `users` de
   Firestore, con el `uid` como id. El backend toma el `uid` **del token**, nunca del body.
3. **Cada request** lleva `Authorization: Bearer <ID token>`. El ID token es un JWT firmado
   por Google. El decorador `@token_required` lo verifica con
   `firebase_admin.auth.verify_id_token`, que comprueba:
   - la **firma**, con las claves públicas de Google (descargadas y cacheadas por el SDK);
   - que `aud` sea **este** proyecto de Firebase;
   - que no haya expirado.

   Si es válido, el `uid` queda en `flask.g.uid`. La verificación es local: no hay una
   llamada a Firebase por request.
4. **Renovación.** El SDK del cliente renueva el ID token con el refresh token antes de que
   expire. Si llega uno expirado, la API responde `auth.token_expired`.
5. **Logout.** `signOut()` borra los tokens del dispositivo. Un ID token ya emitido sigue
   siendo válido hasta su expiración (máximo 1 hora); cortar el acceso de inmediato
   requiere verificar revocación ([#46](https://github.com/AlexCuenca99/zitio/issues/46)).

## Ciclo de vida en local

Es el mismo ciclo: **tú haces de app cliente** y **el emulador hace de Firebase**. El
código del backend no cambia; lo único distinto es una variable de entorno:

- Con `FIREBASE_AUTH_EMULATOR_HOST` definida, el SDK acepta los tokens del emulador, que
  **no están firmados**.
- Sin ella, el SDK exige la firma de Google y un token del emulador falla con
  `auth.token_invalid`.

> **Importante:** `FIREBASE_AUTH_EMULATOR_HOST` nunca debe estar definida en producción:
> con ella, cualquiera podría fabricar un token con el `uid` que quiera.

El host del emulador depende de dónde corre el backend:

| Backend corre en | `FIREBASE_AUTH_EMULATOR_HOST` | Dónde se define |
|---|---|---|
| PyCharm (tu máquina) | `localhost:9099` | `docker/local/prod/.env` |
| Contenedor `app-prod` | `firebase-auth-prod:9099` | Ya está en el compose |

El emulador emite tokens con `aud` igual a su `--project`, que el compose toma de
`PROJECT_ID`. El backend compara `aud` con su propio `PROJECT_ID`: **deben coincidir**.

## Obtener un token en local

1. Levanta los emuladores (la primera vez el de Auth tarda ~40 s en descargar
   `firebase-tools`):

   ```sh
   docker compose -f docker/local/prod/docker-compose.prod.yaml up -d firestore-prod firebase-auth-prod
   ```

2. Crea un usuario. La respuesta trae `idToken` (el token) y `localId` (el `uid`):

   ```sh
   curl -s -X POST "http://localhost:9099/identitytoolkit.googleapis.com/v1/accounts:signUp?key=any" \
     -H "Content-Type: application/json" \
     -d '{"email": "<email>", "password": "<password>", "returnSecureToken": true}'  # pragma: allowlist secret
   ```

   En PowerShell:

   ```powershell
   $body = @{ email = "<email>"; password = "<password>"; returnSecureToken = $true } | ConvertTo-Json  # pragma: allowlist secret
   (Invoke-RestMethod -Method Post -ContentType "application/json" -Body $body `
     -Uri "http://localhost:9099/identitytoolkit.googleapis.com/v1/accounts:signUp?key=any").idToken
   ```

   `signUp` funciona una vez por email. Para un usuario existente usa
   `accounts:signInWithPassword` con el mismo body. El emulador acepta cualquier `key`.

3. Llama a la API con el token:

   ```sh
   curl -s http://localhost:5000/api/v1/users -H "Authorization: Bearer <idToken>"
   ```

El token dura 1 hora. Los usuarios del emulador viven en memoria: se pierden al reiniciar
el contenedor.

## Respuestas de error

Todas siguen el formato de error de la API, con status `401` y el header
`WWW-Authenticate: Bearer`.

| Código | Causa |
|---|---|
| `auth.token_missing` | No hay header `Authorization`, o no es `Bearer <token>`. |
| `auth.token_invalid` | Token malformado, con firma inválida o de otro proyecto (`aud`). En local: falta `FIREBASE_AUTH_EMULATOR_HOST` o los `PROJECT_ID` no coinciden. |
| `auth.token_expired` | El token expiró: pide otro. |
| `auth.internal_error` | Status `500`: no se pudieron obtener las claves públicas de Google. |
