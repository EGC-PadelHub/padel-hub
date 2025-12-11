# Fakenodo (Mock Zenodo in‑process)

## 1. Qué es
Fakenodo es un **simulador mínimo de la API de Zenodo** integrado como *blueprint* (`/fakenodo/api`) dentro de la app Flask. No persiste nada: todos los depósitos y archivos viven solo en memoria (RAM) mientras el proceso está activo. Sirve para **desarrollar y testear** el flujo de publicación de datasets sin internet, sin token ni infraestructura externa.

**Características principales:**
- ✅ Simula endpoints básicos de Zenodo API
- ✅ Gestión de versiones (metadata-only vs cambio de archivos)
- ✅ Generación de DOIs fake (formato: `10.5072/fakenodo.<id>`)
- ✅ No requiere configuración externa ni tokens
- ✅ Ideal para desarrollo local y CI/CD

## 2. Activación rápida

### Desarrollo Local
Se activa automáticamente en desarrollo (por defecto `UPLOADS_USE_FAKENODO_ONLY=true`). Variables en `.env`:

```bash
FLASK_ENV=development
UPLOADS_USE_FAKENODO_ONLY=true
FAKENODO_HOSTNAME=127.0.0.1
```

**Nota:** `FAKENODO_URL` no es necesaria; `ZenodoService` construye automáticamente la URL usando `FAKENODO_HOSTNAME`.

### Docker
En Docker, el hostname debe apuntar al contenedor `web`:

```bash
FAKENODO_HOSTNAME=web  # Configurado automáticamente en docker-compose.*.yml
```

### Usar Zenodo Real
Para desactivar fakenodo y usar Zenodo real:

```bash
export UPLOADS_USE_FAKENODO_ONLY=false
export ZENODO_ACCESS_TOKEN=tu_token_aqui
export ZENODO_API_URL=https://sandbox.zenodo.org/api/deposit/depositions
```

## 3. Endpoints implementados

Todos los endpoints están bajo el prefijo `/fakenodo/api`:

| Método | Endpoint | Descripción | Respuesta |
|--------|----------|-------------|-----------|
| GET | `/fakenodo/api` | Test de conexión | `{"status": "success", "message": "Connected to FakenodoAPI"}` |
| POST | `/fakenodo/api/deposit/depositions` | Crear deposición | `{"id": 1, "conceptrecid": 1, "metadata": {...}, "files": [], "doi": null, "published": false}` |
| GET  | `/fakenodo/api/deposit/depositions` | Listar todas las deposiciones | `[{...}, {...}]` (lista directa) |
| GET  | `/fakenodo/api/deposit/depositions/<id>` | Obtener deposición específica | `{"id": 1, "doi": "10.5072/fakenodo.1", ...}` |
| PUT  | `/fakenodo/api/deposit/depositions/<id>` | Actualizar metadata (no cambia DOI) | `{"id": 1, "metadata": {...updated...}}` |
| POST | `/fakenodo/api/deposit/depositions/<id>/files` | Subir archivo (solo registra nombre) | `{"filename": "file.uvl", "link": "..."}` |
| POST | `/fakenodo/api/deposit/depositions/<id>/actions/publish` | Publicar deposición | `{"id": 1, "doi": "10.5072/fakenodo.1", "conceptrecid": 1, ...}` |
| GET  | `/fakenodo/api/deposit/depositions/<id>/versions` | Listar versiones del concept | `{"versions": [{...}, {...}]}` |
| DELETE | `/fakenodo/api/deposit/depositions/<id>` | Eliminar deposición | `{"message": "Deposition deleted"}` |

**DOI generado:** `10.5072/fakenodo.<id>`

### Lógica de versiones
- **Metadata-only update:** Usar `PUT` + `POST publish` → **mismo DOI**, no crea nueva versión
- **Cambio de archivos:** `POST files` + `POST publish` después de publicar → **nuevo DOI**, nueva versión con nuevo ID
- Todas las versiones comparten el mismo `conceptrecid`

## 4. Flujo básico
1. **Crear deposición** (draft, sin DOI)
2. **Subir archivos** (registra nombres, no guarda contenido binario)
3. **Publicar** (asigna DOI y marca como published)
4. **Consultar** para verificar el DOI generado
5. **(Opcional)** Modificar metadata → republicar mantiene mismo DOI
6. **(Opcional)** Agregar/cambiar archivos → republicar crea nueva versión con nuevo DOI

## 5. Verificación rápida (cURL)

### Test de conexión
```bash
curl -s http://127.0.0.1:5000/fakenodo/api | jq
```

### Flujo completo
```bash
# 1. Crear deposición
DEP=$(curl -s -X POST http://127.0.0.1:5000/fakenodo/api/deposit/depositions \
  -H 'Content-Type: application/json' \
  -d '{"metadata": {"title": "Test Dataset", "upload_type": "dataset", "description": "Prueba", "creators": [{"name": "Test User"}]}}')
echo $DEP | jq
ID=$(echo $DEP | jq -r '.id')

# 2. Subir archivo
curl -s -X POST http://127.0.0.1:5000/fakenodo/depositions/1/files \
  -F name=test.txt -F file=@/etc/hosts | jq

# 3. Publicar (asigna DOI)
curl -s -X POST http://127.0.0.1:5000/fakenodo/depositions/1/actions/publish | jq

# 4. Consultar
curl -s http://127.0.0.1:5000/fakenodo/depositions/1 | jq

# 5. Estado
curl -s http://127.0.0.1:5000/fakenodo/status | jq
```
Si en el paso 3/4 ves un `doi` distinto de `null`, funciona correctamente.

## 6. Variables de entorno clave
| Variable | Valor por defecto | Uso |
|----------|-------------------|-----|
| `UPLOADS_USE_FAKENODO_ONLY` | `true` | Fuerza uso de Fakenodo |
| `FAKENODO_URL` | `http://127.0.0.1:5000/fakenodo/depositions` | Base para crear deposiciones |
| `ZENODO_ACCESS_TOKEN` | (vacío) | Solo necesario si se usa Zenodo real |

## 7. Limitaciones
No hay: persistencia, edición, borrado, versionado, validación estricta, simulación de errores, almacenamiento real de archivos, búsqueda ni rate limits. Todo responde éxito (2xx) mientras el servidor vive.

## 8. Cuándo usar / no usar
Usar: desarrollo local, pruebas de integración, trabajar offline, evitar contaminar sandbox.  
No usar: producción o escenarios donde se requieran DOIs reales y persistencia.

## 9. Resumen rápido
- Mock Zenodo in-process (sin contenedores extra).  
- Datos efímeros en memoria.  
- Endpoints mínimos para crear/subir/publicar.  
- Validación y errores simplificados (siempre OK).  
- DOI fake `10.5072/fakenodo.X`.  
- Activación: exportar variables y `flask run`.  
- Verificación: secuencia cURL y comprobar DOI.

---
Mantén este README corto: cualquier lógica extra debe revisarse en el código fuente del módulo.# Fakenodo - Simulador de API Zenodo# Fakenodo (in-process ultra fake Zenodo)



## ¿Qué es Fakenodo?Este módulo ya NO es una aplicación separada. Se levanta automáticamente con el `flask run` normal del proyecto y expone unos endpoints mínimos que siempre responden OK sin guardar nada real en disco.



**Fakenodo** es un **simulador local de la API de Zenodo** integrado directamente en PadelHub. Su propósito es permitir el desarrollo y testing de funcionalidades de publicación de datasets **sin necesidad de**:Objetivo: permitir que los flujos de subida/publicación de datasets funcionen sin tocar la API real de Zenodo y sin mantener estado permanente. Solo existe memoria efímera mientras el proceso vive.



- ❌ Conexión a internet## Endpoints disponibles (blueprint `/fakenodo`)

- ❌ Credenciales de Zenodo (tokens de acceso)

- ❌ Enviar datos reales a servidores externosBase para `FAKENODO_URL` → `http://127.0.0.1:5000/fakenodo/depositions`

- ❌ Levantar servicios adicionales o contenedores separados

No hay versiones, ni edición avanzada, ni borrado. Si reinicias el servidor, desaparecen los datos.

Es un **mock server in-process** que replica el comportamiento básico de la API de Zenodo, respondiendo siempre exitosamente a las peticiones de creación, carga de archivos y publicación de deposiciones.

## Cómo usarlo desde el módulo dataset

---

1. Asegúrate de tener exportada la URL fake:

## ¿Cómo funciona?  ```bash

  export FAKENODO_URL="http://127.0.0.1:5000/fakenodo/depositions"

### Arquitectura  export UPLOADS_USE_FAKENODO_ONLY=true   # (por defecto ya es true)

  ```

```2. Lanza la app normalmente:

┌─────────────────────────────────────────────────────────────┐  ```bash

│                     Flask App (PadelHub)                     │  flask run

├─────────────────────────────────────────────────────────────┤  ```

│                                                               │3. Cuando subas un dataset, `ZenodoService` usará esta URL y todo responderá OK. No se crean DOIs reales.

│  ┌──────────────────┐          ┌──────────────────┐         │

│  │ ZenodoService    │          │ Fakenodo Module  │         │## Verificación rápida manual

│  │ (Cliente)        │──HTTP───▶│ (Servidor Mock)  │         │

│  │                  │          │                  │         │```bash

│  │ • Decide qué URL │          │ Blueprint:       │         │# Crear depósito

│  │   usar según env │          │ /fakenodo/*      │         │curl -s -X POST http://127.0.0.1:5000/fakenodo/depositions \

│  │ • Hace requests  │          │                  │         │  -H 'Content-Type: application/json' \

│  │ • Sube datasets  │          │ Estado en RAM    │         │  -d '{"metadata": {"title": "Demo", "upload_type": "dataset"}}'

│  └──────────────────┘          └──────────────────┘         │

│                                                               │# (Guarda el campo "id")

└─────────────────────────────────────────────────────────────┘

```# Subir (fake) archivo

curl -s -X POST http://127.0.0.1:5000/fakenodo/depositions/1/files \

### Flujo de datos  -F name=test.txt -F file=@/etc/hosts



1. **Configuración**: El usuario exporta `UPLOADS_USE_FAKENODO_ONLY=true` y `FAKENODO_URL=http://127.0.0.1:5000/fakenodo/depositions`# Publicar (asigna DOI)

curl -s -X POST http://127.0.0.1:5000/fakenodo/depositions/1/actions/publish | jq

2. **Decisión**: `ZenodoService` lee las variables de entorno y decide usar Fakenodo en lugar de la API real de Zenodo

# Consultar depósito (verás el DOI)

3. **Comunicación**: Cuando se sube un dataset:curl -s http://127.0.0.1:5000/fakenodo/depositions/1 | jq

   - `ZenodoService` hace peticiones HTTP con `requests` ```

   - Las peticiones van a `http://127.0.0.1:5000/fakenodo/depositions` (mismo proceso Flask)

   - Fakenodo responde inmediatamente con datos simuladosSi ves `doi` diferente de `null`, funciona.



4. **Almacenamiento**: Los datos se guardan **solo en memoria** (diccionario Python) durante la ejecución## Cómo saber que está activo

   - No hay persistencia en base de datos

   - No hay archivos guardados en disco- Endpoint de estado: `GET /fakenodo/status` → JSON con número de registros.

   - Al reiniciar el servidor, todo se borra- Crear + publicar + recuperar un depósito funciona y siempre responde 2xx.



### Estado en memoria## Preguntas frecuentes



```python| Pregunta | Respuesta |

_STATE = {|----------|-----------|

    "next_id": itertools.count(1),  # Generador de IDs únicos| ¿Dónde se guardan los datos? | Solo en memoria (diccionario Python). |

    "records": {| ¿Se limpian solos? | Al reiniciar el proceso Flask. |

        1: {| ¿Puedo simular errores? | No en esta versión ultra-fake. Todo es éxito. |

            "id": 1,| ¿Necesito token Zenodo? | No. Nunca se envía. |

            "conceptrecid": 1,

            "metadata": {...},## Próximos pasos opcionales

            "files": [...],

            "doi": "10.5072/fakenodo.1",Si algún test necesita simular fallos, se podría añadir un flag de entorno `FAKENODO_FAIL_NEXT` para forzar un 500 en la siguiente petición.

            "state": "published"

        },---

        2: {...},Este README sustituye al anterior (standalone). Cualquier fichero antiguo (`app.py`, carpeta `data/`) ya no es necesario y puede eliminarse.

        ...
    }
}
```

---

## ¿Qué hace Fakenodo?

### Endpoints implementados

Fakenodo expone una **API REST compatible con Zenodo** bajo el prefijo `/fakenodo`:

| Método | Endpoint | Función | Respuesta |
|--------|----------|---------|-----------|
| `GET` | `/fakenodo/depositions` | Lista todas las deposiciones | Array de registros (200) |
| `POST` | `/fakenodo/depositions` | Crea una nueva deposición | Registro con ID y links (201) |
| `GET` | `/fakenodo/depositions/<id>` | Obtiene una deposición | Datos del registro (200/404) |
| `POST` | `/fakenodo/depositions/<id>/files` | Sube un archivo | Confirmación de archivo (201/404) |
| `POST` | `/fakenodo/depositions/<id>/actions/publish` | Publica la deposición | Registro con DOI asignado (202/404) |
| `GET` | `/fakenodo/status` | Estado del servicio | Número de registros en memoria (200) |

### Comportamiento simulado

#### 1. Crear deposición
```bash
POST /fakenodo/depositions
Body: {"metadata": {"title": "Mi Dataset", "upload_type": "dataset"}}

Response (201):
{
  "id": 1,
  "conceptrecid": 1,
  "metadata": {"title": "Mi Dataset", "upload_type": "dataset"},
  "files": [],
  "doi": null,
  "state": "draft",
  "links": {
    "files": "/fakenodo/depositions/1/files",
    "publish": "/fakenodo/depositions/1/actions/publish",
    "self": "/fakenodo/depositions/1"
  }
}
```

#### 2. Subir archivo
```bash
POST /fakenodo/depositions/1/files
Form-data: name=dataset.uvl, file=<binary>

Response (201):
{
  "filename": "dataset.uvl",
  "links": {"self": "/fakenodo/depositions/1/files/dataset.uvl"}
}
```

**Nota**: El archivo NO se guarda en disco, solo se registra el nombre en memoria.

#### 3. Publicar
```bash
POST /fakenodo/depositions/1/actions/publish

Response (202):
{
  "id": 1,
  "doi": "10.5072/fakenodo.1",
  "conceptrecid": 1
}
```

El DOI generado tiene el formato `10.5072/fakenodo.<id>` (prefijo de sandbox).

---

## ¿Cuándo se usa?

### Automáticamente en desarrollo

Cuando configuras:

```bash
export UPLOADS_USE_FAKENODO_ONLY=true  # Fuerza el uso de fakenodo
export FAKENODO_URL="http://127.0.0.1:5000/fakenodo/depositions"
```

**Todos los datasets subidos** desde la interfaz web irán a Fakenodo en lugar de Zenodo real.

### En tests automatizados

```python
from app.modules.zenodo.services import ZenodoService

def test_dataset_upload():
    # ZenodoService usará automáticamente Fakenodo si está configurado
    service = ZenodoService()
    
    # Esta petición va a /fakenodo/depositions (no a Zenodo real)
    deposition = service.create_new_deposition(dataset)
    
    assert deposition['id'] is not None
    assert deposition['doi'] is None  # Aún no publicado
```

### Verificación manual

```bash
# 1. Crear depósito
curl -s -X POST http://127.0.0.1:5000/fakenodo/depositions \
  -H 'Content-Type: application/json' \
  -d '{"metadata": {"title": "Test", "upload_type": "dataset"}}' | jq

# 2. Subir archivo
curl -s -X POST http://127.0.0.1:5000/fakenodo/depositions/1/files \
  -F name=test.txt -F file=@/etc/hosts | jq

# 3. Publicar
curl -s -X POST http://127.0.0.1:5000/fakenodo/depositions/1/actions/publish | jq

# 4. Consultar
curl -s http://127.0.0.1:5000/fakenodo/depositions/1 | jq

# 5. Ver estado del servicio
curl -s http://127.0.0.1:5000/fakenodo/status | jq
# Output: {"module": "fakenodo", "mode": "in-process", "records": 1}
```

---

## Configuración

### Variables de entorno

| Variable | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| `UPLOADS_USE_FAKENODO_ONLY` | `true` | Fuerza el uso de fakenodo para uploads |
| `FAKENODO_URL` | `http://127.0.0.1:5000/fakenodo/depositions` | URL base de fakenodo |
| `ZENODO_ACCESS_TOKEN` | - | Token real de Zenodo (no necesario con fakenodo) |

### Cómo activar Fakenodo

#### Opción 1: Variables de entorno (recomendado para desarrollo)

```bash
export FLASK_APP=app
export FLASK_ENV=development
export FAKENODO_URL="http://127.0.0.1:5000/fakenodo/depositions"
export UPLOADS_USE_FAKENODO_ONLY=true

flask run
```

#### Opción 2: Archivo `.flaskenv` (persistente)

Crea un archivo `.flaskenv` en la raíz del proyecto:

```bash
FLASK_APP=app
FLASK_ENV=development
FAKENODO_URL=http://127.0.0.1:5000/fakenodo/depositions
UPLOADS_USE_FAKENODO_ONLY=true
```

Luego simplemente:

```bash
flask run
```

### Cómo desactivar Fakenodo (usar Zenodo real)

```bash
export UPLOADS_USE_FAKENODO_ONLY=false
export ZENODO_ACCESS_TOKEN="tu_token_aqui"
export ZENODO_API_URL="https://sandbox.zenodo.org/api/deposit/depositions"

flask run
```

---

## Limitaciones

### ❌ No implementado

- **Persistencia**: Los datos se pierden al reiniciar el servidor
- **Edición de metadata**: No puedes modificar deposiciones ya creadas
- **Borrado**: No hay endpoint DELETE
- **Versionado**: No soporta nuevas versiones de un mismo dataset
- **Validación**: No valida metadatos (acepta cualquier JSON)
- **Errores**: Siempre responde OK (no simula fallos de red o validación)
- **Archivos reales**: No almacena el contenido de los archivos subidos
- **Búsqueda**: No hay endpoint de búsqueda/filtrado

### ✅ Suficiente para

- Desarrollo local sin conexión
- Tests de integración del flujo de publicación
- Validar que el código de `ZenodoService` funciona
- Evitar crear deposiciones de prueba en Zenodo real
- Desarrollo rápido sin configurar credenciales

---

## Arquitectura técnica

### Registro del módulo

Fakenodo es un **módulo Flask estándar** que se registra automáticamente:

```python
# app/modules/fakenodo/__init__.py
from .routes import fakenodo_module

# app/__init__.py registra todos los módulos automáticamente
# incluyendo fakenodo_module como blueprint
```

### Implementación minimalista

```python
# routes.py (simplificado)
from flask import Blueprint, jsonify, request

fakenodo_module = Blueprint("fakenodo", __name__, url_prefix="/fakenodo")

_STATE = {
    "next_id": itertools.count(1),
    "records": {},
}

@fakenodo_module.route("/depositions", methods=["POST"])
def create_deposition():
    rec_id = next(_STATE["next_id"])
    record = {
        "id": rec_id,
        "metadata": request.get_json().get("metadata", {}),
        "files": [],
        "doi": None,
        "state": "draft"
    }
    _STATE["records"][rec_id] = record
    return jsonify(record), 201
```

Total: **~100 líneas de código Python** para replicar el comportamiento básico de Zenodo.

---

## Diferencias con Zenodo real

| Aspecto | Zenodo Real | Fakenodo |
|---------|-------------|----------|
| Persistencia | Base de datos permanente | RAM (efímero) |
| DOI | DOIs reales registrados | DOIs fake `10.5072/fakenodo.X` |
| Archivos | Almacenados en S3/disco | Solo nombres en memoria |
| Validación | Estricta (schemas JSON) | Acepta todo |
| Límites | 50GB por dataset | Sin límites (no guarda) |
| Versiones | Soporte completo | No soportado |
| Búsqueda | Elasticsearch | No disponible |
| Auth | Tokens OAuth2 | No requiere autenticación |
| Rate limits | 60 req/min | Sin límites |

---

## Preguntas frecuentes (FAQ)

### ¿Por qué usar Fakenodo en vez de Zenodo sandbox?

- ✅ No necesitas crear cuenta en Zenodo
- ✅ No necesitas token de acceso
- ✅ Funciona sin internet
- ✅ Tests más rápidos (sin latencia de red)
- ✅ No contaminas el sandbox con datos de prueba

### ¿Los DOIs generados son válidos?

**No**. El prefijo `10.5072/` indica un DOI de prueba. No están registrados en DataCite ni son resolubles públicamente.

### ¿Puedo usar Fakenodo en producción?

**NO**. Fakenodo es solo para desarrollo/testing. En producción debes usar Zenodo real con `UPLOADS_USE_FAKENODO_ONLY=false`.

### ¿Cómo verifico que Fakenodo está activo?

```bash
curl http://127.0.0.1:5000/fakenodo/status

# Respuesta esperada:
# {"module": "fakenodo", "mode": "in-process", "records": 0}
```

### ¿Se guardan los archivos subidos?

**No**. Solo se registra el nombre del archivo. El contenido binario se descarta inmediatamente.

### ¿Puedo inspeccionar los datos en memoria?

Sí, desde la consola Python del servidor:

```python
from app.modules.fakenodo.routes import _STATE
print(_STATE["records"])
```

### ¿Qué pasa si reinicio el servidor?

Todos los datos en `_STATE` se pierden. Empiezas con ID 1 de nuevo.

---

## Evolución histórica

| Versión | Implementación | Estado |
|---------|----------------|--------|
| **v1** | App Flask standalone separada | ❌ Deprecada |
| | Requería levantar proceso adicional | |
| | Guardaba datos en `data/store.json` | |
| **v2** | Blueprint in-process (actual) | ✅ Activa |
| | Integrado en la app principal | |
| | Estado solo en RAM | |
| | Sin archivos de configuración | |

**Archivos obsoletos** (pueden eliminarse):
- `app/modules/fakenodo/app.py` (marcado como deprecated)
- `app/modules/fakenodo/data/` (residuos de v1)

---

## Testing

### Ejemplo de test de integración

```python
# app/modules/dataset/tests/test_zenodo_integration.py
import pytest
from app.modules.zenodo.services import ZenodoService

@pytest.fixture
def zenodo_service():
    return ZenodoService()

def test_full_workflow(zenodo_service, sample_dataset):
    # 1. Crear deposición
    deposition = zenodo_service.create_new_deposition(sample_dataset)
    assert deposition['id'] is not None
    
    # 2. Subir archivo
    result = zenodo_service.upload_file(
        sample_dataset,
        deposition['id'],
        sample_feature_model
    )
    assert result['filename'] == 'model.uvl'
    
    # 3. Publicar
    published = zenodo_service.publish_deposition(deposition['id'])
    assert 'doi' in published
    assert published['doi'].startswith('10.5072/fakenodo.')
```

### Configuración de tests

```python
# conftest.py
import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def configure_fakenodo():
    os.environ["UPLOADS_USE_FAKENODO_ONLY"] = "true"
    os.environ["FAKENODO_URL"] = "http://127.0.0.1:5000/fakenodo/depositions"
```

---

## Resumen ejecutivo

**Fakenodo = Mock de Zenodo para desarrollo local**

- 🎯 **Propósito**: Evitar llamadas a API externa durante desarrollo
- 🏗️ **Arquitectura**: Blueprint Flask integrado (in-process)
- 💾 **Datos**: Solo en memoria (RAM), efímero
- 🔌 **API**: Compatible con endpoints básicos de Zenodo
- ✅ **Casos de uso**: Desarrollo local, tests automatizados
- ❌ **NO usar en**: Producción, datos reales

**Con Fakenodo puedes desarrollar y testear la funcionalidad de publicación de datasets sin necesidad de internet, credenciales o servicios externos.**
