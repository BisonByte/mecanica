"""Script mínimo para crear o actualizar un usuario administrador localmente.

Uso:
  python create_admin.py
  python create_admin.py --email admin@example.com --password "Secr3t!" --nombre "Admin" --rol "super"

El script inicializa la base de datos SQLite en `webapp/data/users.db`, genera un hash
PBKDF2-HMAC-SHA256 para la contraseña y marca la cuenta como aprobada.
"""
from __future__ import annotations

import argparse
import getpass
from pathlib import Path
from typing import Optional

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

from services import users


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crear o actualizar un administrador")
    parser.add_argument("--email", help="Correo electrónico del administrador")
    parser.add_argument("--password", help="Contraseña a asignar")
    parser.add_argument("--nombre", help="Nombre completo", default="Administrador")
    parser.add_argument("--rol", help="Rol descriptivo", default="admin")
    return parser.parse_args()


def prompt_password() -> str:
    password = getpass.getpass("Contraseña: ")
    confirm = getpass.getpass("Confirmar contraseña: ")
    if password != confirm:
        raise ValueError("Las contraseñas no coinciden.")
    return password


def main() -> None:
    args = parse_args()
    email = (args.email or input("Correo electrónico del admin: ")).strip().lower()
    if not email:
        print("Correo vacío. Abortando.")
        return

    password: Optional[str] = args.password
    if not password:
        try:
            password = prompt_password()
        except ValueError as exc:
            print(exc)
            return

    users.ensure_db()
    record = users.create_or_update_user(
        email=email,
        password=password,
        full_name=args.nombre,
        role=args.rol,
        status="approved",
        is_admin=True,
    )
    print("Usuario administrador listo:")
    print(f"  Email: {record['email']}")
    print(f"  Nombre: {record.get('full_name') or args.nombre}")
    print("  Rol: admin")
    print("Base de datos:", users.DB_PATH)


if __name__ == "__main__":
    main()
