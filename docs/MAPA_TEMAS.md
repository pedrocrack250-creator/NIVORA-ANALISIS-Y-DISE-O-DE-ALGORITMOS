# Mapa de temas de la asignatura → código de Nivora

Distingue dónde se **usa** cada tema (parte del funcionamiento de la plataforma)
de dónde solo se **enseña o explora** (Laboratorio de algoritmos).

## A. Aplicados al funcionamiento de la plataforma

| Tema | Dónde se usa | Archivos |
|---|---|---|
| Divide y vencerás, ordenamiento, Merge Sort (8, 9, 10) | Define el orden de las unidades de la ruta, que decide el desbloqueo, y ordena en Progreso las lecciones por repasar (menor acierto primero, estable) | `services/progreso_service.py` (`estado_unidades`, `lecciones_para_repasar`) → `services/algoritmos/merge_sort.py` |
| Algoritmos voraces y selección local (12, 13) | Recomienda la siguiente pregunta en Aprender y al terminar un quiz, con intentos y errores reales por pregunta, solo entre lecciones ya desbloqueadas | `services/recomendacion_service.py` → `services/algoritmos/voraz.py`; datos de `ExerciseRepository.find_quiz_questions` y `PROGRESO_EJERCICIO` |
| Complejidad temporal y espacial (2, 3) | Cada módulo documenta su complejidad; las mediciones reales se muestran en el Laboratorio | docstrings de `services/algoritmos/*.py` |

## B. Laboratorio de algoritmos (se ejecutan de verdad, pero no sostienen el resto de la app)

| Tema | Actividad | Archivos |
|---|---|---|
| Análisis, complejidad, Big O, eficiencia (1–5) | Conteo real de comparaciones de Merge Sort y Quick Sort en mejor, promedio y peor caso, con cotas teóricas | `services/algoritmos/analisis.py`, `templates/laboratorio/eficiencia.html` |
| Relaciones de recurrencia y su resolución (6, 7) | Tres recurrencias resueltas (árbol de recursión, sustitución, ecuación característica) y teorema maestro, verificadas contra el conteo real | `analisis.py` (`recurrencia_*`, `teorema_maestro`, `verificar_recurrencias`) |
| Quick Sort (11) | Partición de Lomuto con contadores; peor caso exacto n(n-1)/2 | `services/algoritmos/quick_sort.py` |
| Programación dinámica, memoización, tabulación (19, 20, 21) | Escaleras con recursión pura, memoización y tabulación | `services/algoritmos/programacion_dinamica.py` |
| Backtracking y 4 reinas (22, 23) | Solucionador con rastro de intentos, podas y retrocesos | `services/algoritmos/backtracking.py` |
| Grafos, MST, Prim, Kruskal, Union-Find (14–18) | Contenido educativo con ejemplos ejecutados sobre un grafo fijo de 5 vértices | `prim.py`, `kruskal.py`, `union_find.py` |

## Limitaciones declaradas

- Grafos, Prim, Kruskal y Union-Find no intervienen en la lógica de la app: la ruta
  es una cadena lineal de prerrequisitos y no necesita un árbol de expansión mínima.
- Quick Sort no se usa en el funcionamiento de la plataforma: Merge Sort es estable
  y por eso es el que ordena datos reales.
- Programación dinámica y backtracking son actividades de exploración por naturaleza.
