# Nivora

Aplicacion Flask para aprender Python.

## Desarrollo

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:NIVORA_SECRET_KEY = "clave-local-de-desarrollo"
flask --app app run --debug
```

## Pruebas

```powershell
python -m pytest -q
```

Las pruebas crean una base SQLite temporal independiente por instancia de la aplicación; no modifican `database/nivora.db`.

## Laboratorio de algoritmos

El Laboratorio forma parte de **Aprender**: aparece como una sección propia
después de las cuatro unidades (`/aprender#laboratorio`) y sus páginas viven en
`/aprender/laboratorio/...`. Las antiguas URL de `/practica` redirigen allí. Incluye actividades interactivas de Merge Sort, programación dinámica, Backtracking y el algoritmo voraz, además de contenido educativo de Kruskal, Prim y Union-Find. La recomendación Voraz utiliza los resultados guardados de los quizzes.

## Producción

Configura `NIVORA_SECRET_KEY` con una clave aleatoria larga, `NIVORA_DATABASE_PATH` con la ruta de la base de datos y `NIVORA_COOKIE_SECURE=1` cuando se use HTTPS. Ejecuta `deploy.sh` en un entorno Linux con Gunicorn. No actives `FLASK_DEBUG` en producción.
## Recomendación Voraz (Fase 5)

Al evaluar un quiz, Nivora registra por pregunta el último estado, el total de
intentos, los aciertos y los errores en `PROGRESO_EJERCICIO`. La página
`Laboratorio · Algoritmo voraz` recomienda una pregunta pendiente con esta prioridad:

1. Mayor cantidad de respuestas incorrectas acumuladas.
2. Menor dificultad (`basico`, `intermedio`, `avanzado`).
3. Menor posición dentro de la lección.

Es una heurística voraz local; no pretende calcular una ruta de aprendizaje
óptima. En el esquema actual `USUARIO.id_persona` es su clave primaria, por lo
que ese identificador se guarda en `PROGRESO_EJERCICIO.id_usuario`.

## Ruta de aprendizaje y progreso

- Las cuatro unidades tienen 4 lecciones cada una con un quiz de 3 preguntas.
- `services/progreso_service.py` concentra las reglas: una unidad se completa
  cuando todas sus lecciones están completadas y la siguiente se desbloquea
  entonces; la unidad 01 está disponible desde el inicio.
- Abrir una lección crea su registro en `PROGRESO_LECCION` (sin intentarla ni
  completarla). La recomendación inicial de Aprender se muestra solo mientras el
  usuario no tenga ningún registro de lección; el nivel elegido se guarda en
  `USUARIO.nivel` para conservar la recomendación entre sesiones.
