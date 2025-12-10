# CI/CD Workflows - Padel Hub

Esta documentación explica los workflows automatizados de GitHub Actions que gestionan la integración continua (CI) y despliegue continuo (CD) del proyecto.

## 🔄 Resumen de Workflows

| Workflow | Tipo | Trigger | Propósito |
|----------|------|---------|-----------|
| **codacy.yml** | CI | push a `trunk` | Análisis de calidad y tests |
| **deploy-trunk.yml** | CD | push a `trunk` | Deploy a preproducción |
| **tag-and-deploy.yml** | CI/CD | push a `main` | Tests, versionado y deploy a producción |
| **auto-manage.yml** | Automatización | issues opened/edited | Gestión automática de issues |

---

## 🧪 Integración Continua (CI)

### 1. Codacy CI (`codacy.yml`)
**Trigger:** Push a rama `trunk`

**Funciones:**
- ✅ Verifica dependencias desactualizadas
- 🧪 Ejecuta tests en Python 3.11 y 3.12 con MySQL
- 📊 Genera reporte de cobertura de código
- 📈 Sube métricas a Codacy para análisis de calidad
- 🔒 Ejecuta análisis de seguridad

**Propósito:** Validar calidad del código antes de merge a `main`

### 2. Deploy to Production - Testing Phase (`tag-and-deploy.yml`)
**Trigger:** Push a rama `main`

**Funciones CI:**
- 🧪 Ejecuta todos los tests (excepto Selenium) con MySQL
- ✅ Valida que el código esté listo para producción

---

## 🚀 Despliegue Continuo (CD)

### 1. Deploy to Preproduction (`deploy-trunk.yml`)
**Trigger:** Push a rama `trunk`

**Funciones:**
- 🚀 Despliega automáticamente a entorno de preproducción en Render
- ✅ Verifica que el webhook se ejecute correctamente

**Propósito:** Permitir testing en entorno similar a producción antes de merge a `main`

### 2. Deploy to Production (`tag-and-deploy.yml`)
**Trigger:** Push a rama `main`

**Proceso completo:**
1. **Testing** - Ejecuta tests completos
2. **Version Detection** - Analiza commit para determinar tipo de versión
3. **Tag Creation** - Crea tag Git con nueva versión
4. **Release Creation** - Crea GitHub Release (solo para versiones MAJOR)
5. **Production Deploy** - Despliega a producción en Render

---

## 📋 Sistema de Versionado Semántico

El workflow `tag-and-deploy.yml` implementa versionado automático basado en **Conventional Commits**:

### Detección de Tipo de Versión

| Prefijo de Commit | Tipo de Versión | Incremento | Deploy | Release |
|-------------------|-----------------|------------|---------|---------|
| `docs:` | PATCH | +0.0.1 | ❌ No | ❌ No |
| `fix:` | MINOR | +0.1.0 | ✅ Sí | ❌ No |
| `feat:` (o otros) | MAJOR | +1.0.0 | ✅ Sí | ✅ Sí |

### Ejemplos de Versionado

```bash
# Commit de documentación
git commit -m "docs: update API documentation"
# → Crea tag v1.2.4 (PATCH +0.0.1)
# → NO despliega (solo documentación)

# Commit de bugfix
git commit -m "fix: resolve email validation error"
# → Crea tag v1.3.0 (MINOR +0.1.0)
# → Despliega a producción
# → NO crea GitHub Release

# Commit de feature
git commit -m "feat: add notification system"
# → Crea tag v2.0.0 (MAJOR +1.0.0)
# → Despliega a producción
# → Crea GitHub Release
```

### Algoritmo de Tag Disponible

El sistema busca automáticamente el primer tag disponible si ya existe:
- Si `v2.0.0` existe, intenta `v2.0.1`, `v2.0.2`, etc.
- Garantiza que no haya conflictos de versionado

---

## 🎯 Automatización de Issues

### Auto-Manage Issues (`auto-manage.yml`)
**Trigger:** Issues created o edited

**Funciones:**
- 👥 **Auto-asignación:** Parsea la sección "Assignees" y asigna automáticamente
- 📋 **Gestión de proyecto:** Añade issues al board "padel-hub Board"
- 🏷️ **Etiquetado por prioridad:**
  - High → `priority: high`
  - Medium → `priority: medium`
  - Low → `priority: low`

---

## 🛠️ Configuración de Entornos

### Secretos Requeridos

| Secret | Propósito | Usado en |
|--------|-----------|----------|
| `PAT_TOKEN` | Crear tags y releases | tag-and-deploy.yml |
| `RENDER_DEPLOY_HOOK_URL` | Deploy producción | tag-and-deploy.yml |
| `RENDER_DEPLOY_HOOK_PADELHUB_URL` | Deploy preproducción | deploy-trunk.yml |
| `CODACY_PROJECT_TOKEN` | Subir métricas de calidad | codacy.yml |

### Servicios de Base de Datos

Todos los workflows de testing usan **MySQL 5.7** como servicio:
```yaml
services:
  mysql:
    image: mysql:5.7
    env:
      MYSQL_ROOT_PASSWORD: padelhub_root_password
      MYSQL_DATABASE: padelhubdb_test
      MYSQL_USER: padelhub_user
      MYSQL_PASSWORD: padelhub_password
```

---

## 🔄 Flujo de Trabajo Completo

### Desarrollo de Features
```bash
feature/* → trunk → preproducción (deploy-trunk.yml)
                 → calidad (codacy.yml)
          → main → producción (tag-and-deploy.yml)
```

### Desarrollo de Fixes
```bash
bugfix → trunk → preproducción (deploy-trunk.yml)
              → calidad (codacy.yml)
       → main → producción (tag-and-deploy.yml)
```

### Documentación
```bash
docs/* → trunk → preproducción (deploy-trunk.yml)
             → calidad (codacy.yml)
      → main → versionado PATCH (tag-and-deploy.yml)
              → SIN despliegue (solo docs)
```

---

## 📈 Monitoreo y Calidad

- **Codacy Dashboard:** Métricas automáticas de calidad y cobertura
- **GitHub Releases:** Registro automático de versiones MAJOR
- **Render Deployments:** Seguimiento de despliegues automáticos
- **MySQL Testing:** Tests completos con base de datos real

Este sistema garantiza código de calidad, despliegues automáticos y versionado consistente siguiendo mejores prácticas de DevOps.