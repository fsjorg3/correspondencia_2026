import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

# 1. Cargar el string de conexión desde .env
load_dotenv()

# 2. Importar la configuración y modelos desde la app principal
# Esto asegura que usemos exactamente la misma BD (PostgreSQL o SQLite)
from app import app, db, Oficio

def limpiar_fecha(valor):
    """Limpia y estandariza el formato de fecha para la BD"""
    if pd.isna(valor) or str(valor).strip() in ["", "nan", "None"]:
        return None
    if isinstance(valor, datetime):
        return valor.strftime("%Y-%m-%d")
    val_str = str(valor).strip()
    if " " in val_str:
        val_str = val_str.split(" ")[0]
    return val_str

def importar_registros(ruta_excel):
    if not os.path.exists(ruta_excel):
        print(f"[X] Error: No se encontró el archivo '{ruta_excel}'")
        return

    print(f"Leyendo archivo Excel: {ruta_excel}")
    try:
        # Leer el Excel todo como texto para evitar problemas de tipos mixtos
        df = pd.read_excel(ruta_excel, dtype=str)
        df.columns = df.columns.str.strip() # Limpiar espacios en los nombres de columnas
    except Exception as e:
        print(f"[X] Error al leer el archivo Excel: {e}")
        return

    # Convertir los "nan" de pandas a nulos nativos de Python (None)
    df = df.replace({np.nan: None})
    datos = df.to_dict(orient="records")

    print(f"Se encontraron {len(datos)} registros en el Excel. Iniciando importación...")

    # Activar el contexto de la aplicación de Flask para poder usar la BD
    with app.app_context():
        # ¡¡DIFERENCIA CLAVE CON APP.PY!!
        # NO hacemos db.session.query(Oficio).delete() 
        # Simplemente añadiremos los nuevos.

        filas_importadas = 0

        for i, fila in enumerate(datos, start=1):
            folio = fila.get("FOLIO") or fila.get("No.")
            if not folio or str(folio).strip() in ["", "nan", "None"]:
                print(f" [!] Fila {i}: Ignorada (Falta el FOLIO).")
                continue

            # Parseo seguro de números
            termino_val = fila.get("TÉRMINO")
            dias_val = fila.get("DÍAS DE ATENCIÓN")

            try:
                termino_val = int(float(termino_val)) if termino_val not in ["", "None", "nan", None] else None
            except:
                termino_val = None

            try:
                dias_val = int(float(dias_val)) if dias_val not in ["", "None", "nan", None] else None
            except:
                dias_val = None

            # Semáforo -> Estatus
            semaforo = fila.get("SEMAFORO")
            if semaforo and str(semaforo).strip().lower() == "finalizado":
                estatus_val = "Solucionado"
            else:
                estatus_val = fila.get("ESTATUS")

            # Crear el objeto Oficio
            nuevo = Oficio(
                numero=folio,
                numero_oficio=fila.get("NUMERO DE OFICIO"),
                fecha=limpiar_fecha(fila.get("FECHA INGRESO")),
                hora=fila.get("HORA"),
                numero_expediente=fila.get("No. EXP."),
                quien_emite=fila.get("QUIEN LO EMITE"),
                con_copia_para=fila.get("CON COPIA PARA"),
                anexos=fila.get("ANEXOS"),
                gerencia_turnada=fila.get("GERENCIA"),
                asunto=fila.get("ASUNTO"),
                prioridad=fila.get("PRIORIDAD"),
                termino=termino_val,
                fecha_limite=limpiar_fecha(fila.get("FECHA LÍMITE DE ATENCIÓN")),
                responsable1=fila.get("RESPONSABLE 1"),
                responsable2=fila.get("RESPONSABLE"),
                nis=fila.get("NIS"),
                estatus=estatus_val,
                observaciones=fila.get("OBSERVACIONES"),
                fecha_atencion=limpiar_fecha(fila.get("FECHA ATENCIÓN")),
                oficio_respuesta=fila.get("OFICIO DE RESPUESTA"),
                fecha_acuse=limpiar_fecha(fila.get("FECHA ACUSE DE RESPUESTA")),
                dias_atencion=dias_val
            )

            db.session.add(nuevo)
            filas_importadas += 1

            if filas_importadas % 100 == 0:
                print(f" ... {filas_importadas} registros preparados")

        # Intentar guardar todo en la base de datos de una vez
        try:
            db.session.commit()
            print("\n==========================================")
            print("[OK] IMPORTACIÓN FINALIZADA CON ÉXITO")
            print(f"Registros agregados: {filas_importadas}")
            print("Los registros que ya existían previamente NO fueron borrados.")
            print("==========================================")
        except Exception as e:
            db.session.rollback()
            print("\n==========================================")
            print("[X] ERROR CRÍTICO AL GUARDAR EN BASE DE DATOS")
            print("Detalles del error:")
            print(str(e))
            print("\nSe ha cancelado la importación para proteger tu información.")
            print("==========================================")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso correcto: python importar_excel.py \"ruta/al/archivo.xlsx\"")
        sys.exit(1)
        
    ruta_archivo = sys.argv[1]
    importar_registros(ruta_archivo)
