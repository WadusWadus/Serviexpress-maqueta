"""Formularios base: estilo de los campos (RNF19, RNF20) y aviso de conflicto de edición (RNF23)."""

from django import forms

MENSAJE_CONFLICTO = (
    "Otro usuario modificó este registro mientras lo editaba. Revise los datos actuales y vuelva a guardar."
)


CLASE_CAMPO = "input w-full"
CLASE_LISTA = "select w-full"
CLASE_TEXTO_LARGO = "textarea w-full"
CLASE_CASILLA = "checkbox checkbox-primary checkbox-sm"


def aplicar_estilos(form):
    """Agrega a cada campo la clase de daisyUI que le corresponde."""
    for campo in form.fields.values():
        widget = campo.widget
        if isinstance(widget, forms.HiddenInput):
            continue
        if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
            clase = CLASE_CASILLA
        elif isinstance(widget, forms.RadioSelect):
            clase = "radio radio-primary radio-sm"
        elif isinstance(widget, forms.Select):
            clase = CLASE_LISTA
        elif isinstance(widget, forms.Textarea):
            clase = CLASE_TEXTO_LARGO
        else:
            clase = CLASE_CAMPO
        widget.attrs["class"] = (widget.attrs.get("class", "") + " " + clase).strip()


class ConEstilos:
    """Mixin: aplica las clases de daisyUI a todos los campos."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        aplicar_estilos(self)


class Formulario(ConEstilos, forms.Form):
    pass


class FormularioModelo(ConEstilos, forms.ModelForm):
    pass


class FormularioConVersion(FormularioModelo):
    """RNF23 · Lleva la versión leída en un campo oculto y la compara al guardar."""

    version_leida = forms.IntegerField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["version_leida"].initial = self.instance.version

    def clean(self):
        datos = super().clean()
        leida = datos.get("version_leida")
        if self.instance.pk and leida is not None and leida != self.instance.version:
            raise forms.ValidationError(MENSAJE_CONFLICTO, code="conflicto_version")
        return datos


class CampoFecha(forms.DateField):
    widget = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
