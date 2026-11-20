"""Datos de demostración (MAQUETA-SPEC sección 6).

Cada app del proyecto puede tener un módulo `demo.py` con una función `cargar(salida)`.
El comando los llama en el orden de INSTALLED_APPS, que respeta las dependencias.
Es idempotente: cada `cargar()` usa get_or_create / update_or_create o revisa si ya cargó.
"""

from importlib import import_module

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

APPS_PROYECTO = ["core", "cuentas", "personal", "clientes", "catalogo", "reservas", "abastecimiento", "ventas", "informes"]


class Command(BaseCommand):
    help = "Carga los datos de demostración de la maqueta (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Vacía la base (flush) antes de cargar.")

    def handle(self, *args, **opciones):
        if opciones["reset"]:
            call_command("flush", interactive=False, verbosity=0)
            self.stdout.write("Base de datos vaciada.")
        with transaction.atomic():
            for etiqueta in APPS_PROYECTO:
                if not apps.is_installed(etiqueta):
                    continue
                try:
                    modulo = import_module(f"{etiqueta}.demo")
                except ModuleNotFoundError as error:
                    if error.name != f"{etiqueta}.demo":
                        raise
                    continue
                modulo.cargar(self.stdout)
        self.stdout.write(self.style.SUCCESS("Datos de demostración listos."))
