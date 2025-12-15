# Guía de Contribución - Padel Hub

¡Gracias por contribuir a Padel Hub! Esta guía te ayudará a entender cómo trabajamos.

## 📌 Nota Importante

Este sistema de issues y convenciones de commits se implementó el **25 de noviembre de 2025**. Los commits anteriores a esta fecha no siguen estas convenciones, lo cual es normal durante la evolución del proyecto.

**A partir de ahora, todos los nuevos cambios deben seguir este proceso.**

---

## �📋 Tabla de Contenidos

- [Flujo de Trabajo](#flujo-de-trabajo)
- [Ramas](#ramas)
- [Convenciones de Commits](#convenciones-de-commits)
- [Manejo de Bugs](#manejo-de-bugs)
- [Desarrollo de Features](#desarrollo-de-features)
- [Versionado](#versionado)
- [Pull Requests y Merges](#pull-requests-y-merges)

---

## 🔄 Flujo de Trabajo

Trabajamos con ramas principales y ramas de trabajo:

**Ramas Principales:**
- **`main`**: Producción (solo código estable)
- **`trunk`**: Desarrollo (integración de features y fixes)
- **`bugfix`**: Corrección de errores

**Ramas de Trabajo (se borran después del merge):**
- **`feature/*`**: Nuevas funcionalidades
- **`document/*`**: Cambios de documentación

---

## 🌿 Ramas

### Ramas Principales

- **main**: Código en producción
- **trunk**: Rama de desarrollo principal
- **bugfix**: Rama compartida para corrección de bugs

### Ramas de Trabajo (se eliminan después del merge)

- **feature/nombre-descriptivo**: Para nuevas funcionalidades
  - Ejemplo: `feature/notificaciones-email`
  - Ejemplo: `feature/sistema-reservas`
  - Se crean desde `trunk`
  - **Se eliminan después del merge a trunk**

- **document/nombre-descriptivo**: Para cambios de documentación
  - Ejemplo: `document/api-guide`
  - Ejemplo: `document/contribution-update`
  - Se crean desde `trunk`
  - **Se eliminan después del merge a trunk**
  - Usan commits tipo `docs:`

---

## 💬 Convenciones de Commits

Usamos **Conventional Commits** para mantener un historial limpio y automatizar el versionado.

### Formato Obligatorio

Todos los commits deben seguir esta estructura de **3 partes**:

```
<tipo>: <título> (máximo 50 caracteres)

<descripción detallada obligatoria>
Explica el QUÉ y el POR QUÉ del cambio.
Puede ocupar múltiples líneas.
```

**Componentes obligatorios:**
1. **Línea 1**: Título con tipo (`feat:`, `fix:`, `docs:`) + descripción corta
2. **Línea 2**: Línea en blanco (separador)
3. **Línea 3+**: Descripción detallada (mínimo 1 línea de contenido)

⚠️ **El cuerpo es obligatorio** - el githook rechazará commits sin descripción detallada.

### Tipos de Commits

#### `fix:` - Corrección de Bugs
Corrige un error en el código. **Aumenta la versión MINOR** (1.0.0 → 1.1.0).

```bash
fix: fix Gmail authentication error
fix: fix memory leak in file upload
```

#### `feat:` - Nuevas Funcionalidades
Añade nueva funcionalidad. **Aumenta la versión MAJOR** (1.0.0 → 2.0.0).

```bash
feat: add email notification system
feat: implement advanced match search
```

#### `docs:` - Documentación
Cambios solo en documentación. **NO aumenta la versión** (sin deploy).

```bash
docs: update contribution guide
docs: add API documentation examples
docs: fix typos in README
```

### Commits y Merges

#### 📝 Para COMMITS (sin #número)

**Los commits requieren título Y descripción detallada:**

```bash
# ✅ COMMITS VÁLIDOS (usa git commit sin -m para abrir el editor)
git commit
# En el editor:
feat: añade sistema de notificaciones

Se implementa porque los usuarios necesitan saber cuando
hay nuevas actualizaciones en sus datasets. Agrega modelo
Notification, endpoints API y sistema de envío por email.

# ❌ COMMITS RECHAZADOS
git commit -m "fix: corrige validación"         # Sin descripción detallada
git commit -m "fix: corrige bug #123"           # No usar #número en commits
git commit -m "feat: añade feature. Closes #46" # No usar Closes en commits
git commit -m "arreglo bug"                     # Sin feat: o fix:
```

💡 **Tip**: Usa `git commit` (sin `-m`) para que se abra el editor con la plantilla que te guía.

⚠️ **Importante**: El cuerpo del commit es **obligatorio**. El githook valida que existan al menos:
- Línea 1: título con formato `feat:`, `fix:` o `docs:`
- Línea 2: en blanco
- Línea 3+: descripción detallada (mínimo 1 línea de contenido)

#### 🔀 Para MERGES

**A trunk/bugfix** (solo referencia, NO cierra):

```bash
# ✅ MERGES VÁLIDOS A TRUNK
git merge bugfix -m "fix: integra corrección #45"
git merge feature/nombre -m "feat: integra notificaciones #46"

# ❌ MERGES RECHAZADOS
git merge bugfix                                # Sin mensaje personalizado
git merge bugfix -m "merge bugfix"              # Sin feat:/fix:
git merge bugfix -m "fix: integra corrección"   # Sin #número
```

**A main** (cierre automático, Closes OBLIGATORIO):

```bash
# ✅ MERGES VÁLIDOS A MAIN
git merge trunk -m "feat: release notificaciones. Closes #46"
git merge bugfix -m "fix: release corrección crítica. Closes #45"

# ❌ MERGES RECHAZADOS EN MAIN
git merge trunk -m "feat: release notificaciones #46"  # Sin Closes
```

#### ⚠️ Cierre automático de issues

**IMPORTANTE**: Las issues **solo se cierran automáticamente cuando el commit con `Closes #número` llega a `main`** (rama default de GitHub).

**¿Cuándo usar `Closes`?**

```bash
# Bug NO crítico (solo trunk, NO main):
git merge bugfix -m "fix: integra corrección #45"
# ⚠️ NO usar Closes porque NO llegará a main
# → Cerrar MANUALMENTE en GitHub

# Bug crítico o Feature (trunk → main):
git merge trunk -m "fix: release corrección. Closes #45"
# ✅ SÍ usar Closes porque SÍ llega a main
# → Se cierra AUTOMÁTICAMENTE cuando llegue a main
```

**Resumen:**
- Si el merge **NO va a main** → NO uses `Closes` (cierre manual)
- Si el merge **SÍ va a main** → SÍ usa `Closes` (cierre automático)

#### 📝 Plantilla de Commits

Para facilitar el seguimiento de las convenciones, **configura la plantilla de commit**:

```bash
# Configurar la plantilla (solo una vez)
git config commit.template .gitmessage
```

**Después, SIEMPRE usa `git commit` (sin `-m`)** para que se abra el editor con la plantilla:

```bash
# ✅ CORRECTO: Abre el editor con la plantilla
git commit

# ❌ INCORRECTO: No permite descripción detallada
git commit -m "feat: añade funcionalidad"
```

Si necesitas título Y descripción con `-m`, usa dos `-m`:

```bash
git commit -m "feat: título" -m "Descripción detallada del cambio..."
```

#### 🔒 Validación de Commits (Git Hook)

El proyecto incluye un Git Hook que **valida automáticamente** el formato de los commits. Para instalarlo:

```bash
# Copiar el hook (solo una vez por desarrollador)
cp .githooks/commit-msg .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg
```

Una vez instalado, si intentas hacer un commit con formato incorrecto, **será rechazado automáticamente**:

```bash
# ❌ Esto será RECHAZADO (sin feat:/fix:)
git commit -m "arreglo bug"

# ❌ Esto será RECHAZADO (sin descripción)
git commit -m "fix: corrige error"

# ❌ Esto será RECHAZADO (con #número en commit)
git commit -m "fix: corrige error #45"

# ✅ Esto será ACEPTADO (título + descripción)
git commit -m "fix: corrige error de login" -m "El formulario no validaba correctamente emails vacíos."
```

---

## 🐛 Manejo de Bugs

### 1. Reportar el Bug

1. Ve a [Issues](../../issues)
2. Click en "New Issue"
3. Selecciona **"🐛 Bug Report"**
4. Completa el formulario con:
   - Descripción del bug
   - Pasos para reproducir
   - Comportamiento esperado vs actual
   - Prioridad (Alta/Media/Baja)
   - Tipo (Planificada/No planificada)
   - **Assignees** (quién trabajará en esto - obligatorio)
5. Crea la issue (ej: #45)

### 2. Trabajar en la Solución

```bash
# Cambiar a la rama bugfix
git checkout bugfix
git pull origin bugfix

# Realizar los cambios necesarios
# ... editar código ...

# Commitear (sin #número)
git add .
git commit -m "fix: corrige autenticación con emails Gmail"

# Subir a bugfix remoto
git push origin bugfix
```

### 3. Integrar la Solución

#### **Si el bug NO va a main** (solo trunk):

```bash
# Merge a trunk (con #número, SIN Closes)
git checkout trunk
git pull origin trunk
git merge bugfix -m "fix: integra corrección de autenticación #45"
git push origin trunk

# ⚠️ La issue #45 NO se cierra automáticamente (porque no llegó a main)
# Debes cerrar MANUALMENTE la issue #45 en GitHub
# 💡 El hook NO permite usar Closes aquí y te avisará si lo intentas
```

#### **Si el bug va a producción** (trunk → main):

```bash
# Paso 1: Merge a trunk (con #número, sin Closes)
git checkout trunk
git pull origin trunk
git merge bugfix -m "fix: integra corrección de autenticación #45"
git push origin trunk

# Paso 2: Merge a main (CON Closes OBLIGATORIO)
git checkout main
git pull origin main
git merge trunk -m "fix: release corrección de autenticación. Closes #45"
# ✅ El hook VALIDA que incluyas Closes porque estás en main
git push origin main
# ← Issue #45 se cierra AUTOMÁTICAMENTE ✅
# ← Workflow aumenta versión MINOR (1.0.0 → 1.1.0)
```

### 4. Cerrar la Issue

- **Si NO usaste `Closes #45`**: Cierra manualmente en GitHub
- **Si SÍ usaste `Closes #45`** y llegó a main: Se cerró automáticamente ✅

---

## ✨ Desarrollo de Features

### 1. Solicitar la Feature

1. Ve a [Issues](../../issues)
2. Click en "New Issue"
3. Selecciona **"✨ Feature Request"**
4. Completa el formulario con:
   - Descripción de la funcionalidad
   - Propuesta de solución
   - Prioridad (Alta/Media/Baja)
   - Tipo (Planificada/No planificada)
   - **Assignees** (quién trabajará en esto - obligatorio)
5. Crea la issue (ej: #46)

### 2. Desarrollar la Feature

```bash
# Crear rama desde trunk
git checkout trunk
git pull origin trunk
git checkout -b feature/nombre-descriptivo

# Desarrollar la funcionalidad
# ... editar código ...

# Commitear (sin #número)
git add .
git commit -m "feat: añade servicio de email"
git commit -m "feat: añade templates de notificaciones"
git commit -m "feat: integra notificaciones con eventos"

# Subir la rama
git push origin feature/nombre-descriptivo
```

### 3. Integrar la Feature

```bash
# Paso 1: Merge a trunk (con #número, sin Closes)
git checkout trunk
git pull origin trunk
git merge feature/nombre-descriptivo -m "feat: integra sistema de notificaciones #46"
# 💡 El hook te avisará si usas Closes aquí (no es main)
git push origin trunk
# ⚠️ Issue #46 AÚN ABIERTA (no llegó a main)

# Eliminar la rama feature después del merge
git branch -d feature/nombre-descriptivo
git push origin --delete feature/nombre-descriptivo

# Paso 2: Merge a main (CON Closes OBLIGATORIO)
git checkout main
git pull origin main
git merge trunk -m "feat: release sistema de notificaciones. Closes #46"
# ✅ El hook VALIDA que incluyas Closes porque estás en main
git push origin main
# ← Issue #46 se cierra AUTOMÁTICAMENTE ✅
# ← Workflow aumenta versión MAJOR (1.0.0 → 2.0.0)
```

### 4. Cerrar la Issue

La issue #46 se cerró automáticamente en el merge a main (porque usaste `Closes #46` y llegó a main).

---

## 📚 Cambios de Documentación

Para cambios que **solo afectan documentación** (sin código):

### 1. Crear Issue

1. Ve a [Issues](../../issues)
2. Click en "New Issue"
3. Selecciona **"📚 Documentation"**
4. Completa el formulario con:
   - Descripción del problema/mejora de documentación
   - Tipo de documentación (README, API, Contributing, etc.)
   - Cambios propuestos
   - Prioridad (Alta/Media/Baja)
   - **Assignees** (quién trabajará en esto - obligatorio)
5. Crea la issue (ej: #47)

### 2. Crear Rama document/

```bash
# Crear rama desde trunk
git checkout trunk
git pull origin trunk
git checkout -b document/nombre-descriptivo

# Ejemplo:
git checkout -b document/api-guide
git checkout -b document/contribution-update
```

### 3. Hacer Commits (tipo docs:)

```bash
# Editar documentación
# ... editar README.md, CONTRIBUTING.md, etc ...

# Commitear con docs: (sin #número)
git commit
# En el editor:
docs: update API documentation

Adds detailed examples for all endpoints, including
request/response formats and error codes.
```

### 4. Merge a trunk (sin versión, sin deploy)

```bash
# Merge a trunk (con #número si hay issue)
git checkout trunk
git pull origin trunk
git merge document/api-guide -m "docs: integrate API documentation #47"
git push origin trunk

# Eliminar la rama document
git branch -d document/api-guide
git push origin --delete document/api-guide
```

### 5. Merge a main (sin versión, sin deploy)

```bash
# Merge a main (CON Closes si hay issue)
git checkout main
git pull origin main
git merge trunk -m "docs: release API documentation. Closes #47"
git push origin main
# ✅ Issue #47 se cierra
# ⚠️ NO se crea tag
# ⚠️ NO se hace deploy
```

**Importante**: Los commits `docs:` NO activan el workflow de deploy, solo actualizan la documentación en GitHub.

---

## 🏷️ Versionado

Seguimos **Semantic Versioning** (MAJOR.MINOR.PATCH) con nuestra convención específica:

### Versión MINOR (X.1.0)
Se incrementa con commits tipo `fix:`
- Correcciones de bugs
- Hotfixes
- Parches de seguridad

**Ejemplo**: `1.0.0` → `1.1.0`

### Versión MAJOR (2.0.0)
Se incrementa con commits tipo `feat:`
- Nuevas funcionalidades
- Mejoras importantes

**Ejemplo**: `1.0.0` → `2.0.0`

### Sin Versión (docs:)
Los commits tipo `docs:` **NO incrementan versión**
- Solo cambios de documentación
- No se crea tag
- No se hace deploy a producción

**Nota**: Los cambios de documentación se reflejan en el repositorio sin generar una nueva versión.

### Automatización

El versionado se maneja automáticamente mediante GitHub Actions al hacer merge a `main`. El workflow:

1. Lee el tipo de commit (`fix:` o `feat:`)
2. Incrementa la versión correspondiente:
   - `fix:` → versión MINOR (1.0.0 → 1.1.0)
   - `feat:` → versión MAJOR (1.0.0 → 2.0.0)
3. Crea un tag en Git
4. Genera un release (opcional)

---

## 🔀 Pull Requests y Merges

### Nuestro Flujo (Sin PRs)

**No utilizamos Pull Requests**. En su lugar:

1. Trabajamos en ramas locales (`bugfix` o `feature/*`)
2. Hacemos **merge directo** a `trunk`
3. De `trunk` a `main` cuando sea necesario
4. **Borramos las ramas `feature/*`** después del merge a trunk

### Comandos de Merge

```bash
# Merge de bugfix a trunk
git checkout trunk
git merge bugfix
git push origin trunk

# Merge de feature a trunk
git checkout trunk
git merge feature/nombre-descriptivo
git push origin trunk

# Borrar rama feature después del merge
git branch -d feature/nombre-descriptivo
git push origin --delete feature/nombre-descriptivo

# Merge de trunk a main (producción)
git checkout main
git merge trunk
git push origin main
```

### Resolución de Conflictos

Si hay conflictos durante el merge:

```bash
# Ver archivos en conflicto
git status

# Editar los archivos manualmente y resolver conflictos

# Marcar como resueltos
git add <archivo-resuelto>

# Completar el merge
git commit
```

---

## 📊 Resumen: Validación del Hook por Rama

El hook `commit-msg` valida los mensajes automáticamente según la rama:

### Commits (cualquier rama):
```bash
✅ git commit  # Con editor (título + descripción)
✅ git commit -m "feat: título" -m "Descripción..."
❌ git commit -m "feat: título"  # Sin descripción
❌ git commit -m "feat: título #45"  # Con #número
❌ git commit -m "feat: título. Closes #45"  # Con Closes
```

### Merges a trunk/bugfix:
```bash
✅ git merge ... -m "feat: integra cambios #46"
⚠️  git merge ... -m "feat: integra cambios. Closes #46"  # Advierte pero acepta
❌ git merge ... -m "feat: integra cambios"  # Sin #número
```

### Merges a main:
```bash
✅ git merge ... -m "feat: release cambios. Closes #46"  # Obligatorio
❌ git merge ... -m "feat: release cambios #46"  # Sin Closes (RECHAZADO)
```

---

## ✅ Checklist Antes de Commitear

- [ ] El código compila sin errores
- [ ] Los tests pasan:
  - `rosemary test` (tests unitarios con pytest)
  - `rosemary selenium` (tests E2E con Selenium)
  - `rosemary locust` (tests de carga)
- [ ] El mensaje de commit tiene título Y descripción
- [ ] NO incluyes `#número` en commits individuales
- [ ] Incluyes `Closes #número` en merges a main
- [ ] El código sigue las convenciones del proyecto

---

## 🤝 Preguntas

Si tienes dudas sobre el flujo de trabajo, contacta al equipo o consulta la documentación del proyecto.

¡Gracias por contribuir! 🎾
