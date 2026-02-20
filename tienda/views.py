# Importamos utilidades para renderizar plantillas y para devolver un 404 si no existe el objeto
from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.db.models import Sum, F
from .models import Producto, Pedido, Cliente
from .forms import ProductoForm, PedidoSimpleForm, PedidoItemFormSet
from django.views.decorators.http import require_GET
from core.ia.buscador import buscar_productos


# Vista de inicio (solo muestra una plantilla básica sin datos)
def home(request):
    # render() recibe: request, ruta de la plantilla, contexto (diccionario)
    return render(request, "tienda/home.html", {})


# Vista que lista todos los productos
def lista_productos(request):
    # ORM: trae todos los productos y los ordena por nombre
    productos = Producto.objects.all().order_by("nombre")
    # Pasamos la lista de productos al template
    return render(request, "tienda/lista_productos.html", {"productos": productos})


# Vista de detalle de un producto
def detalle_producto(request, pk):
    # Busca un producto por clave primaria (pk); si no existe, devuelve 404 automáticamente
    producto = get_object_or_404(Producto, pk=pk)
    # Pasamos el objeto producto a la plantilla
    return render(request, "tienda/detalle_producto.html", {"producto": producto})


# Vista que lista todos los pedidos
def lista_pedidos(request):
    pedidos = Pedido.objects.annotate(
        total_productos=Sum("items__cantidad"),
        total_precio=Sum(F("items__cantidad") * F("items__precio_unitario")),
    )
    return render(request, "tienda/lista_pedidos.html", {"pedidos": pedidos})


# Vista de detalle de un pedido
def detalle_pedido(request, pk):
    pedido = get_object_or_404(
        Pedido.objects.select_related("cliente").prefetch_related("items__producto"),
        pk=pk,
    )
    items = pedido.items.all()
    total_unidades = sum(it.cantidad for it in items)
    total_pedido = sum(it.cantidad * it.precio_unitario for it in items)
    # Calcula el subtotal por línea para cada item
    for it in items:
        it.line_total = it.cantidad * it.precio_unitario
    return render(
        request,
        "tienda/detalle_pedido.html",
        {
            "pedido": pedido,
            "items": items,
            "total_unidades": total_unidades,
            "total_pedido": total_pedido,
        },
    )


# Vista de detalle de un cliente
def detalle_cliente(request, pk):
    # Traemos el cliente o 404 si no existe
    cliente = get_object_or_404(Cliente, pk=pk)
    # Desde el cliente accedemos a sus pedidos → relación inversa: cliente.pedidos
    # Optimización: select_related para el cliente y prefetch_related para los productos
    pedidos = (
        cliente.pedidos.select_related("cliente")
        .prefetch_related("items__producto")
        .order_by("-fecha")
    )
    # Enviamos al template tanto el cliente como su lista de pedidos
    return render(
        request, "tienda/detalle_cliente.html", {"cliente": cliente, "pedidos": pedidos}
    )


# Vista para CREAR un producto
def crear_producto(request):
    if request.method == "POST":
        # Vinculamos datos del formulario (POST) a la instancia de ProductoForm
        form = ProductoForm(request.POST)
        if form.is_valid():
            # Si es válido, guardamos el objeto en la BD
            form.save()
            # Redirigimos para evitar reenvío del POST al refrescar
            return redirect("tienda:lista_productos")
        # Si no es válido, caemos al render con errores incluidos en 'form'
    else:
        # GET: formulario vacío
        form = ProductoForm()

    # Renderizamos la plantilla con el formulario (vacío o con errores)
    return render(request, "tienda/crear_producto.html", {"form": form})


# Vista para EDITAR un producto existente
def editar_producto(request, pk):
    # Obtenemos el producto o devolvemos 404 si no existe
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == "POST":
        # Vinculamos datos de POST y la instancia a editar
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()  # esto actualiza 'producto' en BD
            return redirect("tienda:detalle_producto", pk=producto.pk)
    else:
        # GET: mostramos el formulario precargado con datos del producto
        form = ProductoForm(instance=producto)

    return render(
        request, "tienda/editar_producto.html", {"form": form, "producto": producto}
    )


# Vista para ELIMINAR un producto
def eliminar_producto(request, pk):
    # Buscamos el producto o devolvemos 404 si no existe
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == "POST":
        # Si es POST, significa que ya confirmamos la eliminación
        producto.delete()
        # Redirigimos a la lista de productos después de eliminar
        return redirect("tienda:lista_productos")

    # Si es GET, mostramos la plantilla de confirmación
    return render(request, "tienda/eliminar_producto.html", {"producto": producto})


# ELIMINAR pedido
def eliminar_pedido(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if request.method == "POST":
        pedido.delete()
        return redirect("tienda:lista_pedidos")
    return render(request, "tienda/eliminar_pedido.html", {"pedido": pedido})


# CREAR pedido con items
@transaction.atomic
def crear_pedido_items(request):
    if request.method == "POST":
        pedido_form = PedidoSimpleForm(request.POST)
        if pedido_form.is_valid():
            pedido = pedido_form.save()  # Crea el pedido para asociarle ítems
            formset = PedidoItemFormSet(request.POST, instance=pedido)
            if formset.is_valid():
                formset.save()  # Crea/guarda todas las líneas
                return redirect("tienda:detalle_pedido", pk=pedido.pk)
        else:
            # Si el pedido no es válido, necesitamos un pedido temporal para el formset
            pedido = Pedido()  # no guardado
            formset = PedidoItemFormSet(request.POST, instance=pedido)
    else:
        pedido_form = PedidoSimpleForm()
        formset = PedidoItemFormSet()

    return render(
        request,
        "tienda/crear_pedido_items.html",
        {
            "pedido_form": pedido_form,
            "formset": formset,
        },
    )


# EDITAR pedido con items
@transaction.atomic
def editar_pedido_items(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if request.method == "POST":
        pedido_form = PedidoSimpleForm(request.POST, instance=pedido)
        formset = PedidoItemFormSet(request.POST, instance=pedido)
        if pedido_form.is_valid() and formset.is_valid():
            pedido_form.save()
            formset.save()
            return redirect("tienda:detalle_pedido", pk=pedido.pk)
    else:
        pedido_form = PedidoSimpleForm(instance=pedido)
        formset = PedidoItemFormSet(instance=pedido)

    return render(
        request,
        "tienda/editar_pedido_items.html",
        {
            "pedido": pedido,
            "pedido_form": pedido_form,
            "formset": formset,
        },
    )

@require_GET
def buscar_view(request):
    q = request.GET.get("q", "")
    resultados = buscar_productos(q, k=5) if q else []
    return render(request, "tienda/buscar.html", {"q": q, "resultados": resultados})
