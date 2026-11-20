from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction

from core.forms import FormularioConVersion, FormularioModelo
from core.validadores import normalizar_rut
from cuentas.forms import ConContrasenaMixin

from .models import Cliente


class ClienteNuevoForm(FormularioModelo, ConContrasenaMixin):
    """HU04 · RF05 · Ficha + cuenta de cliente en un solo formulario."""

    usuario = forms.CharField(label="Usuario para ingresar a la web", max_length=150,
                              help_text="Con este usuario el cliente reserva horas por Internet.")

    class Meta:
        model = Cliente
        fields = ["rut", "nombres", "apellidos", "telefono", "email", "direccion"]

    field_order = ["rut", "nombres", "apellidos", "telefono", "email", "direccion", "usuario", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rut"].widget.attrs["placeholder"] = "12345678-9"
        self.fields["usuario"].widget.attrs["autocapitalize"] = "none"

    def clean_rut(self):
        return normalizar_rut(self.cleaned_data["rut"])

    def clean_usuario(self):
        nombre = self.cleaned_data["usuario"].strip()
        if get_user_model().objects.filter(username__iexact=nombre).exists():
            raise forms.ValidationError("Ya existe una cuenta con ese usuario.")
        return nombre

    @transaction.atomic
    def save(self, commit=True):
        """Crea la cuenta (perfil CLIENTE) y la ficha; si algo falla, no se crea ninguna."""
        Usuario = get_user_model()
        datos = self.cleaned_data
        cuenta = Usuario(
            username=datos["usuario"], first_name=datos["nombres"], last_name=datos["apellidos"],
            email=datos.get("email", ""), perfil=Usuario.CLIENTE,
        )
        cuenta.set_password(datos["password1"])
        cuenta.save()
        cliente = super().save(commit=False)
        cliente.usuario = cuenta
        cliente.save()
        return cliente


class ClienteEditarForm(FormularioConVersion):
    """HU05 · RF06 · RNF23 · El RUT no se edita."""

    class Meta:
        model = Cliente
        fields = ["nombres", "apellidos", "telefono", "email", "direccion"]

    @transaction.atomic
    def save(self, commit=True):
        cliente = super().save(commit)
        cuenta = cliente.usuario
        cuenta.first_name, cuenta.last_name, cuenta.email = cliente.nombres, cliente.apellidos, cliente.email
        cuenta.save(update_fields=["first_name", "last_name", "email"])
        return cliente
