from repositories.progress_repository import ProgressRepository
from database.database import DatabaseConnection
from services.algoritmos.voraz import recomendar_siguiente


def test_recomienda_pendiente_con_mas_errores():
    ejercicios = [
        {"id_ejercicio": 1, "estado": "pendiente", "errores": 0,
         "dificultad": "basico", "numero": 1},
        {"id_ejercicio": 2, "estado": "incorrecto", "errores": 3,
         "dificultad": "avanzado", "numero": 2},
        {"id_ejercicio": 3, "estado": "incorrecto", "errores": 2,
         "dificultad": "basico", "numero": 3},
    ]

    assert recomendar_siguiente(ejercicios)["id_ejercicio"] == 2


def test_desempata_por_menor_dificultad_y_posicion():
    ejercicios = [
        {"id_ejercicio": 3, "estado": "incorrecto", "errores": 1,
         "dificultad": "intermedio", "numero": 1},
        {"id_ejercicio": 2, "estado": "incorrecto", "errores": 1,
         "dificultad": "basico", "numero": 2},
        {"id_ejercicio": 1, "estado": "incorrecto", "errores": 1,
         "dificultad": "basico", "numero": 1},
    ]

    assert recomendar_siguiente(ejercicios)["id_ejercicio"] == 1


def test_no_recomienda_si_todo_esta_correcto():
    ejercicios = [
        {"id_ejercicio": 1, "estado": "correcto", "errores": 2,
         "dificultad": "basico", "numero": 1},
    ]
    assert recomendar_siguiente(ejercicios) is None


def test_guarda_intentos_aciertos_y_errores_en_base_temporal(tmp_path):
    database = DatabaseConnection(config={"database_path": str(tmp_path / "nivora_test.db")})
    database.connect().close()
    repository = ProgressRepository(database)

    repository.save_exercise_attempt(7, 1, False)
    repository.save_exercise_attempt(7, 1, True)
    repository.save_exercise_attempt(7, 1, False)

    progress = repository.find_exercise_progress(7)[1]
    assert progress["estado"] == "incorrecto"
    assert progress["intentos"] == 3
    assert progress["aciertos"] == 1
    assert progress["errores"] == 2
