"""HU01, HU02 · Formularios de ingreso y de cuentas del personal."""

from django import forms
from django.contrib.auth import password_validation

from core.forms import Formulario, FormularioModelo

from .models import Usuario

PERFILES_PERSONAL = [p for p in Usuario.PERFILES if p[0] != Usuario.CLIENTE]


class IngresoForm(Formulario):
    """HU01 · RF01"""

    usuario = forms.CharField(label="Usuario", max_length=150)
    contrasena = forms.CharField(label="Contraseña", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["usuario"].widget.attrs.update(autofocus=True, autocomplete="username", autocapitalize="none")
        self.fields["contrasena"].widget.attrs.update(autocomplete="current-password")


class ConContrasenaMixin(forms.Form):
    """Contraseña inicial con confirmación y las reglas de Django."""

    password1 = forms.CharField(label="Contraseña inicial", widget=forms.PasswordInput, strip=False,
                                help_text="Mínimo 8 caracteres; no solo números ni una contraseña común.")
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput, strip=False)

    def clean_password2(self):
        p1, p2 = self.cleaned_data.get("password1"), self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        if p2:
            password_validation.validate_password(p2)
        return p2


class UsuarioCrearForm(FormularioModelo, ConContrasenaMixin):
    """HU02 · RF02 · Cuentas del personal (las de cliente se crean con la ficha, HU04)."""

    perfil = forms.ChoiceField(label="Perfil", choices=PERFILES_PERSONAL)

    class Meta:
        model = Usuario
        fields = ["username", "first_name", "last_name", "email", "perfil"]
        labels = {"username": "Usuario", "first_name": "Nombres", "last_name": "Apellidos", "email": "Correo"}

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password1"])
        if commit:
            usuario.save()
        return usuario


class UsuarioEditarForm(FormularioModelo):
    """HU02 · RF02, RF03 · Modificar nombre, correo y perfil."""

    class Meta:
        model = Usuario
        fields = ["first_name", "last_name", "email", "perfil", "is_active"]
        labels = {"first_name": "Nombres", "last_name": "Apellidos", "email": "Correo", "is_active": "Cuenta activa"}
        help_texts = {"is_active": "Una cuenta inactiva no puede ingresar. Las cuentas no se borran."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.perfil == Usuario.CLIENTE:
            # El perfil de un cliente queda fijo: su cuenta está unida a la ficha (HU04).
            self.fields["perfil"].disabled = True
        else:
            self.fields["perfil"].choices = PERFILES_PERSONAL
