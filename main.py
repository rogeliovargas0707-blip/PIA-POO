"""
Main del programa. Aqui se debe ejecutar el programa.
"""

import logging
from pathlib import Path

from conexion import ConexionDB, DB_Default_Path
from controlador import Controlador
from gui import GUITerminal


# ── Configuración de logging ───────────────────────────────────────────────────

def _configurar_logging(nivel: int = logging.INFO) -> None:
    """
    Configura logging a consola Y a archivo de log.
    El archivo se guarda junto a la BD para facilitar auditoría.
    """
    log_path = Path(__file__).parent / "libreria_acme.log"

    formato = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    logging.basicConfig(
        level=nivel,
        format=formato,
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler()
        ],
    )
    logging.getLogger(__name__).info("Logging inicializado. Archivo: %s", log_path)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    _configurar_logging()
    logger = logging.getLogger(__name__)

    logger.info("=== Iniciando Librería ACME ===")

    db = ConexionDB(DB_Default_Path)

    try:
        db.conectar()
        controlador = Controlador(db)
        vista = GUITerminal(controlador)
        vista.iniciar()
    except KeyboardInterrupt:
        print("\n\n  Interrupción del usuario. Cerrando...")
        logger.info("Aplicación interrumpida por el usuario (Ctrl+C).")
    except Exception as e:
        logger.exception("Error fatal no controlado: %s", e)
        print(f"\n  ERROR CRÍTICO: {e}")
        print("  Revisa libreria_acme.log para más detalles.")
        raise SystemExit(1)
    finally:
        db.cerrar()
        logger.info("=== Librería ACME finalizada ===")


if __name__ == "__main__":
    main()