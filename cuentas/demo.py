"""Datos demo · S1 · los 6 usuarios de la sección 6 (contraseña Demo2026!)."""

from .models import Usuario

CONTRASENA_DEMO = "Demo2026!"

USUARIOS_DEMO = [
    ("admin", Usuario.ADMIN, "Juan Pedro", "Administrador"),
    ("administrativo", Usuario.ADMINISTRATIVO, "Ana", "Rojas"),
    ("administrativo2", Usuario.ADMINISTRATIVO, "Bruno", "Díaz"),
    ("mecanico", Usuario.MECANICO, "Carlos", "Muñoz"),
    ("cliente1", Usuario.CLIENTE, "María", "González"),
    ("cliente2", Usuario.CLIENTE, "Pedro", "Soto"),
]


def cargar(salida):
    for username, perfil, nombres, apellidos in USUARIOS_DEMO:
        usuario, creado = Usuario.objects.get_or_create(
            username=username,
            defaults={"perfil": perfil, "first_name": nombres, "last_name": apellidos,
                      "email": f"{username}@serviexpress.demo", "is_staff": perfil == Usuario.ADMIN,
                      "is_superuser": perfil == Usuario.ADMIN},
        )
        if creado:
            usuario.set_password(CONTRASENA_DEMO)
        usuario.intentos_fallidos, usuario.bloqueado_hasta, usuario.is_active = 0, None, True
        usuario.save()
    salida.write("  cuentas: 6 usuarios demo")
