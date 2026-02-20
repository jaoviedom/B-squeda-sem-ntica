from django.urls import path
from . import views

app_name = "tienda"

urlpatterns = [
    path("", views.home, name="home"),
    # Ruta raíz ("/") → ejecuta la vista 'home'.
    # 'name="home"' permite referenciarla en plantillas con {% url 'tienda:home' %}.
    path("productos/", views.lista_productos, name="lista_productos"),
    # Ruta "/productos/" → muestra la lista de productos.
    # Usa la vista 'lista_productos'.
    path("productos/<int:pk>/", views.detalle_producto, name="detalle_producto"),
    # Ruta dinámica "/productos/1/" o "/productos/5/"...
    # <int:pk> captura el número de ID (primary key) del producto.
    # Llama a la vista 'detalle_producto' con ese 'pk'.
    path("pedidos/", views.lista_pedidos, name="lista_pedidos"),
    # Ruta "/pedidos/" → muestra todos los pedidos registrados.
    # Usa la vista 'lista_pedidos'.
    path("pedidos/<int:pk>/", views.detalle_pedido, name="detalle_pedido"),
    # Ruta dinámica "/pedidos/3/"...
    # Llama a 'detalle_pedido' mostrando info de un pedido específico.
    path("clientes/<int:pk>/", views.detalle_cliente, name="detalle_cliente"),
    # Ruta dinámica "/clientes/2/"...
    # Muestra los datos de un cliente específico y sus pedidos.
    path("productos/nuevo/", views.crear_producto, name="crear_producto"),  # Crear
    path("productos/<int:pk>/editar/", views.editar_producto, name="editar_producto"),  # Editar
    path("productos/<int:pk>/eliminar/", views.eliminar_producto, name="eliminar_producto",),  # Eliminar
    # Pedidos
    path("pedidos/<int:pk>/eliminar/", views.eliminar_pedido, name="eliminar_pedido"),
    path("pedidos/nuevo-items/", views.crear_pedido_items, name="crear_pedido_items"),
    path("pedidos/<int:pk>/editar-items/", views.editar_pedido_items, name="editar_pedido_items"),

    path("buscar/", views.buscar_view, name="buscar"),
]
