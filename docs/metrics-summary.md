# Resumen de Métricas - PadelHub

**Última actualización:** 15 de diciembre de 2025 - 12:37 PM  
**Estado:** Métricas congeladas para entrega final. Incluye cambios hasta el commit anterior.

## Métricas Generales

- **Total de Commits:** 126
- **Líneas de Código (LoC):** 35,877 líneas netas
- **Total de Tests:** 169 funciones de test
- **Issues Cerradas:** 38

## Distribución por Desarrollador

| Desarrollador | Commits | LoC Añadidas | LoC Eliminadas | LoC Netas | Tests | Issues |
|--------------|---------|--------------|----------------|-----------|-------|--------|
| Guillermo Linares | 32 | 21,679 | 3,469 | 18,210 | 63 | 8 |
| Javier Pallarés | 29 | 1,350 | 671 | 679 | 27 | 9 |
| Celia Dorantes | 23 | 2,477 | 918 | 1,559 | 21 | 7 |
| José María Silva | 22 | 1,383 | 557 | 826 | 7 | 5 |
| Darío Zafra | 20 | 16,218 | 1,615 | 14,603 | 51 | 9 |
| **TOTAL** | **126** | **43,107** | **7,230** | **35,877** | **169** | **38** |

## Metodología de Conteo

- **Commits:** `git log --all --pretty="%an" | sort | uniq -c` (todos los commits del repositorio)
- **LoC:** `git log --author="nombre" --numstat` analizado con awk (líneas añadidas - eliminadas)
- **Tests:** `git log -p | grep "^\+.*def test_"` (funciones de test añadidas)
- **Issues:** GitHub Projects (incluye issues migradas de ZenHub, período Oct-Dic 2025)

## Referencias

- Detalles de commits: `docs/metrics-commits.log`
- Análisis detallado de LoC: `docs/metrics-detailed.log`
- Distribución de tests e issues: `docs/metrics-tests.log`
