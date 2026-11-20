# Especificación de la maqueta funcional — Sistema de Gestión Taller Mecánico SERVIEXPRESS

> **Para quién es este archivo:** el equipo (Fernanda, Thomas, Emilio) y el asistente de IA que genera el código (PyCharm u otro).
> **Qué es:** la especificación de una maqueta en Django que muestra **cada historia de usuario (HU01–HU24) funcionando**, con sus criterios de aceptación, construida **sprint por sprint** en el mismo orden del Product Backlog del informe N°2.
> **Fuente:** `propuesta-trabajo-informe-2.md` / `informe-final-1.0.docx` (RF01–RF33, RNF01–RNF25, HU01–HU25, CU01–CU17, S1–S6). Si algo de aquí contradice el informe, **manda el informe**: avisar y corregir este archivo.
> **Dónde va:** copiar este archivo a la raíz del proyecto Django (junto a `manage.py`) y mantenerlo actualizado ahí.

---

## 0. Reglas de trabajo (leer antes de cada sesión)

Estas reglas existen para que la maqueta quede completa y sin huecos entre sprints. El asistente de IA debe cumplirlas tal cual.

1. **Se trabaja un sprint a la vez, en orden: S0 → S1 → S2 → S3 → S4 → S5 → S6.** No se empieza un sprint sin haber cerrado el anterior (checklist de la sección 11).
2. **Dentro del sprint, las HU se construyen en el orden indicado** en su sección. Ese orden respeta las dependencias (no se reserva sin catálogo, no se vende sin servicio realizado, no se recepciona sin orden).
3. **No se adelanta trabajo de sprints futuros.** No crear modelos, campos, pantallas ni botones de HU que todavía no tocan. Cada sprint indica en "Fuera de este sprint" qué no hacer.
4. **Una HU está terminada en la maqueta** cuando cumple la Definition of Done de la sección 3. No hay HU "a medias": si no alcanza, queda sin marcar en el registro de avance (sección 14) y se avisa.
5. **Todo se ve en pantallas propias.** El Django Admin (`/admin/`) se usa solo para depurar; **ninguna HU se demuestra desde el admin**.
6. **No inventar reglas de negocio.** Las reglas salen de los RF, RNF, HU y CU citados aquí. Lo que el caso no define (preguntas V01–V08 del informe) se resuelve con un **valor de demostración configurable** marcado en el código con `# DEMO: pendiente Vxx`. Nunca se presenta como regla del cliente.
7. **Trazabilidad en el código.** Cada vista, modelo y test lleva un comentario o docstring con su HU y RF, por ejemplo `"""HU16 · RF20, RF23 · CU10"""`. Cada pantalla muestra un chip de trazabilidad (sección 5.4).
8. **Un commit por HU**, con el mensaje `HUxx: <nombre de la historia>`. Las migraciones aplicadas en el VPS no se borran ni se reescriben.
9. Idioma: código en español para el dominio (modelos, campos, URLs) e inglés solo donde Django lo exige. Interfaz y mensajes 100% en español.

---

## 1. Objetivo y alcance de la maqueta

**Objetivo:** demostrar, con un sistema web navegable y datos de ejemplo, que cada historia de usuario del Product Backlog se puede ejecutar y cumple sus criterios de aceptación. Sirve como incremento visible en cada Sprint Review y como evidencia ante el docente.

**Dentro del alcance (24 historias):** HU01–HU24, en los sprints S1–S6.

**Fuera del alcance** (igual que el informe, sección 1.2):

| Fuera | Motivo |
|---|---|
| HU25 multiempresa / multimoneda (RNF24, RNF25) | Fuera de la 1ª versión por decisión del PO |
| Emisión electrónica ante el SII | El caso no la pide (V02). La boleta es un documento interno imprimible |
| Pagos en línea, bancos | Fuera del alcance del sistema |
| Cobranza del fiado | Se registra y controla el fiado; no se cobra (1.2) |
| Diagnóstico técnico del vehículo | Fuera del alcance |
| Datos del vehículo (patente, marca) | Pregunta abierta V06: no se agregan campos |
| App móvil nativa | El acceso es por navegador, también desde el celular (RNF19, RNF21) |
| Login con Google / ClaveÚnica | Fuera del alcance (1.2) |

**RNF que la maqueta demuestra:** RNF05, RNF06, RNF07, RNF08, RNF09, RNF10, RNF11, RNF12 (en el VPS), RNF18/RNF19 (reserva en 3 pantallas, usable a 360 px), RNF20, RNF21, RNF23 (aviso de conflicto) y RNF02 en su parte verificable (listas paginadas de 50).
**RNF que no se demuestran** (requieren infraestructura o mediciones reales): RNF01, RNF03 en su tiempo, RNF04, RNF13 (legal), RNF14–RNF17, RNF22 (se prueba solo en Chrome y un navegador más). Se declaran así en la demo; no se simulan.

---

## 2. Stack técnico

| Elemento | Decisión |
|---|---|
| Lenguaje | Python 3.13 (en local; Django 5.2 acepta 3.10–3.14, así que el VPS puede usar la versión que traiga su sistema) |
| Framework | Django 5.2 (LTS) con vistas y plantillas del servidor. **Sin** Django REST Framework ni frontend separado |
| Base de datos | SQLite en local y en el VPS de prueba (es una maqueta). El código no usa nada propio de SQLite, para poder pasar a PostgreSQL después |
| Interfaz | Tailwind CSS 4.3.3 + daisyUI 5.7.50, compilados a `static/css/app.css` con `npm run css` (fuente en `frontend/app.css`). Node solo se usa para compilar; el servidor sirve el CSS ya generado. Diseño responsivo (RNF19) |
| Exportación (S6) | `openpyxl` (Excel) y `python-docx` (Word) |
| Servidor en el VPS | `gunicorn` + `nginx` + certificado HTTPS con `certbot` (RNF12) |
| Configuración | Variables de entorno: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` |
| Localización | `LANGUAGE_CODE = "es-cl"`, `TIME_ZONE = "America/Santiago"`, `USE_TZ = True` |

`requirements.txt` (se completa en S6): `Django>=5.2,<5.3`, `gunicorn`, `openpyxl`, `python-docx`.

---

## 3. Definition of Done de la maqueta (por historia)

Una HU se marca como terminada en la sección 14 solo si cumple **todo** esto:

1. **Modelo y migración** creados (si la HU los necesita).
2. **Pantallas propias** con su URL, enlazadas desde el menú del perfil que corresponde.
3. **Permisos aplicados**: un perfil sin acceso recibe "Acceso denegado" y el intento queda en el log (RNF06).
4. **Validaciones** con mensajes en español que indican el campo y la causa (RNF20).
5. **Un test por cada criterio de aceptación** de la HU (los nombres están en cada ficha), y todos pasan con `python manage.py test`.
6. **Datos de demostración** agregados a `cargar_demo` (sección 6) para que la HU se pueda mostrar sin cargar nada a mano.
7. **Chip de trazabilidad** visible en la pantalla (sección 5.4).
8. **Guion de demostración** de la HU ejecutado a mano en local y luego en el VPS.
9. Las HU de sprints anteriores **siguen funcionando** (todos los tests en verde).

---

## 4. Estructura del proyecto

```
serviexpress/                 ← raíz del repositorio
├── manage.py
├── MAQUETA-SPEC.md           ← este archivo
├── requirements.txt
├── config/                   ← settings, urls, wsgi
├── core/                     ← base común (S0): auditoría, permisos, correlativos, ayuda, plantillas base
├── cuentas/                  ← Área 1 · Acceso y seguridad (HU01, HU02, HU03 en core)
├── clientes/                 ← Área 2 · Clientes (HU04–HU07)
├── reservas/                 ← Área 3 · Reservas y atención (HU08–HU11)
├── catalogo/                 ← Área 4 · Catálogo (HU12, HU13)
├── personal/                 ← Área 4 · Personal (HU14)
├── abastecimiento/           ← Área 5 · Abastecimiento (HU15–HU18)
├── ventas/                   ← Área 6 · Ventas (HU19–HU21)
├── informes/                 ← Área 7 · Informes y gestión (HU22–HU24)
├── templates/                ← base.html y parciales comunes
└── static/
```

Cada app tiene `models.py`, `forms.py`, `views.py`, `urls.py` (con `app_name`), `templates/<app>/` y `tests/test_huXX.py` (un archivo por HU).

**Dependencias entre apps** (una app solo importa de las que están a su izquierda):
`core → cuentas → personal → clientes → catalogo → reservas → abastecimiento → ventas → informes`

---

## 5. Base común (se construye en S0 y la usan todas las HU)

### 5.1 Usuario y perfiles (RF01–RF03)

**El modelo de usuario propio se crea en S0, antes de la primera migración.** Cambiarlo después obliga a borrar la base de datos.

`cuentas.Usuario(AbstractUser)`:

| Campo | Tipo | Uso |
|---|---|---|
| `perfil` | choices: `ADMIN`, `ADMINISTRATIVO`, `MECANICO`, `CLIENTE` | Determina los módulos accesibles (RF03) |
| `intentos_fallidos` | entero, default 0 | Bloqueo tras 5 intentos (RNF10) |
| `bloqueado_hasta` | fecha-hora, nulo | Bloqueo de 15 minutos (RNF10) |

`AUTH_USER_MODEL = "cuentas.Usuario"`. Contraseñas con el hasher por defecto de Django (PBKDF2, RNF05); nunca se muestran ni se exportan.

### 5.2 Permisos por módulo (RF03, RNF06, RNF07)

En `core/permisos.py` hay un diccionario único `MODULOS_POR_PERFIL` y un decorador `@requiere_modulo("<modulo>")` (y su mixin `RequiereModuloMixin` para vistas de clase).

| Módulo | ADMIN | ADMINISTRATIVO | MECANICO | CLIENTE | Sprint |
|---|:-:|:-:|:-:|:-:|---|
| `usuarios` (cuentas y perfiles) | ✔ | | | | S1 |
| `auditoria` (ver log) | ✔ | | | | S1 |
| `personal` (empleados) | ✔ | | | | S1 |
| `clientes` (fichas) | ✔ | ✔ | | | S1 |
| `festivos` | ✔ | | | | S1 |
| `catalogo` (servicios y productos) | ✔ | ✔ | | | S2 |
| `reserva_web` (reservar, mis reservas) | | | | ✔ | S2 |
| `agenda` (reservas en el local) | ✔ | ✔ | | | S2 |
| `atencion` (registrar servicio realizado) | ✔ | | ✔ | | S3 |
| `ventas` (boletas y facturas) | ✔ | ✔ | | | S3 |
| `abastecimiento` (proveedores, órdenes, recepciones) | ✔ | ✔ | | | S4 |
| `fiado` (habilitar) | ✔ | | | | S5 |
| `informes` | ✔ | ✔ | | | S5 |
| `estadisticas_web` | ✔ | | | | S6 |
| `ayuda` | ✔ | ✔ | ✔ | ✔ | S6 |

Reglas:
- **ADMIN accede a todos los módulos** (RNF07): el decorador lo deja pasar siempre.
- Acceso denegado → respuesta 403 con la plantilla `core/acceso_denegado.html` **y** un registro en el log con operación `ACCESO_DENEGADO` (RNF06).
- Además del módulo, hay **dos restricciones por función del empleado** (RF18), que valen para todos los perfiles, incluido ADMIN:
  - Generar órdenes de pedido exige `Empleado.solicita_productos = True` (RF23, S4).
  - Registrar servicios realizados exige `Empleado.ejecuta_servicios = True` (C07, S3).
  En los datos de demostración el administrador figura como empleado con ambas funciones, para que la demo no se trabe.
- Las filas de módulos de sprints futuros se agregan **en su sprint**, no antes.

### 5.3 Log de auditoría (RNF06, RNF08)

`core.RegistroAuditoria`: `fecha_hora` (auto), `usuario` (FK nulo), `operacion` (choices: `CREAR`, `MODIFICAR`, `ANULAR`, `ELIMINAR`, `ACCESO_DENEGADO`, `LOGIN_FALLIDO`, `BLOQUEO`), `entidad` (texto: "Boleta", "OrdenPedido", …), `entidad_id` (texto), `detalle` (JSON: valores anteriores y nuevos).

Función única `core.auditoria.registrar(usuario, operacion, entidad, entidad_id, detalle=None)`. Nadie escribe en la tabla de otra forma. El log no tiene pantallas de edición ni de borrado.

Lo que **debe** quedar registrado: intentos de acceso denegados (S1), creación, modificación, anulación y eliminación de **boletas, facturas y órdenes de pedido** (S3, S4, S5).

### 5.4 Plantilla base e interfaz

`templates/base.html` (shell con menú lateral; la banda de aviso y el chip de trazabilidad solo se muestran con `DJANGO_DEMO=1`; las credenciales demo no se muestran nunca):
- Barra superior con el nombre "SERVIEXPRESS", el menú **según el perfil** (solo muestra módulos permitidos), el usuario conectado y "Salir".
- **Banda fija de aviso:** "Maqueta de demostración — datos ficticios".
- Zona de mensajes (`django.contrib.messages`) con colores de Bootstrap.
- **Chip de trazabilidad** en el pie de cada pantalla: bloque `{% block trazabilidad %}` que cada plantilla llena, por ejemplo `HU08 · RF10, RF11 · CU04 · S2`. En la demo, el docente ve qué historia está mirando.
- Botón **"?" de ayuda** (se activa en S6 con HU03; antes no se dibuja).
- Responsivo: sin desplazamiento horizontal desde 360 px (RNF19).

Páginas generales de S0: `/` (inicio público con botones "Reservar hora" e "Ingresar") y `/panel/` (inicio después de ingresar, con accesos directos según perfil).

Listados: paginados de a 50 registros (RNF02) y con buscador cuando el informe lo pide.

### 5.5 Correlativos (RF20, RF22, boletas)

`core.Correlativo`: `nombre` (único: `orden_pedido`, `boleta`, `factura`) y `ultimo` (entero).
Función `core.correlativos.siguiente(nombre)` que, dentro de `transaction.atomic()` y con `select_for_update()`, suma 1 y devuelve el número.
**No se usa `max(numero) + 1`**: si se eliminara la última orden, su número se reutilizaría, y RF22 lo prohíbe.

### 5.6 Aviso de conflicto de edición (RNF23)

Mixin `core.models.ConVersion` con un campo `version` (entero). El formulario de edición lleva la versión en un campo oculto; al guardar, si la versión en la base ya cambió, no se guarda y se muestra: *"Otro usuario modificó este registro mientras lo editaba. Revise los datos actuales y vuelva a guardar."*
Se aplica a: `Cliente` (S1), `Servicio` (S2), `OrdenPedido` (S5) y `Boleta` (S3).

### 5.7 Valores de demostración configurables (no son reglas del cliente)

En `config/settings.py`, bloque `SERVIEXPRESS`:

```python
SERVIEXPRESS = {
    # DEMO: pendiente V07 (horario de atención no definido en el caso)
    "DIAS_ATENCION": [0, 1, 2, 3, 4, 5],   # lunes a sábado
    "HORA_INICIO": 9,
    "HORA_FIN": 18,                       # último bloque empieza a las 17:00
    "DURACION_BLOQUE_MIN": 60,
    "RESERVAS_POR_BLOQUE": 1,
    "DIAS_ADELANTE_RESERVA": 30,
    # RNF10 y RNF11 (sí son requisitos)
    "MAX_INTENTOS_LOGIN": 5,
    "MINUTOS_BLOQUEO": 15,
}
SESSION_COOKIE_AGE = 15 * 60          # RNF11
SESSION_SAVE_EVERY_REQUEST = True     # la inactividad se cuenta desde la última acción
```

---

## 6. Datos de demostración

Comando `python manage.py cargar_demo` (en `core/management/commands/`). Reglas:
- **Idempotente:** se puede correr varias veces sin duplicar (usar `get_or_create` / `update_or_create`).
- **Crece por sprint:** cada sprint agrega su bloque; no se cargan datos de modelos que aún no existen.
- **Fechas relativas a hoy** (`date.today() + timedelta(...)`), para que la demo funcione cualquier día.
- Opción `--reset`: hace `flush` y vuelve a cargar todo.

**Usuarios de demostración** (contraseña de todos: `Demo2026!`; no se muestra en la pantalla de ingreso, se entrega aparte):

| Usuario | Perfil | Empleado | Para demostrar |
|---|---|---|---|
| `admin` | ADMIN | Sí: solicita productos y ejecuta servicios | HU02, HU06, HU09, HU14, HU22–HU24 |
| `administrativo` | ADMINISTRATIVO | Sí: **solicita productos** | HU04, HU05, HU12–HU13, HU15–HU21 |
| `administrativo2` | ADMINISTRATIVO | Sí: **no** solicita productos | Rechazo de RF23 (HU16) |
| `mecanico` | MECANICO | Sí: ejecuta servicios | HU11 |
| `cliente1` | CLIENTE | — | HU08, HU10; cliente **habilitado para fiado** desde S5 |
| `cliente2` | CLIENTE | — | Cliente **no habilitado** para fiado (S5) |

Contenido por sprint: ver la línea "Datos demo" de cada sprint.

---

## 7. Sprint 0 — Preparación (antes del S1, sin historias)

**Objetivo:** dejar el esqueleto del proyecto andando en local y en el VPS, para que desde el S1 cada historia solo agregue funcionalidad.

| # | Tarea | Resultado verificable |
|---|---|---|
| 0.1 | Crear el proyecto `config` y las apps de la sección 4 (vacías), registrar todas en `INSTALLED_APPS` | `python manage.py check` sin errores |
| 0.2 | Crear `cuentas.Usuario` (5.1) y `AUTH_USER_MODEL` **antes del primer `migrate`** | `migrate` crea la tabla `cuentas_usuario` |
| 0.3 | Settings por variables de entorno (sección 2), localización, bloque `SERVIEXPRESS` (5.7) | Con `DJANGO_DEBUG=0` el sitio arranca |
| 0.4 | `core`: `RegistroAuditoria` + `registrar()` (5.3), `Correlativo` + `siguiente()` (5.5), mixin `ConVersion` (5.6), `permisos.py` con el decorador y la tabla vacía de módulos (5.2) | Tests: `test_correlativo_no_reutiliza`, `test_registrar_auditoria` |
| 0.5 | `base.html` (5.4), página de inicio `/`, `/panel/`, plantilla de acceso denegado | Se ve en el celular sin scroll horizontal |
| 0.6 | Comando `cargar_demo` vacío con la opción `--reset` | Corre sin errores |
| 0.7 | Repositorio git, `.gitignore` (sin `db.sqlite3`, `.env`, `staticfiles/`) | Primer commit |
| 0.8 | Despliegue en el VPS (sección 12) | La página de inicio responde por HTTPS |

**Fuera de este sprint:** login, menús por perfil con contenido, cualquier modelo de negocio.

---

## 8. Sprint 1 — "El taller controla quién accede y registra a su personal y a sus clientes" (18 pts)

**Orden de construcción:** HU01 → HU02 → HU14 → HU04 → HU05 → HU09.
**Datos demo:** los 6 usuarios de la sección 6; sus empleados con funciones; fichas de cliente para `cliente1` y `cliente2` y 3 clientes más; solo los feriados irrenunciables de 2026 y 2027 (1 ene, 1 may, 18 y 19 sep, 25 dic), según el CSV entregado por el equipo. Decisión del equipo: los demás feriados no se cargan; las pantallas de festivos y de reserva lo avisan con una ventana emergente (`parciales/aviso_feriados.html`).

### HU01 — Iniciar sesión (3 pts) · RF01 · RNF05, RNF10, RNF11 · CU01
*Como usuario del sistema (cliente o personal del taller), quiero ingresar con mi usuario y contraseña, para acceder solo a lo que me corresponde.*

- **URLs:** `/cuentas/ingresar/`, `/cuentas/salir/`.
- **Funcionamiento:**
  - Vista de ingreso propia (no basta la de Django) que antes de autenticar revisa `bloqueado_hasta`.
  - Ingreso correcto: pone `intentos_fallidos = 0` y redirige a `/panel/`.
  - Ingreso incorrecto: suma 1 a `intentos_fallidos`, registra `LOGIN_FALLIDO` y muestra *"Usuario o contraseña incorrectos"* (sin decir cuál de los dos).
  - Al 5° fallo consecutivo: `bloqueado_hasta = ahora + 15 min`, registra `BLOQUEO` y muestra *"Cuenta bloqueada por 15 minutos por intentos fallidos"*.
  - Cuenta desactivada (`is_active = False`): no ingresa.
  - Sesión expira a los 15 min sin actividad (5.7) y vuelve al ingreso con el mensaje *"Su sesión se cerró por inactividad"*.
  - Todas las vistas, salvo `/`, el ingreso y la ayuda pública, exigen sesión.
- **Criterios de aceptación → tests (`cuentas/tests/test_hu01.py`):**
  - Con datos correctos ingresa → `test_ingreso_correcto_redirige_al_panel` (uno por perfil, incluido el cliente).
  - Con datos incorrectos ve un error → `test_ingreso_incorrecto_muestra_error`.
  - Tras 5 intentos fallidos la cuenta se bloquea 15 min → `test_bloqueo_tras_cinco_intentos`, `test_bloqueo_expira_a_los_15_minutos` (simular el tiempo modificando `bloqueado_hasta`).
  - RNF05 → `test_contrasena_guardada_con_hash`.
- **Guion de demo:** ingresar como `mecanico` → ver solo su menú. Salir. Fallar 5 veces con `cliente2` → mensaje de bloqueo.

### HU02 — Cuentas y perfiles (5 pts) · RF02, RF03 · RNF06, RNF07 · CU02
*Como Administrador, quiero crear cuentas y asignarles un perfil, para controlar quién hace qué en el sistema.*

- **URLs:** `/cuentas/usuarios/` (lista con filtro por perfil), `/cuentas/usuarios/nuevo/`, `/cuentas/usuarios/<id>/editar/`, `/cuentas/usuarios/<id>/desactivar/`, `/auditoria/` (lista del log, filtrable por operación y fecha).
- **Funcionamiento:**
  - Crear cuenta del personal: usuario, nombre, correo, perfil (ADMIN, ADMINISTRATIVO, MECANICO) y contraseña inicial con confirmación.
  - Modificar: nombre, correo, perfil. Desactivar: `is_active = False` (no se borran cuentas).
  - Las cuentas de perfil CLIENTE no se crean aquí: se crean con la ficha de cliente (HU04).
  - Llenar la tabla `MODULOS_POR_PERFIL` con los módulos de S1 y aplicar el decorador en todas las vistas de S1.
- **Criterios de aceptación → tests (`cuentas/tests/test_hu02.py`):**
  - Una cuenta sin permiso a un módulo no puede entrar a él → `test_mecanico_no_entra_a_usuarios` (403).
  - …y el intento queda registrado → `test_acceso_denegado_queda_en_log`.
  - RNF07 → `test_admin_entra_a_todos_los_modulos` (recorre todas las URLs del menú).
  - `test_admin_crea_cuenta_con_perfil`, `test_cuenta_desactivada_no_ingresa`.
- **Guion de demo:** `admin` crea la cuenta `mecanico2`. Ingresar como `mecanico2` y escribir `/cuentas/usuarios/` en la barra → acceso denegado. Volver como `admin` a `/auditoria/` → aparece el intento.

### HU14 — Empleados y su función (3 pts) · RF18 · CU17
*Como Administrador, quiero registrar a los empleados y su función, para saber quién puede pedir productos y quién ejecuta servicios.*

- **Modelo `personal.Empleado`:** `rut` (único, con validación de dígito verificador), `nombres`, `apellidos`, `telefono`, `usuario` (OneToOne a `Usuario`, nulo: un empleado puede no tener cuenta), `solicita_productos` (bool), `ejecuta_servicios` (bool), `activo` (bool).
- **URLs:** `/personal/empleados/`, `/personal/empleados/nuevo/`, `/personal/empleados/<id>/editar/`.
- **Regla:** `clean()` exige al menos una función marcada → *"Marque al menos una función: solicitar productos o ejecutar servicios"*.
- **Criterios de aceptación → tests (`personal/tests/test_hu14.py`):**
  - Cada empleado tiene al menos una función marcada → `test_empleado_sin_funcion_es_rechazado`, `test_empleado_con_una_funcion_se_guarda`.
- **Guion de demo:** crear un empleado sin marcar funciones → error. Marcar "ejecuta servicios" → se guarda. La lista muestra las funciones de cada uno.

### HU04 — Registrar ficha de cliente (3 pts) · RF05 · CU03 · *historia de referencia = 3 pts*
*Como Empleado Administrativo, quiero registrar la ficha de un cliente con usuario y contraseña, para atenderlo y emitirle documentos.*

- **Modelo `clientes.Cliente` (con `ConVersion`):** `usuario` (OneToOne a `Usuario` con perfil CLIENTE), `rut` (único, validado), `nombres`, `apellidos`, `telefono`, `email`, `direccion`, `fecha_registro` (auto).
- **URL:** `/clientes/nuevo/`.
- **Funcionamiento:** un solo formulario crea en una transacción la ficha **y** la cuenta del cliente (usuario + contraseña, perfil CLIENTE). Si algo falla, no se crea ninguna de las dos.
- Quién registra al cliente (solo el personal o también el propio cliente por la web) es la pregunta abierta **V04**: en la maqueta lo registra el personal, que es lo que dice HU04. No se hace autorregistro.
- **Criterios de aceptación → tests (`clientes/tests/test_hu04.py`):**
  - La ficha queda guardada → `test_ficha_cliente_se_guarda`.
  - …y el cliente puede ingresar a la web con su usuario → `test_cliente_nuevo_puede_ingresar`.
  - `test_rut_duplicado_es_rechazado`, `test_rut_invalido_es_rechazado`.
- **Guion de demo:** `administrativo` registra a un cliente nuevo. Salir e ingresar con el usuario del cliente → ve su panel de cliente.

### HU05 — Modificar y consultar ficha (2 pts) · RF06 · CU03 · RNF23
*Como Empleado Administrativo, quiero modificar y consultar la ficha de un cliente, para mantener sus datos al día.*

- **URLs:** `/clientes/` (lista paginada de 50, buscador por RUT, nombre o apellido), `/clientes/<id>/` (ficha), `/clientes/<id>/editar/`.
- **Funcionamiento:** edita datos de contacto; el RUT no se edita. Usa la versión de `ConVersion` (5.6).
- **Criterios de aceptación → tests (`clientes/tests/test_hu05.py`):**
  - Los cambios quedan guardados y se ven en la consulta → `test_modificacion_se_ve_en_la_ficha`.
  - RNF23 → `test_edicion_concurrente_avisa_conflicto`.
  - RNF02 (parte verificable) → `test_lista_clientes_pagina_de_50`.
- **Guion de demo:** buscar "cliente1", cambiar teléfono, ver la ficha. Abrir la edición en dos pestañas y guardar en ambas → la segunda recibe el aviso de conflicto.

### HU09 — Días festivos (2 pts) · RF12 · CU05
*Como Administrador, quiero registrar los días festivos del año, para que nadie reserve cuando el taller no atiende.*

- **Modelo `reservas.DiaFestivo`:** `fecha` (única), `descripcion`.
- **URLs:** `/reservas/festivos/?anio=2026` (lista por año con selector), `/reservas/festivos/nuevo/`, `/reservas/festivos/<id>/editar/`, `/reservas/festivos/<id>/eliminar/`.
- **Funcionamiento:** función `reservas.servicios.es_festivo(fecha)` que usará la reserva en S2.
- **Criterios de aceptación → tests (`reservas/tests/test_hu09.py`):**
  - Una fecha registrada como festiva no se puede reservar → en S1 se prueba la función: `test_es_festivo_devuelve_true_para_fecha_registrada`. **El test de la reserva rechazada se agrega en S2 (HU08)**, porque la reserva aún no existe.
  - `test_fecha_festiva_duplicada_es_rechazada`.
- **Guion de demo:** `admin` agrega el festivo de una fecha cercana (por ejemplo, en 3 días). En S2 se mostrará que esa fecha no aparece al reservar.

**Fuera de este sprint:** catálogo, reservas, fiado (el campo `fiado_habilitado` **no** se crea todavía), ayuda (HU03).

---

## 9. Sprint 2 — "Los clientes reservan hora por Internet o en el local" (19 pts)

**Orden de construcción:** HU13 → HU12 → HU08 → HU10.
**Datos demo:** 10 productos (aceite 10W-40, filtro de aceite, filtro de aire, pastillas de freno, líquido de frenos, refrigerante, bujías, ampolleta, escobillas, batería) con código y unidad; 5 servicios activos con precio y productos asociados (cambio de aceite, cambio de pastillas, revisión de frenos, cambio de batería, mantención básica) y 1 servicio desactivado; 3 reservas vigentes de `cliente1` en los próximos días y 1 anulada.

### HU13 — Productos (3 pts) · RF17 · CU08
*Como Empleado Administrativo, quiero registrar los productos con código y unidad, para usarlos en servicios y pedidos.*

- **Modelo `catalogo.Producto`:** `codigo` (único), `descripcion`, `unidad` (choices: unidad, litro, kilo, metro, juego), `activo`.
- **URLs:** `/catalogo/productos/` (lista paginada con buscador), `/nuevo/`, `/<id>/editar/`, `/<id>/desactivar/`.
- **Criterios de aceptación → tests (`catalogo/tests/test_hu13.py`):**
  - No se aceptan dos productos con el mismo código → `test_codigo_duplicado_es_rechazado` (también con distinta mayúscula/minúscula: el código se guarda en mayúsculas).
  - `test_producto_desactivado_no_aparece_en_selecciones`.
- **Guion de demo:** crear un producto con un código que ya existe → error en el campo código.

### HU12 — Catálogo de servicios con productos (5 pts) · RF15, RF16 · CU07
*Como Empleado Administrativo, quiero mantener el catálogo de servicios con los productos que usa cada uno, para que los clientes reserven lo que el taller ofrece.*

- **Modelos:** `catalogo.Servicio` (con `ConVersion`): `nombre` (único), `descripcion`, `precio` (entero, pesos), `duracion_bloques` (default 1), `activo`. `catalogo.ServicioProducto`: `servicio`, `producto`, `cantidad` (decimal > 0); único por (servicio, producto).
  El precio no lo pide un RF de forma literal, pero es condición necesaria para calcular el total de la boleta (CU12, paso 4).
- **URLs:** `/catalogo/servicios/`, `/nuevo/`, `/<id>/` (detalle con sus productos), `/<id>/editar/` (formulario + formset de productos), `/<id>/desactivar/`.
- **Criterios de aceptación → tests (`catalogo/tests/test_hu12.py`):**
  - Un servicio desactivado no aparece al reservar → `test_servicio_desactivado_no_aparece_en_reserva` (el queryset `Servicio.objects.reservables()` lo usa HU08).
  - Cada servicio muestra sus productos → `test_detalle_servicio_lista_productos`.
- **Guion de demo:** ver "Cambio de aceite" con sus productos. Desactivar "Mantención básica" y, ya en HU08, mostrar que no aparece.

### HU08 — Reservar hora por Internet (8 pts) · RF10, RF11 · RNF18, RNF19 · CU04 ★
*Como Cliente, quiero reservar una hora por Internet, para no tener que llamar al taller.*

- **Modelo `reservas.Reserva`:** `numero` (id visible), `cliente` (FK), `servicio` (FK), `fecha`, `hora_inicio`, `estado` (choices: `VIGENTE`, `ANULADA`, `ATENDIDA`), `canal` (`WEB`, `LOCAL`), `creada_por` (FK Usuario), `creada_en`.
  **Restricción única condicional:** (`fecha`, `hora_inicio`) con `estado = VIGENTE` (1 reserva por bloque, 5.7). Así dos usuarios no pueden tomar la misma hora (flujo 5a).
- **Servicio de disponibilidad** `reservas.servicios.horas_disponibles(fecha)`: bloques del horario de 5.7, menos los ya reservados, y vacío si la fecha es festiva, no es día de atención o ya pasó.
- **Flujo del cliente: exactamente 3 pantallas** (RNF18), con el avance guardado en la sesión:
  1. `/reservas/nueva/` → tarjetas con los servicios reservables (nombre, precio, descripción).
  2. `/reservas/nueva/fecha/` → selector de fecha de los próximos 30 días (**los festivos no se ofrecen**) y botones con las horas libres de la fecha elegida.
  3. `/reservas/nueva/confirmar/` → resumen y botón "Confirmar". Al confirmar → mensaje "Reserva N° X registrada" y redirección a "Mis reservas".
- **Validación en el servidor (flujo 4a):** aunque se fuerce una fecha festiva en la URL o el formulario, se rechaza con *"Fecha no disponible: día festivo"*.
- **Hora tomada (flujo 5a):** si al confirmar la hora ya fue tomada (`IntegrityError`), mensaje *"La hora elegida acaba de ser reservada por otra persona. Elija otra."* y vuelve a la pantalla 2.
- **Canal local (RF10, Empleado Administrativo):** `/agenda/` muestra las reservas del día y de los próximos días; `/agenda/nueva/` es el mismo flujo con un paso previo para buscar al cliente por RUT. Queda con `canal = LOCAL`.
- Pantallas de reserva usables a 360 px (RNF19): probar con las herramientas de desarrollador del navegador.
- **Criterios de aceptación → tests (`reservas/tests/test_hu08.py`):**
  - Reserva en 3 pantallas o menos desde el celular → `test_flujo_reserva_completo_en_tres_pasos`.
  - Los festivos no aparecen disponibles → `test_festivo_no_aparece_disponible`, `test_reserva_en_festivo_forzada_es_rechazada` (cierra el criterio pendiente de HU09).
  - `test_hora_ocupada_no_se_ofrece`, `test_hora_tomada_al_confirmar_vuelve_a_elegir`, `test_servicio_desactivado_no_se_puede_reservar`, `test_empleado_reserva_en_local_para_un_cliente`.
- **Guion de demo:** desde un celular (o modo responsivo a 360 px), `cliente1` reserva "Cambio de aceite" en 3 pantallas. La fecha festiva cargada en S1 no aparece. Desde `/agenda/`, `administrativo` ve la reserva.

### HU10 — Cambiar o anular la reserva (3 pts) · RF13 · CU04
*Como Cliente, quiero cambiar o anular mi reserva, para ajustarla si no puedo asistir.*

- **URLs:** `/reservas/mis-reservas/` (vigentes y pasadas del cliente), `/reservas/<numero>/cambiar/` (reutiliza las pantallas 2 y 3 de HU08), `/reservas/<numero>/anular/` (confirmación). El Empleado Administrativo hace lo mismo desde `/agenda/`.
- **Reglas:** solo reservas `VIGENTE` con fecha futura. Un cliente solo ve y toca **sus** reservas (otro número → 404).
- **Criterios de aceptación → tests (`reservas/tests/test_hu10.py`):**
  - El cambio libera la hora anterior → `test_cambio_libera_hora_anterior`.
  - La anulación libera la hora → `test_anulacion_libera_hora`.
  - `test_cliente_no_ve_reservas_de_otro`, `test_no_se_cambia_reserva_pasada`.
- **Guion de demo:** `cliente1` cambia su reserva a otra hora; ingresar como `cliente2` y comprobar que la hora original quedó libre.

**Fuera de este sprint:** registro del servicio realizado (el estado `ATENDIDA` existe, pero ninguna pantalla lo asigna hasta S3), boletas.

---

## 10. Sprints 3 a 6

### Sprint 3 — "El taller registra los servicios realizados y los cobra" (20 pts)

**Orden de construcción:** HU11 → HU19 → HU20 → HU21.
**Datos demo:** 4 servicios realizados de `cliente1` (2 pendientes de documento, 1 con boleta emitida y 1 con boleta anulada con su motivo); 1 factura registrada para otro cliente; los correlativos `boleta` y `factura` iniciados.

#### HU11 — Registrar servicio realizado (5 pts) · RF14 · CU06 ★
*Como Mecánico, quiero registrar el servicio que realicé, para dejar constancia de mi trabajo y permitir el cobro.*

- **Modelo `reservas.ServicioRealizado`:** `cliente`, `servicio`, `reserva` (FK nula: el cliente puede llegar sin reserva), `fecha`, `empleado` (FK `Empleado` con `ejecuta_servicios`), `observacion`, `estado_documento` (`PENDIENTE`, `DOCUMENTADO`), `registrado_en`.
- **URLs:** `/atencion/` (reservas vigentes de hoy, con botón "Registrar servicio"), `/atencion/registrar/?reserva=<numero>` (precargado con cliente y servicio), `/atencion/registrar/` (sin reserva: buscar cliente por RUT y elegir servicio, flujo 1a), `/atencion/realizados/` (lista del día).
- **Reglas:** el empleado se toma del usuario conectado; si no tiene empleado con `ejecuta_servicios` → acceso denegado y log (C07). Al registrar con reserva, la reserva pasa a `ATENDIDA`. Si el cliente no existe (flujo 1b) → mensaje *"Cliente no registrado: derivar al Empleado Administrativo"* (no se crea la ficha desde aquí).
- **Criterios de aceptación → tests (`reservas/tests/test_hu11.py`):**
  - El servicio queda asociado al cliente, la fecha y el mecánico → `test_servicio_realizado_guarda_cliente_fecha_y_mecanico`.
  - `test_registro_desde_reserva_la_marca_atendida`, `test_registro_sin_reserva` (1a), `test_cliente_no_registrado_muestra_derivacion` (1b), `test_empleado_sin_funcion_no_registra_servicio`.
- **Guion de demo:** `mecanico` abre `/atencion/`, registra el servicio de la reserva de hoy de `cliente1`, y luego uno sin reserva.

#### HU19 — Generar boleta (5 pts) · RF26 · RNF08 · CU12 ★
*Como Empleado Administrativo, quiero generar la boleta de los servicios realizados, para cobrar al cliente.*

- **Modelos `ventas.Boleta` (con `ConVersion`):** `numero` (correlativo `boleta`), `cliente`, `fecha_emision`, `total`, `estado` (`EMITIDA`, `ANULADA`), `motivo_anulacion`, `anulada_por`, `anulada_en`, `emitida_por`, `observacion`. `ventas.LineaBoleta`: `boleta`, `servicio_realizado` (FK), `descripcion`, `monto`.
- **URLs:** `/ventas/boletas/` (lista con filtros por número, cliente y estado), `/ventas/boletas/nueva/` (paso 1: buscar cliente; paso 2: marcar los servicios pendientes, ver el total y confirmar), `/ventas/boletas/<numero>/` (vista **imprimible** con `@media print` y botón "Imprimir").
- **Reglas:** el monto de cada línea es el precio del servicio. Al emitir, en una transacción: número correlativo, líneas, total, servicios → `DOCUMENTADO`, log `CREAR`. Un servicio `DOCUMENTADO` no vuelve a aparecer como pendiente.
- La boleta es un documento interno: no tiene validez tributaria en la maqueta (V02). Mostrarlo en la boleta impresa.
- **Criterios de aceptación → tests (`ventas/tests/test_hu19.py`):**
  - La boleta toma los datos del servicio y del cliente → `test_boleta_toma_datos_de_servicio_y_cliente`.
  - …y el servicio queda marcado como documentado → `test_servicio_queda_documentado`.
  - `test_numero_boleta_correlativo`, `test_emision_queda_en_log`, `test_servicio_documentado_no_aparece_pendiente`.
- **Guion de demo:** `administrativo` emite una boleta a `cliente1` con los 2 servicios pendientes, la imprime, y muestra que ya no aparecen como pendientes.

#### HU20 — Modificar o anular boleta (5 pts) · RF27, RF28 · RNF08, RNF09 · CU12 ★
*Como Empleado Administrativo, quiero modificar o anular una boleta, para corregir errores sin perder el registro.*

- **URLs:** `/ventas/boletas/<numero>/modificar/`, `/ventas/boletas/<numero>/anular/`.
- **Modificar (RF27):** solo boletas `EMITIDA`. Se pueden cambiar la `observacion` y el `monto` de cada línea (el total se recalcula). El log guarda usuario, fecha y **valor anterior y nuevo de cada campo cambiado** en `detalle`. En la ficha de la boleta se ve su historial.
  Qué campos son modificables no lo define el caso (V02): la lista anterior es un valor de demostración (`# DEMO: pendiente V02`).
- **Anular (RF28):** motivo obligatorio. La boleta queda `ANULADA`, conserva todas sus líneas y montos, sus servicios vuelven a `PENDIENTE` (se pueden volver a boletear) y se registra `ANULAR` en el log. La boleta anulada se ve con un sello "ANULADA" y su motivo.
- **No eliminar (RNF09):** no existe URL ni botón de eliminar; `Boleta.delete()` lanza una excepción; en el Django Admin `has_delete_permission` devuelve `False`.
- **Criterios de aceptación → tests (`ventas/tests/test_hu20.py`):**
  - La anulada conserva el original y el motivo → `test_anulada_conserva_lineas_y_motivo`.
  - Ninguna boleta se puede eliminar → `test_boleta_no_se_puede_eliminar` (modelo y URL).
  - `test_modificacion_guarda_valor_anterior_en_log`, `test_anulacion_libera_servicios`, `test_anulacion_sin_motivo_es_rechazada`, `test_boleta_anulada_no_se_modifica`.
- **Guion de demo:** modificar el monto de una línea → ver el historial con el valor anterior. Anular con motivo "Error en el servicio" → la boleta sigue visible con el sello y los servicios vuelven a estar pendientes.

#### HU21 — Registrar factura (5 pts) · RF29 · RNF08 · CU13
*Como Empleado Administrativo, quiero registrar facturas de los servicios realizados, para atender a clientes que la solicitan.*

- **Modelos `ventas.Factura`:** `numero` (correlativo `factura`), `cliente`, `rut_facturacion`, `razon_social`, `giro`, `direccion_facturacion`, `fecha`, `neto`, `iva`, `total`, `registrada_por`. `ventas.LineaFactura`: `factura`, `servicio_realizado`, `descripcion`, `monto`.
- **URLs:** `/ventas/facturas/`, `/ventas/facturas/nueva/` (mismo flujo que la boleta: cliente → servicios pendientes → datos de facturación → confirmar), `/ventas/facturas/<numero>/` (imprimible).
- **Reglas:** los servicios facturados quedan `DOCUMENTADO` (un servicio va en boleta **o** en factura, no en ambas). Log `CREAR`. No hay anular ni eliminar factura: cómo se corrige una factura es la pregunta **V02**.
- **Criterios de aceptación → tests (`ventas/tests/test_hu21.py`):**
  - La factura queda asociada al servicio y al cliente → `test_factura_asociada_a_servicio_y_cliente`.
  - `test_servicio_facturado_no_aparece_para_boleta`, `test_registro_factura_queda_en_log`.
- **Guion de demo:** facturar un servicio pendiente de otro cliente e imprimir la factura.

**Fuera de este sprint:** venta fiada. La boleta se emite solo como venta pagada; la opción "fiado" se agrega en S5 (HU07).

---

### Sprint 4 — "El taller compra a proveedores y recepciona con control" (19 pts)

**Orden de construcción:** HU15 → HU16 → HU18.
**Datos demo:** 3 proveedores (lubricantes, frenos, baterías y eléctrico); 3 órdenes de `administrativo`: una sin recepción, una con recepción parcial y una recepcionada completa; correlativo `orden_pedido` iniciado.

#### HU15 — Proveedores (3 pts) · RF19 · CU09
*Como Empleado Administrativo, quiero registrar a los proveedores con su contacto y rubro, para emitirles órdenes de pedido.*

- **Modelo `abastecimiento.Proveedor`:** `rut` (único, validado), `razon_social`, `nombre_contacto`, `telefono`, `email`, `rubro`, `activo`.
- **URLs:** `/abastecimiento/proveedores/` (lista con buscador por RUT, razón social o rubro), `/nuevo/`, `/<id>/`, `/<id>/editar/`.
- **Criterios de aceptación → tests (`abastecimiento/tests/test_hu15.py`):**
  - El proveedor queda disponible al crear una orden → `test_proveedor_activo_aparece_en_orden`, `test_proveedor_inactivo_no_aparece`.
  - `test_rut_proveedor_duplicado_es_rechazado`.

#### HU16 — Generar orden de pedido (8 pts) · RF20, RF23 · RNF08 · CU10 ★
*Como Empleado Administrativo habilitado, quiero generar órdenes de pedido numeradas, para solicitar productos a un proveedor.*

- **Modelos `abastecimiento.OrdenPedido` (con `ConVersion`):** `numero` (correlativo `orden_pedido`, único), `proveedor`, `fecha`, `creada_por` (FK `Empleado`), `observacion`. Propiedad `tiene_recepciones`. `abastecimiento.LineaOrden`: `orden`, `producto`, `cantidad_solicitada`; único por (orden, producto); propiedad `cantidad_recibida` (suma de recepciones) y `cantidad_pendiente`.
- **URLs:** `/abastecimiento/ordenes/` (lista con número, proveedor, fecha y estado: sin recepción / parcial / completa), `/abastecimiento/ordenes/nueva/` (proveedor + formset de productos y cantidades), `/abastecimiento/ordenes/<numero>/` (detalle imprimible).
- **Reglas:** antes de mostrar el formulario se verifica `Empleado.solicita_productos` (flujo 2a): si no, acceso denegado + log `ACCESO_DENEGADO` (RNF06). El número se asigna **al confirmar**, con `correlativos.siguiente("orden_pedido")`. Log `CREAR`. Cantidades > 0 y productos activos.
- **Criterios de aceptación → tests (`abastecimiento/tests/test_hu16.py`):**
  - Cada orden recibe el siguiente correlativo → `test_ordenes_reciben_correlativo_ascendente`.
  - Un empleado no habilitado no puede generarla → `test_empleado_no_habilitado_no_genera_orden` (con `administrativo2`), `test_intento_no_habilitado_queda_en_log`.
  - `test_creacion_orden_queda_en_log`, `test_orden_sin_productos_es_rechazada`.
- **Guion de demo:** `administrativo` crea la orden N° X a "Lubricantes". Ingresar como `administrativo2` e intentar crear una orden → denegado; mostrarlo en `/auditoria/`.

#### HU18 — Recepcionar productos contra la orden (8 pts) · RF24, RF25 · CU11 ★
*Como Empleado Administrativo, quiero recepcionar productos contra la orden, para no aceptar lo que no se pidió.*

- **Modelos `abastecimiento.Recepcion`:** `orden`, `fecha`, `recibida_por`, `observacion`. `abastecimiento.LineaRecepcion`: `recepcion`, `producto`, `cantidad`.
- **URLs:** `/abastecimiento/recepciones/nueva/` (paso 1: ingresar el número de la orden), `/abastecimiento/ordenes/<numero>/recepcionar/` (paso 2: lista de productos de la orden con su cantidad pendiente; el empleado ingresa lo recibido), `/abastecimiento/recepciones/` (historial).
- **Reglas:**
  - Orden inexistente (1a) → *"La orden N° X no existe"*.
  - El formulario permite agregar un producto por código; si no está en la orden (4a) → se rechaza con *"Producto no solicitado en la orden N° X"* y **no se guarda nada** (RF25). Esta validación vive en el servidor, no solo en la pantalla.
  - Cantidad recibida distinta de la pendiente (4b) → la pantalla vuelve con la advertencia *"La cantidad recibida de <producto> (n) difiere de la pendiente (m). ¿Confirma la recepción?"* y un botón "Confirmar con diferencias".
  - Al guardar se actualizan las cantidades pendientes; desde ese momento la orden `tiene_recepciones` y no se puede modificar ni eliminar (lo usa HU17 en S5).
- **Criterios de aceptación → tests (`abastecimiento/tests/test_hu18.py`):**
  - Un producto que no está en la orden no se puede ingresar → `test_producto_no_solicitado_es_rechazado`, `test_rechazo_no_guarda_la_recepcion`.
  - Una diferencia de cantidad genera advertencia → `test_diferencia_de_cantidad_pide_confirmacion`, `test_confirmar_con_diferencias_guarda`.
  - `test_orden_inexistente_avisa`, `test_recepcion_actualiza_pendientes`.
- **Guion de demo:** recepcionar la orden creada en HU16 con una cantidad menor → advertencia y confirmación. Intentar agregar "Batería" a una orden de lubricantes → rechazo con el mensaje literal.

**Fuera de este sprint:** modificar y eliminar órdenes (HU17, S5).

---

### Sprint 5 — "El taller vende fiado con control, corrige órdenes y analiza su operación" (20 pts)

**Orden de construcción:** HU06 → HU07 → HU17 → HU22.
**Datos demo:** `cliente1` habilitado para fiado con 2 boletas fiadas, para que su saldo se vea; `cliente2` no habilitado; una orden sin recepciones lista para modificar y eliminar; suficientes reservas, servicios, boletas y órdenes en los últimos 60 días para que los informes muestren datos (generar con fechas relativas).

#### HU06 — Habilitar clientes para fiado (2 pts) · RF07 · CU14
*Como Administrador, quiero marcar a los clientes que pueden comprar fiado, para controlar a quién se le da crédito.*

- **Migración:** agregar `Cliente.fiado_habilitado` (bool, default `False`).
- **URLs:** `/clientes/fiado/` (lista de clientes con el interruptor "Habilitado para fiado", solo ADMIN). En la ficha del cliente se ve el estado; solo ADMIN lo cambia (módulo `fiado`).
- Monto máximo de fiado: pregunta abierta **V01**. La maqueta no pone tope.
- **Criterios de aceptación → tests (`clientes/tests/test_hu06.py`):**
  - Solo los clientes marcados aparecen con la opción de fiado → `test_solo_habilitados_tienen_opcion_fiado`.
  - `test_administrativo_no_puede_habilitar_fiado`.

#### HU07 — Venta fiada y saldo (5 pts) · RF08, RF09 · CU14 (extiende CU12)
*Como Empleado Administrativo, quiero registrar ventas fiadas y ver el saldo de cada cliente, para saber cuánto se le debe al taller.*

- **Cambios en la boleta (flujo 3a de CU12):** campo `Boleta.fiada` (bool). En `/ventas/boletas/nueva/` aparece la casilla "Venta fiada" **solo** si el cliente está habilitado.
- **Modelo `clientes.MovimientoFiado`:** `cliente`, `boleta`, `fecha`, `monto` (positivo = deuda; negativo = reverso por anulación), `descripcion`.
- **Reglas:** boleta fiada → movimiento positivo por el total. **Anular una boleta fiada** (HU20) → movimiento negativo por el mismo monto, para que el saldo no quede inflado. Modificar el monto de una boleta fiada → movimiento por la diferencia. Saldo = suma de movimientos. No hay registro de pagos (la cobranza está fuera del alcance).
- **Validación en el servidor:** si se envía `fiada=True` para un cliente no habilitado → *"El cliente no está habilitado para comprar fiado"* y no se emite la boleta.
- **URLs:** `/clientes/<id>/saldo/` (saldo y detalle de movimientos), `/clientes/fiado/` muestra además el saldo de cada habilitado.
- **Criterios de aceptación → tests (`clientes/tests/test_hu07.py`):**
  - La venta fiada suma al saldo → `test_boleta_fiada_suma_al_saldo`.
  - A un cliente no habilitado se le rechaza → `test_fiado_a_no_habilitado_es_rechazado`.
  - `test_anular_boleta_fiada_descuenta_saldo`, `test_modificar_boleta_fiada_ajusta_saldo`.
- **Guion de demo:** emitir una boleta fiada a `cliente1` → ver el saldo. Abrir una boleta para `cliente2` → la casilla no aparece. Anular la boleta fiada → el saldo baja.

#### HU17 — Modificar o eliminar orden sin recepciones (5 pts) · RF21, RF22 · RNF08 · CU10
*Como Empleado Administrativo, quiero modificar o eliminar una orden sin recepciones, para corregir errores antes del despacho.*

- **URLs:** `/abastecimiento/ordenes/<numero>/modificar/`, `/abastecimiento/ordenes/<numero>/eliminar/` (confirmación).
- **Reglas:** si `tiene_recepciones` → botones ocultos y, si se fuerza la URL, *"No se puede modificar ni eliminar una orden con recepciones registradas"*. Modificar: cambiar productos y cantidades, con log `MODIFICAR` y valores anteriores. Eliminar: borra la orden y sus líneas, log `ELIMINAR` con el número y su contenido; **el correlativo no retrocede** (5.5). Las mismas restricciones de habilitación de HU16 (RF23).
- **Criterios de aceptación → tests (`abastecimiento/tests/test_hu17.py`):**
  - Con recepciones no se puede modificar ni eliminar → `test_orden_con_recepcion_no_se_modifica`, `test_orden_con_recepcion_no_se_elimina`.
  - El número eliminado no se reutiliza → `test_numero_eliminado_no_se_reutiliza` (eliminar la última orden y crear otra: recibe el número siguiente, no el eliminado).
  - `test_modificacion_y_eliminacion_quedan_en_log`.
- **Guion de demo:** eliminar la orden N° 5 (la última) y crear una nueva → recibe la N° 6. Intentar modificar una orden recepcionada → mensaje de bloqueo.

#### HU22 — Informes con filtros, vista previa e impresión (8 pts) · RF30, RF31 · RNF03 · CU15
*Como Administrador, quiero generar informes con filtros, verlos en pantalla e imprimirlos, para decidir con información.*

- **URL:** `/informes/` con selector de tipo y filtros; `/informes/<tipo>/?desde=&hasta=&cliente=&servicio=&empleado=&proveedor=`.
- **Tipos de informe (RF30)** y filtros que aplican a cada uno:

| Tipo | Columnas | Filtros |
|---|---|---|
| Servicios realizados | fecha, cliente, servicio, mecánico, estado de documento | fecha, cliente, servicio, empleado |
| Ventas | número, tipo (boleta/factura), fecha, cliente, total, estado, fiada | fecha, cliente, servicio, empleado |
| Reservas | número, fecha y hora, cliente, servicio, canal, estado | fecha, cliente, servicio |
| Abastecimiento | orden, fecha, proveedor, producto, solicitado, recibido, pendiente | fecha, proveedor, empleado |

- **Vista previa e impresión (RF31):** la tabla se ve en pantalla con totales al pie; botón "Imprimir" que abre una versión limpia (`@media print`, sin menú) y llama a `window.print()`.
- **Tamaño (RNF03):** si el rango supera 1 mes o el resultado supera 1.000 filas, la pantalla muestra un indicador de carga mientras se genera y el aviso *"Informe grande: el tiempo de respuesta no está comprometido"*. No se pagina el informe impreso.
- **Criterios de aceptación → tests (`informes/tests/test_hu22.py`):**
  - Filtra por fecha, cliente, servicio, empleado y proveedor → un test por filtro: `test_filtro_fecha`, `test_filtro_cliente`, `test_filtro_servicio`, `test_filtro_empleado`, `test_filtro_proveedor`.
  - Previsualiza e imprime → `test_vista_impresion_sin_menu`.
  - Un informe de hasta 1 mes y 1.000 filas se genera en menos de 5 s → `test_informe_pequeno_menos_de_5_segundos` (con 1.000 filas de prueba, medido con `time.perf_counter`; vale como evidencia en local, no como medición del VPS).
  - `test_informe_grande_muestra_aviso`.
- **Guion de demo:** informe de ventas del último mes filtrado por `cliente1` → vista previa → imprimir a PDF desde el navegador.

**Fuera de este sprint:** exportación (HU23), estadísticas web (HU24), ayuda (HU03).

---

### Sprint 6 — "El taller mide su canal web, exporta informes y cuenta con ayuda en línea" (11 pts + holgura)

**Orden de construcción:** HU23 → HU24 → HU03 → **holgura** (9 pts libres: ajustes pedidos en las Sprint Reviews y preparación de la presentación final).
**Datos demo:** visitas web de los últimos 90 días generadas con fechas relativas (más visitas los lunes, para que el gráfico muestre variación); una sección de ayuda por módulo.

#### HU23 — Exportar informes (3 pts) · RF32 · CU15
*Como Administrador, quiero exportar los informes a texto, Excel y Word, para trabajarlos fuera del sistema.*

- **URL:** misma ruta del informe con `&formato=txt|xlsx|docx`; tres botones en la vista previa.
- **Implementación:** una sola función que arma las filas del informe (la misma que usa la vista previa) y tres exportadores: texto separado por tabulaciones (UTF-8), Excel con `openpyxl` (encabezados en negrita, anchos ajustados), Word con `python-docx` (título, filtros aplicados y tabla). Nombre del archivo: `informe-<tipo>-<desde>-<hasta>.<ext>`.
- Ninguna exportación incluye contraseñas ni datos de cuentas (RNF05).
- **Criterios de aceptación → tests (`informes/tests/test_hu23.py`):**
  - El archivo exportado contiene los mismos datos del informe en pantalla → `test_exportacion_txt_mismas_filas`, `test_exportacion_xlsx_mismas_filas` (leer el archivo con `openpyxl` y comparar), `test_exportacion_docx_mismas_filas`.

#### HU24 — Estadísticas de visitas web (5 pts) · RF33 · CU16
*Como Administrador, quiero ver las estadísticas de visitas al sitio web, para medir el canal web.*

- **Modelo `informes.VisitaWeb`:** `fecha_hora`, `ruta`, `clave_sesion`, `usuario` (nulo).
- **Registro:** middleware `informes.middleware.RegistroVisitasMiddleware` que guarda las peticiones GET exitosas a las páginas públicas y de reserva (`/`, `/reservas/...`, `/cuentas/ingresar/`). No registra archivos estáticos ni pantallas internas. Una visita = una sesión por ruta por día (evita contar recargas).
- **URL:** `/informes/estadisticas-web/` con tres pestañas: por día (últimos 30 días), por semana (últimas 12) y por mes (últimos 12), con tabla y gráfico de barras (Chart.js 4.4.1 desde CDN).
- **Criterios de aceptación → tests (`informes/tests/test_hu24.py`):**
  - Muestra visitas por día, semana y mes → `test_visitas_por_dia`, `test_visitas_por_semana`, `test_visitas_por_mes`.
  - `test_middleware_registra_visita_publica`, `test_middleware_no_cuenta_recargas`, `test_estadisticas_solo_admin`.

#### HU03 — Ayuda en línea contextual (3 pts) · RF04
*Como usuario, quiero abrir la ayuda del módulo en que estoy, para resolver dudas sin salir de la pantalla.*

- **Modelo `core.SeccionAyuda`:** `modulo` (los mismos nombres de 5.2), `titulo`, `contenido` (texto con formato simple).
- **Funcionamiento:** un procesador de contexto obtiene el módulo de la vista actual (atributo `modulo` de la vista o el `app_name` de la URL). El botón "?" de `base.html` abre un panel lateral (offcanvas de Bootstrap) con la sección de ese módulo, **sin salir de la pantalla**. `/ayuda/` muestra el manual completo.
- **Contenido mínimo:** una sección por módulo de 5.2, con los pasos del flujo principal (pueden salir de los flujos básicos de los CU del informe).
- **Criterios de aceptación → tests (`core/tests/test_hu03.py`):**
  - El botón de ayuda abre la sección del manual del módulo en uso → `test_ayuda_muestra_seccion_del_modulo_actual` (probar en clientes, reservas y ventas).
  - `test_modulo_sin_seccion_muestra_manual_general`.

#### Cierre del S6 (holgura)
1. Recorrer el **guion de demostración completo** (sección 13) en el VPS con los 6 usuarios.
2. Correr `python manage.py test` y guardar la salida como evidencia (`docs/evidencia-tests.txt`).
3. Revisar en 360 px todas las pantallas del cliente (RNF19).
4. Completar la sección 14 y la tabla de trazabilidad de la sección 15.

---

## 11. Cierre de cada sprint (puerta para pasar al siguiente)

No se empieza el sprint siguiente hasta marcar todo:

- [ ] Todas las HU del sprint cumplen la Definition of Done (sección 3).
- [ ] `python manage.py test` → todo en verde, **incluidas las HU de sprints anteriores**.
- [ ] Base limpia: `python manage.py cargar_demo --reset` corre sin errores y deja la demo lista.
- [ ] `python manage.py makemigrations --check` → no hay migraciones pendientes.
- [ ] Desplegado en el VPS (sección 12) y `python manage.py check --deploy` sin advertencias críticas.
- [ ] Guion de demo del sprint ejecutado en el VPS (Sprint Review).
- [ ] Sección 14 actualizada: HU marcadas, fecha, y observaciones de la review.
- [ ] Si la review pide cambios: se anotan como HU nuevas o ajustes en la sección 14, **no** se aplican a escondidas en el sprint siguiente.

---

## 12. Despliegue en el VPS (prueba)

1. Subdominio propio para la maqueta (por ejemplo `serviexpress.<dominio>`), separado de los otros proyectos del VPS.
2. Usuario de sistema y carpeta propios; entorno virtual; `pip install -r requirements.txt`.
3. Archivo `.env` (fuera del repositorio) con `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS=https://...`, `DJANGO_DEMO=1`.
4. Settings de producción: `SECURE_SSL_REDIRECT = True`, `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`, `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`, `STATIC_ROOT`.
5. `migrate`, `collectstatic`, `cargar_demo`.
6. `gunicorn` como servicio de systemd (socket o puerto local) y `nginx` como proxy que sirve `/static/`.
7. HTTPS con `certbot --nginx` (RNF12).
8. Respaldo simple: cron diario que copia `db.sqlite3` con la fecha, conservando 7 días (demostración de RNF16, sin la retención de 30 días).
9. Script `deploy.sh`: `git pull` → `pip install` → `migrate` → `collectstatic` → reiniciar el servicio.

---

## 13. Guion de demostración completo (presentación final)

Sigue el ciclo del negocio, de punta a punta, en este orden:

1. **Acceso (S1):** ingresar como `admin` → crear cuenta → mostrar acceso denegado y el log. Bloqueo tras 5 intentos.
2. **Personal y clientes (S1):** empleado sin función → error. Registrar cliente → el cliente ingresa.
3. **Catálogo (S2):** productos y servicios con sus productos.
4. **Reserva web (S2):** en el celular, `cliente1` reserva en 3 pantallas; el festivo no aparece; cambia la reserva.
5. **Atención (S3):** `mecanico` registra el servicio de la reserva.
6. **Venta (S3 + S5):** `administrativo` emite boleta (pagada) e imprime; modifica y anula con motivo; emite una boleta fiada a `cliente1` y muestra el saldo; `cliente2` no tiene la opción.
7. **Abastecimiento (S4 + S5):** `administrativo2` no puede crear la orden; `administrativo` sí; recepción con diferencia y rechazo de producto no solicitado; eliminar una orden y mostrar que el número no se reutiliza.
8. **Gestión (S5 + S6):** informe filtrado, impresión, exportación a Excel; estadísticas web; botón de ayuda.
9. **Cierre:** `/auditoria/` muestra el rastro de todo lo anterior (boletas, órdenes, accesos denegados).

---

## 14. Registro de avance

Marcar `[x]` solo cuando la HU cumple la Definition of Done. Anotar la fecha y el resultado de la review.

| Sprint | HU | Nombre | Pts | Hecha | Fecha | Observaciones de la review |
|---|---|---|---:|:-:|---|---|
| S0 | — | Preparación del proyecto | — | [ ] | | |
| S1 | HU01 | Iniciar sesión | 3 | [ ] | | |
| S1 | HU02 | Cuentas y perfiles | 5 | [ ] | | |
| S1 | HU14 | Empleados y función | 3 | [ ] | | |
| S1 | HU04 | Registrar ficha de cliente | 3 | [ ] | | |
| S1 | HU05 | Modificar y consultar ficha | 2 | [ ] | | |
| S1 | HU09 | Días festivos | 2 | [ ] | | |
| S2 | HU13 | Productos | 3 | [ ] | | |
| S2 | HU12 | Catálogo de servicios | 5 | [ ] | | |
| S2 | HU08 | Reservar hora por Internet | 8 | [ ] | | |
| S2 | HU10 | Cambiar o anular reserva | 3 | [ ] | | |
| S3 | HU11 | Registrar servicio realizado | 5 | [ ] | | |
| S3 | HU19 | Generar boleta | 5 | [ ] | | |
| S3 | HU20 | Modificar o anular boleta | 5 | [ ] | | |
| S3 | HU21 | Registrar factura | 5 | [ ] | | |
| S4 | HU15 | Proveedores | 3 | [ ] | | |
| S4 | HU16 | Generar orden de pedido | 8 | [ ] | | |
| S4 | HU18 | Recepcionar contra la orden | 8 | [ ] | | |
| S5 | HU06 | Habilitar fiado | 2 | [ ] | | |
| S5 | HU07 | Venta fiada y saldo | 5 | [ ] | | |
| S5 | HU17 | Modificar o eliminar orden | 5 | [ ] | | |
| S5 | HU22 | Informes con filtros | 8 | [ ] | | |
| S6 | HU23 | Exportar informes | 3 | [ ] | | |
| S6 | HU24 | Estadísticas web | 5 | [ ] | | |
| S6 | HU03 | Ayuda en línea | 3 | [ ] | | |
| — | HU25 | Multiempresa / multimoneda | 13 | Fuera de la 1ª versión | | |
| | | **Total 1ª versión** | **107** | | | |

---

## 15. Trazabilidad maqueta ↔ informe

| HU | RF | CU | App | URL principal | Archivo de tests |
|---|---|---|---|---|---|
| HU01 | RF01 | CU01 | cuentas | `/cuentas/ingresar/` | `cuentas/tests/test_hu01.py` |
| HU02 | RF02, RF03 | CU02 | cuentas | `/cuentas/usuarios/` | `cuentas/tests/test_hu02.py` |
| HU03 | RF04 | — | core | botón "?" / `/ayuda/` | `core/tests/test_hu03.py` |
| HU04 | RF05 | CU03 | clientes | `/clientes/nuevo/` | `clientes/tests/test_hu04.py` |
| HU05 | RF06 | CU03 | clientes | `/clientes/` | `clientes/tests/test_hu05.py` |
| HU06 | RF07 | CU14 | clientes | `/clientes/fiado/` | `clientes/tests/test_hu06.py` |
| HU07 | RF08, RF09 | CU14 | clientes + ventas | `/clientes/<id>/saldo/` | `clientes/tests/test_hu07.py` |
| HU08 | RF10, RF11 | CU04 | reservas | `/reservas/nueva/` | `reservas/tests/test_hu08.py` |
| HU09 | RF12 | CU05 | reservas | `/reservas/festivos/` | `reservas/tests/test_hu09.py` |
| HU10 | RF13 | CU04 | reservas | `/reservas/mis-reservas/` | `reservas/tests/test_hu10.py` |
| HU11 | RF14 | CU06 | reservas | `/atencion/` | `reservas/tests/test_hu11.py` |
| HU12 | RF15, RF16 | CU07 | catalogo | `/catalogo/servicios/` | `catalogo/tests/test_hu12.py` |
| HU13 | RF17 | CU08 | catalogo | `/catalogo/productos/` | `catalogo/tests/test_hu13.py` |
| HU14 | RF18 | CU17 | personal | `/personal/empleados/` | `personal/tests/test_hu14.py` |
| HU15 | RF19 | CU09 | abastecimiento | `/abastecimiento/proveedores/` | `abastecimiento/tests/test_hu15.py` |
| HU16 | RF20, RF23 | CU10 | abastecimiento | `/abastecimiento/ordenes/nueva/` | `abastecimiento/tests/test_hu16.py` |
| HU17 | RF21, RF22 | CU10 | abastecimiento | `/abastecimiento/ordenes/<n>/modificar/` | `abastecimiento/tests/test_hu17.py` |
| HU18 | RF24, RF25 | CU11 | abastecimiento | `/abastecimiento/recepciones/nueva/` | `abastecimiento/tests/test_hu18.py` |
| HU19 | RF26 | CU12 | ventas | `/ventas/boletas/nueva/` | `ventas/tests/test_hu19.py` |
| HU20 | RF27, RF28 | CU12 | ventas | `/ventas/boletas/<n>/anular/` | `ventas/tests/test_hu20.py` |
| HU21 | RF29 | CU13 | ventas | `/ventas/facturas/nueva/` | `ventas/tests/test_hu21.py` |
| HU22 | RF30, RF31 | CU15 | informes | `/informes/` | `informes/tests/test_hu22.py` |
| HU23 | RF32 | CU15 | informes | `/informes/<tipo>/?formato=xlsx` | `informes/tests/test_hu23.py` |
| HU24 | RF33 | CU16 | informes | `/informes/estadisticas-web/` | `informes/tests/test_hu24.py` |

---

## 16. Instrucciones para el asistente de IA (copiar como prompt)

**Al empezar un sprint:**

> Lee `MAQUETA-SPEC.md` completo. Vamos a trabajar **solo el Sprint N**. Respeta las reglas de la sección 0, la base común de la sección 5 y la Definition of Done de la sección 3.
> Implementa las historias del Sprint N **en el orden indicado**, una a la vez. Para cada historia: (1) modelo y migración, (2) formularios con validaciones en español, (3) vistas con `@requiere_modulo` y las restricciones de función que indique la ficha, (4) plantillas que extienden `base.html` con el chip de trazabilidad, (5) URLs y enlace en el menú del perfil, (6) los tests con los nombres exactos de la ficha, (7) los datos de `cargar_demo`.
> No crees modelos, campos, pantallas ni botones de sprints futuros. Si algo de la ficha es ambiguo o choca con lo ya construido, **detente y pregúntame** en vez de suponer.
> Al terminar cada historia, corre `python manage.py test` y muéstrame el resultado antes de seguir con la siguiente.

**Al terminar una historia:**

> Verifica la HUxx contra su ficha en `MAQUETA-SPEC.md`: lista cada criterio de aceptación con el test que lo cubre y su resultado, confirma que el chip de trazabilidad, el permiso y los datos demo están, y dime qué falta. No marques nada en la sección 14: eso lo hace el equipo.

**Al cerrar el sprint:**

> Recorre el checklist de la sección 11 para el Sprint N y dime cuáles puntos están cumplidos y cuáles no, con la evidencia (salida de los comandos).
