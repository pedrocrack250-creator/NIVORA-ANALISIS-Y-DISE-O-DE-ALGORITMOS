from models.ruta_model import RutaModel


class ProgresoModel:

    @staticmethod
    def obtener_progreso(usuario_id=None, actividades=None):
        # Usa el mismo cálculo que la ruta de Aprender (services.progreso_service)
        # para que ambas pantallas muestren siempre el mismo avance real.
        rutas = RutaModel.obtener_rutas(actividades or {})
        general_completadas = sum(ruta["completadas"] for ruta in rutas)
        general_total = sum(ruta["total"] for ruta in rutas)

        return {
            "general": {
                "completadas": general_completadas,
                "total": general_total,
                "porcentaje": _porcentaje(general_completadas, general_total),
            },
            "rutas": [
                {
                    "nombre": ruta["nombre"],
                    "completadas": ruta["completadas"],
                    "total": ruta["total"],
                    "porcentaje": _porcentaje(ruta["completadas"], ruta["total"]),
                }
                for ruta in rutas
            ],
        }


def _porcentaje(completadas, total):
    return round(completadas / total * 100) if total else 0
