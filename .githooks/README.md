# Git Hooks

Este directorio contiene Git Hooks personalizados para el proyecto.

## ¿Qué son los Git Hooks?

Son scripts que Git ejecuta automáticamente en ciertos eventos (commit, push, etc.). Ayudan a mantener la calidad y consistencia del código.

## Instalación

⚠️ **Los Git Hooks NO se copian automáticamente**. Cada desarrollador debe instalarlos manualmente:

```bash
# Desde la raíz del proyecto
cp .githooks/commit-msg .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg
```

## Hook: commit-msg

Valida que commits y merges sigan el formato requerido.

**Detección inteligente**: El hook detecta automáticamente si es un commit normal o un merge usando:
1. `git rev-parse MERGE_HEAD` - Detecta merges en progreso
2. Busca "Merge branch" en el mensaje - Fallback para compatibilidad

Esto funciona **incluso con mensajes personalizados** (`-m`).

### ✅ Formato válido para COMMITS (sin #número):
```bash
feat: add notification system

Implemented because users need to know when there are new
updates to their datasets. Adds Notification model, API
endpoints and email sending system.
```

```bash
fix: fix login error

Form was not validating empty emails correctly.
Adds validation in frontend and backend.
```

### ✅ Formato válido para MERGES (con #número obligatorio):
```bash
git merge bugfix -m "fix: integrate fix #45"
git merge bugfix -m "fix: integrate fix. Closes #45"
git merge feature/name -m "feat: integrate notifications. Closes #46"
```

### ❌ Formato inválido:
```bash
# COMMITS
arreglo bug                         # Sin feat: o fix:
feat: añade feature #46             # No usar # en commits
fix: corrige bug. Closes #45        # No usar Closes en commits

# MERGES
git merge bugfix                    # Sin mensaje personalizado
git merge bugfix -m "merge bugfix"  # Sin feat:/fix:
git merge bugfix -m "fix: integra"  # Sin #número
```

### Validaciones:

#### Para COMMITS:
1. **Obligatorio**: Debe empezar con `feat:` o `fix:`
2. **Obligatorio**: Debe tener título Y descripción detallada
3. **Obligatorio**: Debe haber una línea en blanco entre título y descripción
4. **Prohibido**: NO usar `#número`
5. **Prohibido**: NO usar `Closes/Fixes/Resolves`

💡 **Tip**: Usa `git commit` (sin `-m`) para que se abra el editor con la plantilla completa.

#### Para MERGES a trunk/bugfix:
1. **Obligatorio**: Mensaje personalizado (no automático)
2. **Obligatorio**: Debe empezar con `feat:` o `fix:`
3. **Obligatorio**: Debe incluir `#número`
4. **NO usar** `Closes` (el hook te avisará si lo usas)

#### Para MERGES a main:
1. **Obligatorio**: Mensaje personalizado (no automático)
2. **Obligatorio**: Debe empezar con `feat:` o `fix:`
3. **Obligatorio**: Debe incluir `Closes/Fixes/Resolves #número`
   - ✅ Esto cierra automáticamente la issue en GitHub
   - ❌ El hook rechazará el merge si no incluyes `Closes`

### Ejemplo de uso:

```bash
# ===== COMMITS =====

# ❌ Sin feat: o fix:
git commit -m "arreglo bug"
# ERROR: El mensaje no sigue el formato correcto
# RECHAZADO ❌

# ❌ Con #número (no permitido en commits)
git commit -m "fix: corrige error #45"
# ERROR: Los commits NO deben incluir #número
# RECHAZADO ❌

# ❌ Commit con solo título (sin descripción)
git commit -m "fix: corrige error de login"
# ERROR: El commit debe tener título Y descripción
# RECHAZADO ❌

# ✅ Formato correcto para commits (usa el editor)
git commit
# Se abre el editor con la plantilla:
# feat: añade sistema de notificaciones
# 
# Se implementa porque los usuarios necesitan...
# ACEPTADO ✅

# ===== MERGES A TRUNK/BUGFIX =====

# ❌ Merge sin mensaje personalizado
git merge bugfix
# ERROR: Los merges DEBEN tener mensaje personalizado
# RECHAZADO ❌

# ❌ Merge sin #número
git merge bugfix -m "fix: integra corrección"
# ERROR: Los merges deben incluir #número
# RECHAZADO ❌

# ⚠️  Merge con Closes (advertencia pero acepta)
git merge bugfix -m "fix: integra corrección. Closes #45"
# ADVERTENCIA: La issue NO se cerrará porque no estás en 'main'
# ACEPTADO ⚠️

# ✅ Merge correcto a trunk
git merge bugfix -m "fix: integra corrección #45"
git merge feature/nombre -m "feat: integra notificaciones #46"
# ACEPTADO ✅
# Issue permanece ABIERTA

# ===== MERGES A MAIN =====

# ❌ Merge sin Closes (rechazado en main)
git merge trunk -m "feat: release notificaciones #46"
# ERROR: Los merges a MAIN deben incluir 'Closes #número'
# RECHAZADO ❌

# ✅ Merge correcto a main (cierre automático)
git merge trunk -m "feat: release notificaciones. Closes #46"
git merge bugfix -m "fix: release corrección. Closes #45"
# ACEPTADO ✅
# Issues se cierran AUTOMÁTICAMENTE en GitHub
```

## Desactivar temporalmente (no recomendado)

Si necesitas hacer un commit sin validación (emergencia):

```bash
git commit --no-verify -m "mensaje"
```

**⚠️ Úsalo solo en casos excepcionales.**
