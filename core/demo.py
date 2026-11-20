"""Datos demo · S6 · una sección de ayuda por módulo (HU03). Los pasos siguen los flujos básicos de los CU."""

from .models import SeccionAyuda

SECCIONES = [
    ("general", "Manual general",
     "SERVIEXPRESS es el sistema del taller: reservas, atención, ventas, abastecimiento e informes.\n"
     "1. Ingrese con su usuario y contraseña.\n2. Use el menú superior: solo verá los módulos de su perfil.\n"
     "3. El botón «?» abre la ayuda de la pantalla en que está.\n4. Tras 15 minutos sin actividad la sesión se cierra."),
    ("usuarios", "Cuentas y perfiles",
     "1. Entre a Administración › Usuarios.\n2. Pulse «Nueva cuenta», complete los datos y elija el perfil.\n"
     "3. Para quitar el acceso, use «Desactivar»: las cuentas no se borran.\n"
     "Las cuentas de clientes se crean desde la ficha del cliente."),
    ("auditoria", "Log de auditoría",
     "1. Entre a Administración › Auditoría.\n2. Filtre por operación, entidad o fechas.\n"
     "Aquí quedan los accesos denegados y los cambios en boletas, facturas y órdenes. El log no se edita."),
    ("personal", "Empleados",
     "1. Entre a Administración › Empleados y pulse «Nuevo empleado».\n"
     "2. Marque al menos una función: «solicita productos» o «ejecuta servicios».\n"
     "3. Asocie su cuenta de usuario para que el sistema reconozca sus funciones."),
    ("festivos", "Días festivos",
     "1. Entre a Administración › Días festivos.\n2. Elija el año y pulse «Nuevo festivo».\n"
     "Las fechas festivas no se ofrecen al reservar."),
    ("clientes", "Fichas de clientes",
     "1. Entre a Clientes › Fichas de clientes.\n2. «Nueva ficha» registra al cliente y su usuario web en un solo paso.\n"
     "3. Busque por RUT, nombre o apellido y use «Modificar ficha» para actualizar datos. El RUT no cambia."),
    ("fiado", "Habilitar fiado",
     "1. Entre a Clientes › Habilitar fiado.\n2. Active el interruptor del cliente.\n"
     "Solo los clientes habilitados tienen la opción «Venta fiada» al emitir una boleta."),
    ("reserva_web", "Reservar hora",
     "1. Elija el servicio.\n2. Elija la fecha y una hora libre.\n3. Revise el resumen y pulse «Confirmar».\n"
     "En «Mis reservas» puede cambiar o anular una reserva futura."),
    ("agenda", "Agenda del local",
     "1. «Agenda» muestra las reservas de hoy y de los próximos días.\n"
     "2. «Reservar en el local»: busque al cliente por RUT, elija servicio, fecha y hora, y confirme.\n"
     "3. Desde la agenda puede cambiar o anular reservas."),
    ("atencion", "Atención en el taller",
     "1. «Reservas de hoy» lista los clientes con hora.\n2. Pulse «Registrar servicio», agregue una observación y registre.\n"
     "3. Si el cliente llegó sin reserva, use «Cliente sin reserva» e ingrese su RUT.\n"
     "Si el cliente no está registrado, derívelo al Empleado Administrativo."),
    ("ventas", "Boletas y facturas",
     "1. «Nueva boleta»: busque al cliente, marque los servicios pendientes y confirme.\n"
     "2. Desde la boleta puede imprimirla, modificarla o anularla con motivo. Las boletas no se eliminan.\n"
     "3. «Nueva factura»: mismo flujo, más los datos de facturación."),
    ("abastecimiento", "Abastecimiento",
     "1. Registre a los proveedores.\n2. «Nueva orden»: elija proveedor, productos y cantidades (solo empleados habilitados).\n"
     "3. «Recepcionar»: ingrese el N° de orden y lo recibido. Lo que no se pidió se rechaza.\n"
     "Una orden sin recepciones se puede modificar o eliminar; su número no se reutiliza."),
    ("informes", "Informes",
     "1. Elija el tipo de informe.\n2. Aplique filtros de fecha, cliente, servicio, empleado o proveedor y pulse «Generar».\n"
     "3. Use «Imprimir» o exporte a Excel, Word o texto."),
    ("estadisticas_web", "Estadísticas web",
     "Muestra las visitas a las páginas públicas y de reserva por día, semana y mes."),
    ("ayuda", "Ayuda", "Este manual. Desde cualquier pantalla, el botón «?» abre la sección del módulo en uso."),
]


def cargar(salida):
    for orden, (modulo, titulo, contenido) in enumerate(SECCIONES):
        SeccionAyuda.objects.update_or_create(modulo=modulo, defaults={"titulo": titulo, "contenido": contenido, "orden": orden})
    salida.write(f"  core: {len(SECCIONES)} secciones de ayuda")
