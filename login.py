"""
login.py:
=========
Modulo de autenticación para la Librería ACME.
Gestiona la sesion activa y expone helpers de autorizacion"""


from modelos import Usuario

class SesionNoIniciadaError(Exception):
    """Excepción personalizada para indicar que no hay una sesión iniciada."""

class SesionManager:
    """
    Gestiona el ciclo de vida de la sesión del empleado.

    Uso:
        gestor = SesionManager(db)
        usuario = gestor.iniciar_sesion("admin", "admin123")
        gestor.requiere_empleado()   # lanza SesionNoIniciadaError si no es empleado
        gestor.cerrar_sesion()
    """

    def __init__(self, db) -> None:
        self._db = db
        self._usuario_activo: Usuario | None
        self._intentos_fallidos: int = 0
    
    # --- Estado de sesion ---
    @property
    def usuario_activo(self) -> Usuario | None:
        """Devuelve el usuario actualmente autenticado, o None si no hay sesión iniciada."""
        return self._usuario_activo
    
    @property
    def hay_sesion(self) -> bool:
        """Indica si hay una sesión activa."""
        return self._usuario_activo is not None
    
    @property
    def es_empleado(self) -> bool:
        """Indica si el usuario activo es un empleado."""
        return (
        self._usuario_activo is not None
        and self._usuario_activo.es_empleado()
    )

    # --- Operaciones ---
    def iniciar_sesion(self, username: str, password: str) -> Usuario | None:
        """
        Intenta autenticar al usuario con las credenciales proporcionadas directamente con la base de datos.
        """
        try:
            # Llama a la base de datos para autenticar al usuario
            usuario = self._db.autenticar_usuario(username, password)
        except Exception as e:
            # Si hay un error lo relanza 
            raise e
        
        if usuario:
            self._usuario_activo = usuario
        
        return usuario
    
    def cerrar_sesion(self) -> None:
        """Cierra la sesión actual, si hay una abierta."""
        self._usuario_activo = None
    
    # --- Guardas de autorización ---
    def requiere_empleado(self) -> None:
        """"
        Verifica si hay un empleado en sesión. Si no, lanza error.
        """
        if not self.es_empleado:
            raise SesionNoIniciadaError(
                "Esta operación requiere haber iniciado sesión como empleado."
            )