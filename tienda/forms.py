from django import forms
from django.forms import inlineformset_factory
from .models import Producto, Cliente, Pedido, PedidoItem

# ModelForm: genera automáticamente campos basados en el modelo Producto
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        # Definimos qué campos mostrar en el formulario
        fields = ["nombre", "descripcion", "precio"]
        # Opcional: widgets para personalizar inputs HTML
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Nombre del producto"}),
            "descripcion": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Descripción breve"}
            ),
            "precio": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    # Validación personalizada de un campo:
    # Si el precio es negativo o cero, rechazamos el dato con un error legible
    def clean_precio(self):
        precio = self.cleaned_data.get("precio")
        if precio is not None and precio <= 0:
            raise forms.ValidationError("El precio debe ser mayor que cero.")
        return precio


# Ejemplo 2: ModelForm para Cliente
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombre", "correo", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Nombre completo"}),
            "correo": forms.EmailInput(attrs={"placeholder": "correo@ejemplo.com"}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()
        if len(nombre) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres.")
        return nombre

class PedidoSimpleForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ["cliente", "estado"]

class PedidoItemForm(forms.ModelForm):
    class Meta:
        model = PedidoItem
        fields = ["producto", "cantidad", "precio_unitario"]
        widgets = {
            "cantidad": forms.NumberInput(attrs={"min": "1", "step": "1"}),
            "precio_unitario": forms.NumberInput(attrs={"min": "0", "step": "0.01"}),
        }

# Creamos un formset inline: varios PedidoItem asociados a un Pedido
PedidoItemFormSet = inlineformset_factory(
    parent_model=Pedido,
    model=PedidoItem,
    form=PedidoItemForm,
    extra=1,            # cuántas filas “vacías” mostrar por defecto
    can_delete=True     # permitir borrar filas
)