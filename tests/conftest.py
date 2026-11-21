import pytest

# Respuestas correctas de los quizzes, por unidad y en el orden de la ruta.
RESPUESTAS_CORRECTAS = {
    "01": {
        "variables": ["nombre", "int", "True"],
        "operadores": ["7", "True", "=="],
        "entrada_salida": ["print", "input", "texto"],
        "repaso_fundamentos": ["lista", "len", "append"],
    },
    "02": {
        "condicionales": ["if", "else", "B"],
        "elif": ["elif", "uno", "and"],
        "ciclo_for": ["0, 1, 2", "5", "for"],
        "ciclo_while": ["falsa", "break", "continue"],
    },
    "03": {
        "listas": ["0", "20", "7"],
        "metodos_listas": ["pop", "sort", "remove"],
        "tuplas": ["()", "no", "4"],
        "diccionarios": ["{}", "20", "keys"],
    },
    "04": {
        "definir_funciones": ["def", "saludar()", ":"],
        "parametros": ["parametros", "Hola", "2"],
        "retorno": ["return", "None", "8"],
        "repaso_funciones": ["no", "recursiva", "4"],
    },
}


@pytest.fixture
def respuestas_correctas():
    return RESPUESTAS_CORRECTAS
