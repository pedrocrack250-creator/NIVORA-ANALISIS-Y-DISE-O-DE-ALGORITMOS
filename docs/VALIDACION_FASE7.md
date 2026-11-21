# Validación e integración — Fase 7

## Alcance revisado

- Navegación principal: Aprender, Practicar, Progreso y acceso al Laboratorio desde Practicar.
- Actividades interactivas: Merge Sort, programación dinámica y Backtracking.
- Contenido educativo: Kruskal, Prim y Union-Find.
- Recomendación Voraz basada en intentos, aciertos y errores registrados por pregunta.
- Persistencia SQLite, creación de esquema en una base limpia y migración de `PROGRESO_EJERCICIO`.

## Correcciones de integración

1. `DatabaseConnection` ahora crea `PERSONA` y `USUARIO` cuando la base está vacía, con las columnas utilizadas por `UserRepository`.
2. La migración añade `aciertos` y `errores` a instalaciones antiguas de `PROGRESO_EJERCICIO` y crea el índice único requerido por el `UPSERT`.
3. `DatabaseConnection` respeta `DATABASE_PATH` de la aplicación Flask.
4. Cada instancia de `TestingConfig` recibe una base temporal independiente, evitando modificar `database/nivora.db` durante las pruebas.
5. `app.py` conserva la clave `NIVORA_SECRET_KEY` configurada, en lugar de regenerar una clave aleatoria en cada arranque.

## Comprobaciones ejecutadas en el entorno de preparación

- Compilación de todos los módulos Python con `python -m compileall -q .`: correcta.
- Inicialización de una base SQLite vacía y creación de un usuario en `PERSONA` y `USUARIO`: correcta.
- Migración de una tabla `PROGRESO_EJERCICIO` antigua conservando registros: correcta.
- Comprobación funcional aislada de Merge Sort, escaleras con memoización, 4 reinas, recomendación Voraz, Kruskal, Prim y Union-Find: correcta.
- Comparación del costo del árbol mínimo del grafo educativo: Kruskal y Prim devuelven 10.

## Pruebas completas pendientes de ejecutar en el equipo de desarrollo

El entorno de preparación no dispone de Flask ni Werkzeug y no tiene acceso a Internet para instalarlos. Por eso no se pudo recolectar ni ejecutar la suite completa de pytest aquí. Ejecutar en el equipo local, dentro del entorno virtual del proyecto:

```bash
pip install -r requirements.txt
python -m pytest -q
```

Después, iniciar la aplicación y revisar el flujo completo en navegador:

```bash
flask --app app run --debug
```

Lista de comprobación manual:

- [ ] Registro de una cuenta nueva en una base limpia.
- [ ] Inicio y cierre de sesión.
- [ ] Completar un quiz y verificar que se actualicen los intentos, aciertos y errores.
- [ ] Volver a Practicar y comprobar que la recomendación Voraz use esos datos.
- [ ] Abrir la lista de ejercicios y cambiar el criterio de Merge Sort.
- [ ] Ejecutar la actividad de programación dinámica con varios valores de `n`.
- [ ] Reproducir los pasos y retrocesos de las 4 reinas.
- [ ] Abrir Kruskal, Prim y Union-Find desde el índice educativo.
- [ ] Comprobar que Aprender y Progreso conservan su comportamiento.

> No marcar las casillas de comprobación manual hasta realizar las pruebas en el navegador.
