import importlib

def cargar_logica(nombre):
    return importlib.import_module(nombre)

def ejecutar_con_respaldo(prompt, imagen_b64):
    try:
        primaria = cargar_logica("LogicaApi")
        return primaria.ejecutar(prompt, imagen_b64)
    except Exception:
        try:
            alterna = cargar_logica("LogicaAlterna")
            return alterna.ejecutar(prompt, imagen_b64)
        except Exception:
            return None
