import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables del .env si existe
load_dotenv()

# Fallback si no está definida DATABASE_URL
if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "sqlite:///correspondencia.db"
    print("⚠️ DATABASE_URL no encontrada. Usando fallback por defecto: sqlite:///correspondencia.db\n")

try:
    from app import app, db, Usuario
except ImportError as e:
    print(f"❌ Error al importar desde app.py: {e}")
    print("Por favor, asegúrate de estar ejecutando el script desde la raíz del proyecto y tener las dependencias instaladas.")
    sys.exit(1)

# =====================================================================
# ⚙️ VARIABLES CONFIGURABLES DEL NUEVO USUARIO
# =====================================================================
NUEVO_USUARIO = "******"
NUEVA_CONTRASENA = "******"
# =====================================================================

ROLES_PERMITIDOS = ["superadmin", "admin", "usuario"]

def main():
    print("==================================================")
    print("🔑 SCRIPT DE CREACIÓN DE USUARIOS PARA EL SISTEMA")
    print("==================================================")
    print(f"👤 Usuario a registrar: {NUEVO_USUARIO}")
    print(f"🔑 Contraseña a establecer: {NUEVA_CONTRASENA}")
    print("--------------------------------------------------")

    # Mostrar tipos de roles permitidos
    print("Tipos de roles permitidos:")
    for i, r in enumerate(ROLES_PERMITIDOS, 1):
        print(f"  {i}. {r}")
    print("--------------------------------------------------")

    # Solicitar rol como entrada de datos
    rol_elegido = ""
    while True:
        try:
            entrada = input("Introduce el rol que le deseas asignar (o el número correspondiente): ").strip().lower()
        except KeyboardInterrupt:
            print("\nOperación cancelada por el usuario.")
            sys.exit(0)

        if entrada in ROLES_PERMITIDOS:
            rol_elegido = entrada
            break
        elif entrada.isdigit() and 1 <= int(entrada) <= len(ROLES_PERMITIDOS):
            rol_elegido = ROLES_PERMITIDOS[int(entrada) - 1]
            break
        else:
            print(f"❌ Rol no válido. Por favor elige entre: {', '.join(ROLES_PERMITIDOS)}")

    # Si es 'usuario', pedir gerencia
    gerencia = None
    if rol_elegido == "usuario":
        try:
            gerencia = input("Introduce la gerencia para este usuario (ej. DG, GAL, GPSOI, etc.): ").strip().upper()
        except KeyboardInterrupt:
            print("\nOperación cancelada.")
            sys.exit(0)

        if not gerencia:
            gerencia = "GENERAL"
            print("⚠️ No se ingresó gerencia, usando 'GENERAL' por defecto.")

    # Crear usuario dentro del contexto de Flask
    with app.app_context():
        # Asegurarnos de que las tablas estén creadas en la base de datos
        db.create_all()

        # Verificar si el usuario ya existe
        existente = Usuario.query.filter_by(usuario=NUEVO_USUARIO).first()
        if existente:
            print(f"\n⚠️ El usuario '{NUEVO_USUARIO}' ya existe en la base de datos.")
            try:
                actualizar = input("¿Deseas actualizar su contraseña y rol con los nuevos datos? (s/n): ").strip().lower()
            except KeyboardInterrupt:
                print("\nOperación cancelada.")
                sys.exit(0)

            if actualizar == 's':
                existente.set_password(NUEVA_CONTRASENA, quien="script_creacion")
                existente.rol = rol_elegido
                existente.gerencia = gerencia
                existente.activo = True
                db.session.commit()
                print(f"✅ Contraseña y rol de '{NUEVO_USUARIO}' actualizados correctamente.")
            else:
                print("Operación cancelada. No se modificó nada.")
            return

        # Crear nueva instancia del modelo de forma dinámica para evitar errores si 'nombre_completo' falta o se añade después
        kwargs = {
            "usuario": NUEVO_USUARIO,
            "rol": rol_elegido,
            "gerencia": gerencia,
            "activo": True,
            "creado_por": "script_creacion"
        }

        # Inspección dinámica para evitar el error si 'nombre_completo' no está definido en las columnas de Usuario en app.py
        if hasattr(Usuario, 'nombre_completo'):
            kwargs["nombre_completo"] = "Usuario Sistema"

        nuevo_usuario = Usuario(**kwargs)
        nuevo_usuario.set_password(NUEVA_CONTRASENA, quien="script_creacion")

        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            print(f"\n🎉 ¡Usuario '{NUEVO_USUARIO}' creado con éxito con el rol '{rol_elegido}'!")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error al guardar el usuario en la base de datos: {e}")

if __name__ == "__main__":
    main()