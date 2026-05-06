"""
gui.py
======
Vista (MVC): interfaz de TERMINAL.

Esta clase implementa toda la interacción con el usuario en consola.
Para migrar a Tkinter, solo hay que crear una nueva clase que exponga
exactamente los mismos métodos públicos y reemplazar esta importación en main.py.

Contrato de la Vista
--------------------
La Vista nunca accede a la BD ni al controlador directamente.
Recibe un Controlador por inyección en __init__ y lo usa para
disparar acciones. Todo el estado de aplicación vive en el Controlador.

Cambios
=======
Aqui escribe todo lo del GUI, y para facilitar la integracion en el archivo main, escribelo como una clase
y luego solo reemplaza en el main.py la importacion de la clase por esta, asi el main.py no se tiene que modificar mas que eso
y todo lo demas no lo tendras que tocar.

La mayoria del codigo de este archivo lo puede borrar ya que use una interfaz de terminal para probarlo.

"""
 
import os
import getpass
import logging

from controlador import Controlador
from modelos import Libro
from login import SesionNoIniciadaError

logger = logging.getLogger(__name__)


# ── Helpers de consola ─────────────────────────────────────────────────────────

def _limpiar() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _separador(char: str = "─", ancho: int = 60) -> None:
    print(char * ancho)


def _titulo(texto: str) -> None:
    _separador("═")
    print(f"  {texto}")
    _separador("═")


def _pausa() -> None:
    input("\n  Presiona ENTER para continuar...")


def _pedir(prompt: str, obligatorio: bool = True) -> str:
    """Lee una cadena de la consola con validación básica."""
    while True:
        valor = input(f"  {prompt}: ").strip()
        if valor or not obligatorio:
            return valor
        print("  ⚠  Este campo es obligatorio.")


def _pedir_int(prompt: str, minimo: int = 0) -> int:
    """Lee un entero con validación de rango."""
    while True:
        try:
            valor = int(_pedir(prompt))
            if valor < minimo:
                print(f"  ⚠  El valor mínimo es {minimo}.")
                continue
            return valor
        except ValueError:
            print("  ⚠  Ingresa un número entero válido.")


def _mostrar_libros(libros: list[Libro]) -> None:
    if not libros:
        print("\n  (Sin resultados)\n")
        return
    _separador()
    print(f"  {'ID':<5} {'Título':<30} {'Autor':<20} {'Género':<12} {'ISBN':<15} {'Stock'}")
    _separador()
    for libro in libros:
        print(
            f"  {str(libro.id):<5} "
            f"{libro.titulo[:29]:<30} "
            f"{libro.autor[:19]:<20} "
            f"{libro.genero[:11]:<12} "
            f"{libro.isbn[:14]:<15} "
            f"{libro.cantidad}"
        )
    _separador()


# ── Vista principal ────────────────────────────────────────────────────────────

class GUITerminal:
    """
    Interfaz de usuario en terminal para la Librería ACME.

    Para reemplazar por Tkinter:
        1. Crea GUITkinter con los mismos métodos públicos.
        2. En main.py cambia: from gui import GUITerminal → from gui_tkinter import GUITkinter
    """

    def __init__(self, controlador: Controlador) -> None:
        self._ctrl = controlador

    # ── Punto de entrada ───────────────────────────────────────────────────────

    def iniciar(self) -> None:
        """Arranca el bucle principal de la aplicación."""
        _limpiar()
        _titulo("Librería ACME — Sistema de Control de Stock")
        self._menu_inicio()

    # ── Menú de inicio (selección de modo) ────────────────────────────────────

    def _menu_inicio(self) -> None:
        while True:
            print("\n  ¿Cómo deseas acceder?\n")
            print("  1 · Empleado (requiere contraseña)")
            print("  2 · Cliente  (solo búsqueda)")
            print("  0 · Salir")
            _separador("-", 40)
            opcion = _pedir("Opción")

            if opcion == "1":
                if self._flujo_login():
                    self._menu_empleado()
            elif opcion == "2":
                self._menu_cliente()
            elif opcion == "0":
                print("\n  Hasta luego.\n")
                break
            else:
                print("  ⚠  Opción no válida.")

    # ── Login ──────────────────────────────────────────────────────────────────

    def _flujo_login(self) -> bool:
        """Muestra el formulario de login. Retorna True si el login fue exitoso."""
        _limpiar()
        _titulo("Inicio de sesión — Empleados")
        try:
            username = _pedir("Usuario")
            password = getpass.getpass("  Contraseña: ")
            exito = self._ctrl.iniciar_sesion(username, password)
            if exito:
                print(f"\n  ✓ Bienvenido, {self._ctrl.usuario_activo.username}.")
                _pausa()
                return True
            else:
                print("\n  ✗ Usuario o contraseña incorrectos.")
                _pausa()
                return False
        except PermissionError as e:
            print(f"\n  🔒 {e}")
            _pausa()
            return False
        except Exception as e:
            logger.exception("Error inesperado en login: %s", e)
            print(f"\n  ✗ Error inesperado: {e}")
            _pausa()
            return False

    # ── Menú empleado ──────────────────────────────────────────────────────────

    def _menu_empleado(self) -> None:
        while True:
            _limpiar()
            usuario = self._ctrl.usuario_activo
            _titulo(f"Menú Empleado — {usuario.username}")
            print("  1 · Agregar libro")
            print("  2 · Editar libro")
            print("  3 · Borrar libro")
            print("  4 · Buscar libros")
            print("  5 · Ver todos los libros")
            print("  0 · Cerrar sesión / Salir")
            _separador("-", 40)
            opcion = _pedir("Opción")

            try:
                if opcion == "1":
                    self._vista_agregar()
                elif opcion == "2":
                    self._vista_editar()
                elif opcion == "3":
                    self._vista_borrar()
                elif opcion == "4":
                    self._vista_buscar()
                elif opcion == "5":
                    self._vista_listar()
                elif opcion == "0":
                    self._ctrl.cerrar_sesion()
                    print("\n  Sesión cerrada.")
                    _pausa()
                    break
                else:
                    print("  ⚠  Opción no válida.")
                    _pausa()
            except SesionNoIniciadaError as e:
                print(f"\n  🔒 {e}")
                _pausa()
                break
            except Exception as e:
                logger.exception("Error en menú empleado: %s", e)
                print(f"\n  ✗ Error: {e}")
                _pausa()

    # ── Menú cliente ───────────────────────────────────────────────────────────

    def _menu_cliente(self) -> None:
        while True:
            _limpiar()
            _titulo("Menú Cliente — Búsqueda de libros")
            print("  4 · Buscar libros")
            print("  5 · Ver catálogo completo")
            print("  0 · Volver")
            _separador("-", 40)
            opcion = _pedir("Opción")

            try:
                if opcion == "4":
                    self._vista_buscar()
                elif opcion == "5":
                    self._vista_listar()
                elif opcion == "0":
                    break
                else:
                    print("  ⚠  Opción no válida.")
                    _pausa()
            except Exception as e:
                logger.exception("Error en menú cliente: %s", e)
                print(f"\n  ✗ Error inesperado: {e}")
                _pausa()

    # ── Vistas de operaciones ──────────────────────────────────────────────────

    def _vista_agregar(self) -> None:
        _limpiar()
        _titulo("Agregar libro")
        try:
            titulo   = _pedir("Título")
            autor    = _pedir("Autor")
            genero   = _pedir("Género")
            isbn     = _pedir("ISBN")
            cantidad = _pedir_int("Cantidad en stock", minimo=0)

            libro = self._ctrl.agregar_libro(titulo, autor, genero, isbn, cantidad)
            print(f"\n  ✓ Libro agregado con ID={libro.id}.")
        except ValueError as e:
            print(f"\n  ⚠  {e}")
        _pausa()

    def _vista_editar(self) -> None:
        _limpiar()
        _titulo("Editar libro")
        self._vista_listar(pausa=False)
        try:
            id_libro = _pedir_int("ID del libro a editar", minimo=1)
            libro = self._ctrl.obtener_libro(id_libro)
            if libro is None:
                print(f"\n  ⚠  No existe libro con ID={id_libro}.")
                _pausa()
                return

            print(f"\n  Editando: {libro}")
            print("  (Deja en blanco para conservar el valor actual)\n")

            titulo   = input(f"  Título    [{libro.titulo}]: ").strip() or libro.titulo
            autor    = input(f"  Autor     [{libro.autor}]: ").strip()  or libro.autor
            genero   = input(f"  Género    [{libro.genero}]: ").strip() or libro.genero
            isbn     = input(f"  ISBN      [{libro.isbn}]: ").strip()   or libro.isbn
            cant_str = input(f"  Cantidad  [{libro.cantidad}]: ").strip()
            cantidad = int(cant_str) if cant_str else libro.cantidad

            self._ctrl.editar_libro(id_libro, titulo, autor, genero, isbn, cantidad)
            print("\n  ✓ Libro actualizado.")
        except ValueError as e:
            print(f"\n  ⚠  {e}")
        _pausa()

    def _vista_borrar(self) -> None:
        _limpiar()
        _titulo("Borrar libro")
        self._vista_listar(pausa=False)
        try:
            id_libro = _pedir_int("ID del libro a eliminar", minimo=1)
            confirmacion = _pedir(f"¿Confirmas eliminar ID={id_libro}? (s/n)")
            if confirmacion.lower() == "s":
                self._ctrl.borrar_libro(id_libro)
                print("\n  ✓ Libro eliminado.")
            else:
                print("\n  Operación cancelada.")
        except ValueError as e:
            print(f"\n  ⚠  {e}")
        _pausa()

    def _vista_buscar(self) -> None:
        _limpiar()
        _titulo("Buscar libros")
        print("  Criterios disponibles: titulo, autor, genero, isbn\n")
        try:
            criterio = _pedir("Criterio de búsqueda")
            valor    = _pedir("Valor a buscar")
            resultados = self._ctrl.buscar_libros(criterio, valor)
            print(f"\n  Se encontraron {len(resultados)} resultado(s):\n")
            _mostrar_libros(resultados)
        except ValueError as e:
            print(f"\n  ⚠  {e}")
        _pausa()

    def _vista_listar(self, pausa: bool = True) -> None:
        _limpiar()
        _titulo("Catálogo completo")
        try:
            libros = self._ctrl.listar_libros()
            print(f"\n  Total de libros: {len(libros)}\n")
            _mostrar_libros(libros)
        except Exception as e:
            print(f"\n  ✗ Error al obtener catálogo: {e}")
        if pausa:
            _pausa()
