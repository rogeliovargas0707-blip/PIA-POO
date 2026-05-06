"""
conexion.py
=============
Capa de acceso a base de datos
Encapsula toda la comunicacion con SQLite 3
Asi el resto del sistema nunca importa sqlite3 directamente
"""

import sqlite3
import hashlib
import logging
from pathlib import Path

from modelos import Libro, Usuario, Rol

# --- Logger module ---
logger = logging.getLogger(__name__)

# --- Ruta donde se encontrara la base de datos ---
DB_Default_Path = Path(__file__).parent / "libreria_acme.db"

class ConexionDB:
    """
    Gestiona la conexion a SQLite 3 y expone metodos CRUD para libros y usuarios.
    """

    def __init__(self, ruta_db: Path = DB_Default_Path) -> None:
        self._ruta_db = ruta_db
        self._conn: sqlite3.Connection | None = None
    
    # --- Gestion de la conexion ---
    def conectar(self) -> None:
        """Abre la conexion e incializa el esquema si es primera ejecucion."""    
        try:
            self._conn = sqlite3.connect(self._ruta_db)
            self._conn.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._inicializar_esquema()  # Crea tablas si no existen
            
            logger.info(f"Conexion a base de datos establecida en {self._ruta_db}")
        
        except sqlite3.Error as e:
            logger.error(f"Error al conectar a la base de datos: {e}")
            raise e

    def cerrar(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("Conexión cerrada.")

    def __enter__(self) -> "ConexionDB":
        self.conectar()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type:
            self._conn.rollback()
            logger.warning("Rollback por excepción: %s", exc_val)
        self.cerrar()
        return False 
    

    # --- Esquema y datos iniciales ---

    def _inicializar_esquema(self) -> None:
        """Crea tablas si no existen e inserta usuario admin por defecto."""
        ddl = """
        CREATE TABLE IF NOT EXISTS libros (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo   TEXT    NOT NULL,
            autor    TEXT    NOT NULL,
            genero   TEXT    NOT NULL DEFAULT '',
            isbn     TEXT    NOT NULL UNIQUE,
            cantidad INTEGER NOT NULL DEFAULT 0 CHECK(cantidad >= 0)
        );

        CREATE TABLE IF NOT EXISTS usuarios (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            rol           TEXT    NOT NULL DEFAULT 'empleado'
        );
        """
        try:
            self._conn.executescript(ddl)
            self._conn.commit()
            self._seed_admin()
        except sqlite3.Error as e:
            logger.exception("Error al inicializar esquema: %s", e)
            raise

    def _seed_admin(self) -> None:
        """Inserta usuario admin si la tabla de usuarios está vacía."""
        # Aqui se nombra al admin y su contraseña por defecto
        cur = self._conn.execute("SELECT COUNT(*) FROM usuarios")
        if cur.fetchone()[0] == 0:
            hash_pw = self._hashear("admin123")
            self._conn.execute(
                "INSERT INTO usuarios (username, password_hash, rol) VALUES (?, ?, ?)",
                ("admin", hash_pw, Rol.EMPLEADO),
            )
            self._conn.commit()
            logger.info("Usuario 'admin' creado con contraseña por defecto.")
    
    # --- Utilidades ---
    @staticmethod
    def _hashear(password: str) -> str:
        """Hashea la contrasena porque es una mejor practica que dejarla en texto plano, pero probablemente lo quite para simplificar el PIA"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _fila_a_libro(self, fila: sqlite3.Row) -> Libro:
        """Convierte una fila de la tabla libros a una instancia de Libro."""
        return Libro.from_dict(dict(fila))
    
    def _fila_a_usuario(self, fila: sqlite3.Row) -> Usuario:
        """Convierte una fila de la tabla usuarios a una instancia de Usuario."""
        return Usuario(
            id=fila["id"],
            username=fila["username"],
            password_hash=fila["password_hash"],
            rol=fila["rol"],
        )
    
    # --- Metodos CRUD ---
    def agregar_libro(self, libro: Libro) -> int:
        """Inserta un libro a la base de datos. Retorna el id (int)"""
        sql = """
        INSERT INTO libros (titulo, autor, genero, isbn, cantidad)
        Values (:titulo, :autor, :genero, :isbn, :cantidad)
        """
        try:
            cur = self._conn.execute(sql, libro.to_dict())
            self._conn.commit()
            libro_id = cur.lastrowid

            logger.info(f"Libro {libro.titulo} agregado con ID {libro_id}")

            return cur.lastrowid
        
        except sqlite3.IntegrityError as e:
            logger.warning("ISBN duplicado: %s", e)
            raise ValueError("Ya existe un libro con ISBN '{libro.isbn}'") from e
        
        except sqlite3.Error as e:
            logger.error("Error al agregar libro: %s", e)
            raise e
    
    def editar_libro(self, libro: Libro) -> None:
        """Actualiza todos los campos de un libro existente."""
        if libro.id is None:
            raise ValueError("El libro no tiene ID; no se puede editar.")
        sql = """
            UPDATE libros
               SET titulo=:titulo, autor=:autor, genero=:genero,
                   isbn=:isbn, cantidad=:cantidad
             WHERE id=:id
        """
        try:
            cur = self._conn.execute(sql, libro.to_dict())
            self._conn.commit()
            if cur.rowcount == 0:
                raise ValueError(f"No existe libro con ID={libro.id}.")
            logger.info("Libro ID=%d actualizado.", libro.id)
        except sqlite3.IntegrityError as e:
            raise ValueError(f"ISBN duplicado: {e}") from e
        except sqlite3.Error as e:
            logger.exception("Error al editar libro: %s", e)
            raise
    
    def borrar_libro(self, id_libro: int) -> None:
        """Elimina un libro por ID."""
        try:
            cur = self._conn.execute("DELETE FROM libros WHERE id=?", (id_libro,))
            self._conn.commit()
            if cur.rowcount == 0:
                raise ValueError(f"No existe libro con ID={id_libro}.")
            logger.info("Libro ID=%d eliminado.", id_libro)
        except sqlite3.Error as e:
            logger.exception("Error al borrar libro: %s", e)
            raise
    
    def buscar_libros(self, criterio: str, valor: str) -> list[Libro]:
        """
        Busca libros por criterio (titulo, autor, genero, isbn).
        La búsqueda es parcial e insensible a mayúsculas (LIKE).
        """
        columnas_validas = {"titulo", "autor", "genero", "isbn"}
        if criterio not in columnas_validas:
            raise ValueError(f"Criterio '{criterio}' no válido. Use: {columnas_validas}")
        sql = f"SELECT * FROM libros WHERE {criterio} LIKE ? COLLATE NOCASE"
        try:
            cur = self._conn.execute(sql, (f"%{valor}%",))
            filas = cur.fetchall()
            logger.debug("Búsqueda '%s'='%s': %d resultado(s).", criterio, valor, len(filas))
            return [self._fila_a_libro(f) for f in filas]
        except sqlite3.Error as e:
            logger.exception("Error en búsqueda: %s", e)
            raise

    def obtener_todos_los_libros(self) -> list[Libro]:
        """Retorna todos los libros ordenados por título."""
        try:
            cur = self._conn.execute("SELECT * FROM libros ORDER BY titulo COLLATE NOCASE")
            return [self._fila_a_libro(f) for f in cur.fetchall()]
        except sqlite3.Error as e:
            logger.exception("Error al obtener libros: %s", e)
            raise

    def obtener_libro_por_id(self, id_libro: int) -> Optional[Libro]:
        try:
            cur = self._conn.execute("SELECT * FROM libros WHERE id=?", (id_libro,))
            fila = cur.fetchone()
            return self._fila_a_libro(fila) if fila else None
        except sqlite3.Error as e:
            logger.exception("Error al obtener libro por ID: %s", e)
            raise
    
    # --- Autenticar usuarios ---

    def autenticar_usuario(self, username: str, password: str) -> Optional[Usuario]:
        """
        Verifica credenciales. Retorna Usuario si son correctas, None en caso contrario.
        """
        hash_pw = self._hashear(password)
        try:
            cur = self._conn.execute(
                "SELECT * FROM usuarios WHERE username=? AND password_hash=?",
                (username, hash_pw),
            )
            fila = cur.fetchone()
            if fila:
                logger.info("Autenticación exitosa: '%s'", username)
                return self._fila_a_usuario(fila)
            logger.warning("Autenticación fallida para '%s'.", username)
            return None
        except sqlite3.Error as e:
            logger.exception("Error al autenticar: %s", e)
            raise