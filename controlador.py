"""
controlador.py
=============
"""
import logging
from typing import Optional

from modelos import Libro
from conexion import ConexionDB
from login import SesionManager, SesionNoIniciadaError

logger = logging.getLogger(__name__)


class Controlador:
    """
    Punto de entrada para todas las acciones de la aplicación.

    Parameteros
    ----------
    db : ConexionDB
        Instancia *ya conectada* de la base de datos.
    """

    def __init__(self, db: ConexionDB) -> None:
        self._db = db
        self._sesion = SesionManager(db)

    # --- Propiedades de sesión (para que la GUI consulte estado) ---
    @property
    def hay_sesion(self) -> bool:
        return self._sesion.hay_sesion

    @property
    def usuario_activo(self):
        return self._sesion.usuario_activo

    # --- Autenticacion ---

    def iniciar_sesion(self, username: str, password: str) -> bool:
        """Intenta iniciar sesion con las credenciales dadas, devuelve True si tiene exito, False si falla"""
        try:
            usuario = self._sesion.iniciar_sesion(username, password)
            return usuario is not None  
        except PermissionError:
            raise   # la GUI decide cómo mostrar este error

    def cerrar_sesion(self) -> None:
        self._sesion.cerrar_sesion()
        logger.info("Controlador: sesión cerrada.")
    
    # --- Operaciones de empleado ---
    def agregar_libro(
        self,
        titulo: str,
        autor: str,
        genero: str,
        isbn: str,
        cantidad: int,
    ) -> Libro:
        """
        Crea y persiste un libro nuevo.
        Solo disponible para empleados autenticados.
        """
        self._sesion.requiere_empleado()
        libro = Libro(
            titulo=titulo,
            autor=autor,
            genero=genero,
            isbn=isbn,
            cantidad=cantidad,
        )
        self._db.agregar_libro(libro)
        logger.info("Controlador: libro agregado → %r", libro)
        return libro

    def editar_libro(
        self,
        id_libro: int,
        titulo: str,
        autor: str,
        genero: str,
        isbn: str,
        cantidad: int,
    ) -> Libro:
        """
        Modifica los datos de un libro existente.
        Solo disponible para empleados autenticados.
        """
        self._sesion.requiere_empleado()

        libro = self._db.obtener_libro_por_id(id_libro)
        if libro is None:
            raise ValueError(f"No se encontró libro con ID={id_libro}.")

        # Actualizar campos mediante los setters con validación
        libro.titulo   = titulo
        libro.autor    = autor
        libro.genero   = genero
        libro.isbn     = isbn
        libro.cantidad = cantidad

        self._db.editar_libro(libro)
        logger.info("Controlador: libro editado → %r", libro)
        return libro

    def borrar_libro(self, id_libro: int) -> None:
        """
        Elimina un libro por ID.
        Solo disponible para empleados autenticados.
        """
        self._sesion.requiere_empleado()
        self._db.borrar_libro(id_libro)
        logger.info("Controlador: libro ID=%d eliminado.", id_libro)

    # ── Operaciones públicas (empleados y clientes) ────────────────────────────

    def buscar_libros(self, criterio: str, valor: str) -> list[Libro]:
        """
        Busca libros por criterio (titulo, autor, genero, isbn).
        Disponible para empleados Y clientes sin autenticación.
        """
        criterio = criterio.lower().strip()
        valor    = valor.strip()
        if not valor:
            raise ValueError("El valor de búsqueda no puede estar vacío.")
        return self._db.buscar_libros(criterio, valor)

    def listar_libros(self) -> list[Libro]:
        """Retorna todos los libros (empleados y clientes)."""
        return self._db.obtener_todos_los_libros()

    def obtener_libro(self, id_libro: int) -> Optional[Libro]:
        """Retorna un libro por ID o None si no existe."""
        return self._db.obtener_libro_por_id(id_libro)

