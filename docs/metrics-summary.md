# Métricas del Proyecto PadelHub

**Generado:** 10 de diciembre de 2025

## Resumen por Miembro del Equipo

### Guillermo Linares Borrego (@Glinbor10)
- **Commits:** 27
- **Líneas añadidas:** 18,929
- **Líneas eliminadas:** 1,538
- **LoC neto:** 17,391
- **Archivos de test modificados:** 21
- **Funciones de test añadidas:** ~59

### Celia Dorantes (@celdorrui)
- **Commits:** 20
- **Líneas añadidas:** 1,696
- **Líneas eliminadas:** 165
- **LoC neto:** 1,531
- **Archivos de test modificados:** 9
- **Funciones de test añadidas:** ~21

### Javier Pallarés González (@javpalgon)
- **Commits:** 16
- **Líneas añadidas:** 887
- **Líneas eliminadas:** 262
- **LoC neto:** 625
- **Archivos de test modificados:** 2
- **Funciones de test añadidas:** ~27

### Darío Zafra Ruiz (@darzafrui)
- **Commits:** 11
- **Líneas añadidas:** 16,036
- **Líneas eliminadas:** 1,403
- **LoC neto:** 14,633
- **Archivos de test modificados:** 16
- **Funciones de test añadidas:** ~44

### José María Silva Guzmán (@jossilguz)
- **Commits:** 8
- **Líneas añadidas:** 2,901
- **Líneas eliminadas:** 1,525
- **LoC neto:** 1,376
- **Archivos de test modificados:** 2
- **Funciones de test añadidas:** ~5

---

## TOTALES DEL PROYECTO

| Métrica | Valor |
|---------|-------|
| **Commits totales** | 82 |
| **Líneas añadidas** | 40,449 |
| **Líneas eliminadas** | 4,893 |
| **LoC neto total** | 35,556 |
| **Archivos de test únicos** | ~50 |
| **Funciones de test** | ~156 |

---

## Comandos Utilizados para Generar Métricas

### 1. Commits por autor
```bash
git log --all --pretty="%an" | sort | uniq -c | sort -rn
```

**Resultado guardado en:** [`metrics-commits.log`](metrics-commits.log)

### 2. Líneas de código por autor
```bash
for author in "Guillermo Linares Borrego" "Celia Dorantes" "Javier Pallarés González" "darzafrui" "JOSE MARIA SILVA GUZMAN"; do
  echo "=== $author ==="
  echo "Commits: $(git log --all --author="$author" --oneline | wc -l)"
  git log --all --author="$author" --pretty=tformat: --numstat | \
    awk '{added+=$1; removed+=$2} END {print "Lines added:", added, "Lines removed:", removed, "Net LoC:", added-removed}'
  echo ""
done
```

**Resultado guardado en:** [`metrics-detailed.log`](metrics-detailed.log)

### 3. Tests por autor
```bash
for author in [lista de autores]; do
  echo "=== $author ==="
  # Archivos de test modificados
  git log --all --author="$author" --name-only --pretty=format: | \
    grep -E "test_.*\.py$|.*_test\.py$" | sort -u | wc -l
  # Funciones de test añadidas
  git log --all --author="$author" -p | grep -E "^\+.*def test_" | wc -l
  echo ""
done
```

**Resultado guardado en:** [`metrics-tests.log`](metrics-tests.log)

---

## Notas Metodológicas

- **LoC (Lines of Code):** Incluye todos los tipos de archivos (Python, YAML, Markdown, JSON, etc.)
- **Tests:** Aproximación basada en funciones que comienzan con `def test_` en archivos de test Python
- **Periodo:** Octubre 2024 - Diciembre 2024
- **Exclusiones:** No se excluyen dependencias iniciales ni código generado; los números reflejan contribuciones brutas al repositorio
- **Test files:** Conteo de archivos únicos que contienen `test_` en el nombre o terminan en `_test.py`

---

## Verificación

Para verificar estos números en tu máquina local:

```bash
# Clonar el repositorio
git clone https://github.com/EGC-PadelHub/padel-hub.git
cd padel-hub

# Verificar commits totales
git log --all --oneline | wc -l

# Verificar commits por autor
git log --all --pretty="%an" | sort | uniq -c | sort -rn

# Ver logs completos
cat docs/metrics-*.log
```
