"""modelos.py
=============
Clases del dominio de la Librería ACME.
En este archivo se definen las clases que representan las entidades del negocio: libro y usuario
No contiene logica de persistencia ni de presentacion."""

# --- Clase Libro ---
# Esta clase representa un libro y permite manejar los libros para la capa de persistencia (base de datos) y la capa de presentación (GUI).

class Libro:
    """Representa un libro en el catálogo de la Librería ACME."""

    def __init__(
        self,
        titulo: str,
        autor: str,
        genero: str,
        isbn: str,
        cantidad: int = 0,
        id: int | None = None,
    ) -> None:
        self._id = id
        self._titulo = titulo
        self._autor = autor
        self._genero = genero
        self._isbn = isbn
        self._cantidad = cantidad
    
    # -- Getters y Setters ---
    @property
    def id(self) -> int | None:
        return self._id

    @id.setter
    def id(self, valor: int) -> None:
        if self._id is not None:
            raise AttributeError("El ID no puede modificarse una vez asignado.")
        self._id = valor
        
    @property
    def titulo(self) -> str:
        return self._titulo
    
    @titulo.setter
    def titulo(self, valor: str) -> None:
        valor = valor.strip()
        if not valor:
            raise ValueError("El título no puede estar vacío.")
        self._titulo = valor
    
    @property
    def autor(self) -> str:
        return self._autor
    
    @autor.setter
    def autor(self, valor: str) -> None:
        valor = valor.strip()
        if not valor:
            raise ValueError("El autor no puede estar vacío.")
        self._autor = valor
    
    @property
    def genero(self) -> str:
        return self._genero
    
    @genero.setter
    def genero(self, valor: str) -> None:
        valor = valor.strip()

    @property
    def isbn(self) -> str:
        return self._isbn
    
    @isbn.setter
    def isbn(self, valor: str) -> None:
        valor = valor.strip()
        if not valor:
            raise ValueError("El ISBN no puede estar vacío.")
        self._isbn = valor
    
    @property
    def cantidad(self) -> int:
        return self._cantidad

    @cantidad.setter
    def cantidad(self, valor: int) -> None:
        if valor < 0:
            raise ValueError("La cantidad no puede ser negativa.")
        self._cantidad = valor

    # -- Metodos auxiliares para manejarlos en el GUI y con base de datos ---
    
    def to_dict(self) -> dict:
        """Serializa el libro a diccionario (útil para la capa de persistencia)."""
        return {
            "id": self._id,
            "titulo": self._titulo,
            "autor": self._autor,
            "genero": self._genero,
            "isbn": self._isbn,
            "cantidad": self._cantidad,
        }

    @classmethod
    def from_dict(cls, datos: dict) -> "Libro":
        """Crea una instancia de Libro desde un diccionario (e.g., fila de BD)."""
        return cls(
            id=datos.get("id"),
            titulo=datos["titulo"],
            autor=datos["autor"],
            genero=datos["genero"],
            isbn=datos["isbn"],
            cantidad=datos.get("cantidad", 0),
        )

    def __repr__(self) -> str:
        return (
            f"Libro(id={self._id!r}, titulo={self._titulo!r}, "
            f"autor={self._autor!r}, isbn={self._isbn!r}, cantidad={self._cantidad})"
        )

    def __str__(self) -> str:
        return (
            f"[{self._id}] {self._titulo} — {self._autor} "
            f"| Género: {self._genero} | ISBN: {self._isbn} | Stock: {self._cantidad}"
        )


# --- Clases para usuarios ---

# --- Clase rol (Clase de constantes) ---

class Rol:
    EMPLEADO = "empleado"
    CLIENTE  = "cliente"

# --- Clase Usuario ---

class Usuario:
    """Representa a un usuario del sistema (empleado o cliente)."""

    def __init__(
        self,
        username: str,
        password_hash: str,
        rol: str = Rol.EMPLEADO,
        id: int | None = None,
    ) -> None:
        self._id = id
        self._username = username
        self._password_hash = password_hash
        self._rol = rol

    # --- Getters ---

    @property
    def id(self) -> int | None:
        return self._id

    @property
    def username(self) -> str:
        return self._username

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    def rol(self) -> str:
        return self._rol
    
    # --- Metodos auxiliares ---

    def es_empleado(self) -> bool:
        return self._rol == Rol.EMPLEADO

    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "username": self._username,
            "password_hash": self._password_hash,
            "rol": self._rol,
        }

    def __repr__(self) -> str:
        return f"Usuario(id={self._id!r}, username={self._username!r}, rol={self._rol!r})"