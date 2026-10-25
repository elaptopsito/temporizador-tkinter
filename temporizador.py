import tkinter as tk
from tkinter import simpledialog, messagebox
from pathlib import Path
import json
import sys

if getattr(sys, "frozen", False):
    CARPETA_BASE = Path(sys.executable).resolve().parent
else:
    CARPETA_BASE = Path(__file__).resolve().parent

ARCHIVO_TEMPORIZADORES = CARPETA_BASE / "temporizadores.json"
ARCHIVO_HISTORIAL = CARPETA_BASE / "historial.json"

temporizadores = []
historial = {}
ventana_historial = None
cuerpo_historial = None

def cargar_temporizadores():
    """Cargar los temporizadores de la ejecucion anterior"""
    if not ARCHIVO_TEMPORIZADORES.exists():
        return []
    try:
        with open(ARCHIVO_TEMPORIZADORES, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (json.JSONDecodeError, OSError):
        messagebox.showwarning(
            "Aviso",
            "No se pudo encontrar el archivo con los temporizadores, se inicia con la lista vacia",
            parent=ventana
        )
        return []
    
    if not isinstance(datos, list):
        return []
    return datos

def guardar_temporizadores():
    """Guardar los temporizadores en un json"""
    datos = [{"nombre": t.nombre, "minutos": t.minutos} for t in temporizadores]
    with open(ARCHIVO_TEMPORIZADORES, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)


#Persistencia del historial
def cargar_historial():
    """Cargar el historial con los minutos pasados en cada
    actividad"""
    if not ARCHIVO_HISTORIAL.exists():
        return {}
    try:
        with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (json.JSONDecodeError, OSError):
        messagebox.showwarning(
            "Aviso",
            "No se encontró el historial, se empieza con el historial vacío",
            parent=ventana
        )
        return {}

    if not isinstance(datos, dict):
        return
    return {k: v for k,v in datos.items() if isinstance(k, str) and isinstance(v, int)}

def guardar_historial():
    """Guardar el historial en formato json"""
    with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=2, ensure_ascii=False)

def formatear_tiempo(total_segundos):
    """Obtener el tiempo en formato HH:MM:SS"""
    hora, resto = divmod(total_segundos, 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{hora:02d}:{minutos:02d}:{segundos:02d}"

def registrar_actividad(nombre):
    if nombre not in historial:
        historial[nombre] = 0
        guardar_historial()
        actualizar_ventana_historial()

def sumar_al_historial(nombre, segundos):
    historial[nombre] = historial.get(nombre, 0) + segundos
    guardar_historial()
    actualizar_ventana_historial()

#Ventana del historial
def abrir_historial():
    global ventana_historial, cuerpo_historial

    if ventana_historial is not None and ventana_historial.winfo_exists():
        ventana_historial.lift()
        return

    ventana_historial = tk.Toplevel(ventana)
    ventana_historial.title("Historial de actividades")
    ventana_historial.geometry("400x500")
    ventana_historial.protocol("WM_DELETE_WINDOW", cerrar_historial)

    cuerpo_historial = tk.Frame(ventana_historial, pady=10, padx=10)
    cuerpo_historial.pack(fill="both", expand=True)

    actualizar_ventana_historial()

def cerrar_historial():
    global ventana_historial, cuerpo_historial
    if ventana_historial is not None:
        ventana_historial.destroy()
    ventana_historial = None
    cuerpo_historial = None

def actualizar_ventana_historial():
    if ventana_historial is None or cuerpo_historial is None:
        return

    for widget in cuerpo_historial.winfo_children():
        widget.destroy()

    if not historial:
        tk.Label(cuerpo_historial, text="Todavía no hay actividades",
                 font=("Arial", 12)).pack()
        return

    for nombre, segundos in historial.items():
        fila = tk.Frame(cuerpo_historial, bd=1, relief="groove", padx=5, pady=5)
        fila.pack(fill="x", pady=2)
        tk.Label(fila, text=nombre, font=("Arial", 14), bd=1).pack(side="left")
        tk.Label(fila, text=formatear_tiempo(segundos), font=("Arial", 14)).pack(side="right")
 
class Temporizador:
    """Hacer el temporizador, su cuerpo y metodos"""
    def __init__(self, contenedor, nombre, minutos):
        self.nombre = nombre
        self.segundos = 0
        self.minutos = minutos
        self.limite = minutos * 60
        self.activo = False
        self.id_after = None

        self.fila = tk.Frame(contenedor, bd=1, relief="groove", padx=5, pady=5)
        self.fila.pack(fill="x", pady="3")

        self.etiqueta_nombre = tk.Label(self.fila, text=nombre, font=("Arial", 14, "bold"))
        self.etiqueta_nombre.pack(side="left")

        self.etiqueta_tiempo = tk.Label(self.fila, text="00:00:00", font=("Arial", 14))
        self.etiqueta_tiempo.pack(side="left", padx=10)

        self.botones = tk.Frame(self.fila)
        self.botones.pack(side="right")

        self.boton_iniciar = tk.Button(
            self.botones,
            text="Iniciar temporizador",
            command=self.iniciar
        )
        self.boton_iniciar.pack(side="right")

        self.boton_eliminar = tk.Button(
            self.botones,
            text="Eliminar",
            command=self.eliminar_temporizador
        )
        self.boton_eliminar.pack(side="left", padx=2)

        for widget in (self.fila, self.etiqueta_nombre, self.etiqueta_tiempo):
            widget.bind("<Button-3>", self.mostrar_menu)

    def mostrar_menu(self, event):
        """Mostrar el menu al hacer click derecho"""
        menu_temporizador_actual.set(id(self))
        menu_contextual_temporizador.tk_popup(event.x_root, event.y_root)
        menu_contextual_temporizador.grab_release()

    
    def iniciar(self):
        """Iniciar el temporizador"""
        if self.activo:
            return
        self.activo = True
        self.boton_iniciar.config(text="Iniciado", state="disabled")
        self.boton_eliminar.config(state="disabled")
        self.id_after = self.fila.after(1000, self.tick)

    def tick(self):
        """Configurar el tick para que se ejecute el temporizador"""
        self.segundos += 1
        self.etiqueta_tiempo.config(text=formatear_tiempo(self.segundos))
        if self.segundos >= self.limite:
            self.terminar()
        else:
            self.id_after = self.fila.after(1000, self.tick)

    def terminar(self):
        """Configurar para cuando el temporizador llegue a su fin"""
        self.activo = False
        self.id_after = None
        self.segundos = 0
        self.etiqueta_tiempo.config(text=formatear_tiempo(0))
        self.boton_iniciar.config(text="Iniciar temporizador", state="normal")
        self.boton_eliminar.config(state="normal")

        sumar_al_historial(self.nombre, self.limite)

        messagebox.showinfo(
            "Temporizador terminado",
            f"{self.nombre} ha llegado a {self.limite // 60} minutos.",
            parent=ventana
        )

    def eliminar_temporizador(self):
        """Eliminar un temporizador de la lista"""
        if not messagebox.askyesno("Eliminar", f"Eliminar '{self.nombre}'?", parent=ventana):
            return

        if self.id_after is not None:
            self.fila.after_cancel(self.id_after)
            self.id_after = None
        self.activo = False
        self.fila.destroy()
        temporizadores.remove(self)
        guardar_temporizadores()

def agregar_temporizador():
    """Agregar un temporizador con su nombre a la lista de temporizadores."""
    nombre = simpledialog.askstring("Nuevo temporizador", "Nombre de la actividad:", parent=ventana)
    if nombre is None:
        return
    nombre = nombre.strip()
    if nombre == "":
        messagebox.showwarning("Campo vacío", "Tenes que ingresar el nombre de la actividad", parent=ventana)
        return

    minutos = simpledialog.askinteger(
        "Duración", "Minutos:",
        parent=ventana, minvalue=1, maxvalue=2000
    )
    if minutos is None:
        return
    
    nuevo = Temporizador(cuerpo_temporizador, nombre, minutos)
    nuevo.etiqueta_tiempo.config(text=formatear_tiempo(nuevo.limite))
    temporizadores.append(nuevo)

    registrar_actividad(nombre)
    guardar_temporizadores()

def buscar_temporizador():
    """Obtener el id del temporizador que se le ha echo
    click derecho"""
    for t in temporizadores:
        if id(t) == menu_temporizador_actual.get():
            return t
    return None

def editar_nombre():
    """Editar el nombre de un temporizador"""
    t = buscar_temporizador()
    if t is None:
        return

    if t.activo:
        messagebox.showinfo(
            "Temporizador en curso",
            "Espera a que finalice el temporizador antes de cambiar su nombre.",
            parent=ventana
        )
        return
    
    nuevo = simpledialog.askstring(
        "Editar nombre",
        "Nuevo nombre:",
        initialvalue=t.nombre,
        parent=ventana
    )
    if nuevo is None:
        return
    nuevo = nuevo.strip()
    if nuevo == "":
        messagebox.showwarning(
            "Campo vacío",
            "Tenes que ingresar el nuevo nombre",
            parent=ventana
        )
        return
    
    t.nuevo = nuevo
    t.etiqueta_nombre.config(text=nuevo)
    guardar_temporizadores()

def editar_duracion():
    """Editar la duracion de un temporizador"""
    t = buscar_temporizador()
    if t is None:
        return

    if t.activo:
        messagebox.showinfo(
            "Temporizador en curso",
            "Espera a que el temporizador termine antes de editar su duración.",
            parent=ventana
        )
        return
    nuevo = simpledialog.askinteger(
        "Editar duración",
        "Nueva duración:",
        initialvalue=t.minutos,
        parent=ventana,
        minvalue=1,
        maxvalue=1440
    )
    if nuevo is None:
        return
    t.nuevo = nuevo
    t.minutos = nuevo
    t.limite = nuevo * 60
    guardar_temporizadores()

ventana = tk.Tk()
ventana.title("Temporizador")
ventana.geometry("400x500")

#La cabecera donde va a estar el boton de agregar
cabecera = tk.Frame(ventana, bg="blue", padx=10, pady="5", bd=1)
cabecera.pack(fill="x")
boton_agregar = tk.Button(cabecera, text="Agregar", command=agregar_temporizador)
boton_agregar.pack(side="right")
boton_historial = tk.Button(
    cabecera, 
    text="Historial",
    command=abrir_historial
)
boton_historial.pack(side="left")

#El cuerpo del temporizador 
cuerpo_temporizador = tk.Frame(ventana, bg="green", padx=10, pady=5, bd=1)
cuerpo_temporizador.pack(fill="both", expand=True)

menu_temporizador_actual = tk.IntVar(value=1)
menu_contextual_temporizador = tk.Menu(ventana, tearoff=0)
menu_contextual_temporizador.add_command(label="Editar duración", command=editar_duracion)
menu_contextual_temporizador.add_command(label="Editar nombre", command=editar_nombre)

#Cargar el historial
historial = cargar_historial()

#Cargo los datos antes del mainloop()
for datos in cargar_temporizadores():
    nuevo = Temporizador(cuerpo_temporizador, datos["nombre"], datos["minutos"])
    nuevo.etiqueta_tiempo.config(text=formatear_tiempo(nuevo.limite))
    temporizadores.append(nuevo)
    historial.setdefault(datos["nombre"], 0)

messagebox.showinfo(
    "Aviso",
    "En este programa los temporizadores no se pueden pausar.\n\n"
    "Si vas a iniciar un temporizador, acabalo completo.",
    parent=ventana
)

ventana.mainloop()