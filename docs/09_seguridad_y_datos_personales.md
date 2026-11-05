# Datos personales y seguridad de acceso

## Qué datos personales hay

La fuente identifica a personas de dos formas:

| Dónde | Qué contiene | Riesgo |
|---|---|---|
| Columnas `Operario` y `Personal involucrado` | Nombres completos y parciales de operarias y de personal de mantenimiento (43 personas) | Evaluar el desempeño de personas con nombre propio en un tablero que ve toda la empresa. |
| Columna `Observaciones` | Texto libre que puede mencionar a personas (275 filas) | No hay forma de garantizar que un filtro elimine todos los nombres. |
| Metadatos del archivo | Autores y rutas del libro | Exposición en un repositorio público. |

En Colombia el tratamiento de estos datos se rige por la Ley 1581 de 2012 y su decreto reglamentario. Los principios que se aplican aquí son la **finalidad** (analizar procesos, no evaluar personas), la **minimización** (no cargar lo que no se necesita) y la **seguridad** (limitar quién accede y a qué).

## Cómo se tratan

| Medida | Dónde | Efecto |
|---|---|---|
| **Seudonimización antes de cargar** | `etl/bi_etl/anonymize.py`, regla R11 | Cada nombre se reemplaza por un HMAC-SHA256 con una sal secreta (`PER-` más 10 caracteres). Ningún nombre llega a PostgreSQL, ni a Power BI, ni a Grafana. |
| **Sal secreta fuera del repositorio** | `ANONYMIZATION_SALT` en `.env` | Sin la sal no se puede recalcular el seudónimo de un nombre conocido. La misma persona conserva su seudónimo entre cargas. |
| **Minimización** | Regla R14 | La columna `Observaciones` no se carga. Los motivos de paro se normalizan a una lista cerrada (R24). |
| **Sin datos personales en los tableros** | Grafana y Power BI | El tablero de Grafana no usa personas. En Power BI, `Persona` solo tiene seudónimo y rol, y sus columnas no están en ningún visual; el análisis es por máquina, turno, referencia y causa. |
| **Fuente y salidas fuera de Git** | `.gitignore` | Se excluyen `*.xlsm`, `*.xls*`, `P-MTO-*.pdf`, `data/source/` y los PDF entregables. |

**Límite conocido.** La seudonimización no es anonimización: quien tenga la sal y la lista de nombres puede reidentificar. Además, un nombre de pila suelto no se une con un nombre completo (podría ser otra persona), por lo que una misma persona puede tener dos seudónimos. Por eso la sal se trata como un secreto y la base como información restringida.

**Recomendación a la empresa.** Definir si se necesita evaluar por persona. Si no, quitar el nombre en el origen, es decir, que el formato registre la matrícula del operario y no el nombre.

## Seguridad de acceso a los tableros

### Base de datos

| Control | Implementación |
|---|---|
| **Mínimo privilegio** | Grafana y Power BI se conectan con el rol **`bi_lector`**, que solo tiene `SELECT` sobre `dw`, `audit` y `ops` (`db/init/01_roles.sh`, `sql/ddl/03_permisos.sql`). El usuario administrador solo lo usan el ETL y el simulador. |
| **Solo lectura reforzada** | El rol tiene `default_transaction_read_only = on` y un `statement_timeout` de 30 s, así que ni siquiera una sesión abierta con ese rol puede modificar datos ni dejar una consulta colgada. |
| **Los permisos sobreviven al ETL** | El ETL recrea `dw` y `audit` en cada ejecución; `03_permisos.sql` vuelve a conceder los permisos. |
| **Credenciales fuera del repositorio** | `.env` está excluido; `.env.example` está versionado con valores `cambiar_esto`, y los servicios se niegan a iniciar si siguen así. |

### Grafana

- **Acceso anónimo desactivado** y registro de usuarios cerrado.
- **Fuente de datos no editable** desde la interfaz y creada con el usuario de solo lectura.
- **Telemetría desactivada** (informes de uso y búsqueda de actualizaciones).
- **Webhook de alertas autenticado** con un token propio; el receptor compara en tiempo constante y registra solo el esquema y la longitud cuando rechaza una petición, nunca el valor.
- **Red:** el simulador solo escucha dentro de la red de Docker; no se publica su puerto. Hacia el anfitrión solo salen PostgreSQL (5432) y Grafana (3000).

### Power BI

- El proyecto **no contiene datos ni credenciales**: cada persona se autentica con su propio usuario al abrirlo.
- Para publicar en el servicio de Power BI, se recomienda **seguridad a nivel de fila** (por ejemplo, un rol por línea para supervisores) y compartir con grupos, no con personas. En esta entrega no se define porque no hay servicio al que publicar.

## Qué falta para producción

La demostración corre en una máquina sin cifrado. Para una planta real:

1. **TLS** en PostgreSQL y en Grafana (con un proxy inverso) y desactivar «sin cifrado» en Power BI.
2. **Roles de Grafana** por función: *Viewer* para supervisión, *Editor* para mantenimiento, *Admin* solo para el responsable del sistema; autenticación con el directorio de la empresa (SSO) en lugar de usuario local.
3. **Gestor de secretos** (en lugar de un `.env` en el servidor) y rotación de claves.
4. **Copias de seguridad** del volumen de PostgreSQL y registro de accesos.
5. **Autorización de tratamiento** y aviso de privacidad para el personal, y política de retención de los datos.
