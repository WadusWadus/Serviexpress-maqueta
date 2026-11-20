"""HU23 · Exportar informes a texto, Excel y Word · RF32 · CU15.

Los tres exportadores usan las mismas filas que la vista previa (consultas.generar).
Ninguna exportación incluye contraseñas ni datos de cuentas (RNF05).
"""

import io

from django.http import HttpResponse
from docx import Document
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from .consultas import formatear

TIPOS_MIME = {
    "txt": "text/plain; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def nombre_archivo(informe, extension):
    return f"informe-{informe.tipo}-{informe.desde:%Y-%m-%d}-{informe.hasta:%Y-%m-%d}.{extension}"


def _texto(informe):
    """Texto separado por tabulaciones, UTF-8."""
    lineas = ["\t".join(nombre for nombre, _ in informe.columnas)]
    for fila in informe.filas:
        lineas.append("\t".join(formatear(v, f).replace("\t", " ") for v, (_, f) in zip(fila, informe.columnas)))
    return ("\n".join(lineas) + "\n").encode("utf-8")


def _excel(informe):
    libro = Workbook()
    hoja = libro.active
    hoja.title = informe.titulo[:31]
    hoja.append([nombre for nombre, _ in informe.columnas])
    for celda in hoja[1]:
        celda.font = Font(bold=True)
    for fila in informe.filas:
        hoja.append([float(v) if f == "cantidad" else v for v, (_, f) in zip(fila, informe.columnas)])
    for i, (nombre, formato) in enumerate(informe.columnas, start=1):
        letra = get_column_letter(i)
        if formato == "fecha":
            for (celda,) in hoja.iter_rows(min_row=2, min_col=i, max_col=i):
                celda.number_format = "DD-MM-YYYY"
        elif formato == "pesos":
            for (celda,) in hoja.iter_rows(min_row=2, min_col=i, max_col=i):
                celda.number_format = '"$"#,##0'
        ancho = max([len(nombre)] + [len(formatear(f[i - 1], formato)) for f in informe.filas[:500]])
        hoja.column_dimensions[letra].width = min(ancho + 2, 50)
    totales = libro.create_sheet("Totales")
    totales.append(["Filtro / total", "Valor"])
    for celda in totales[1]:
        celda.font = Font(bold=True)
    for etiqueta, valor in informe.filtros_aplicados:
        totales.append([etiqueta, valor])
    for etiqueta, valor, formato in informe.totales:
        totales.append([etiqueta, formatear(valor, formato)])
    totales.column_dimensions["A"].width = 32
    totales.column_dimensions["B"].width = 24
    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()


def _word(informe):
    documento = Document()
    documento.add_heading(f"Informe de {informe.titulo.lower()} · SERVIEXPRESS", level=1)
    documento.add_paragraph(" · ".join(f"{e}: {v}" for e, v in informe.filtros_aplicados))
    tabla = documento.add_table(rows=1, cols=len(informe.columnas))
    tabla.style = "Table Grid"
    for celda, (nombre, _) in zip(tabla.rows[0].cells, informe.columnas):
        celda.text = nombre
        for parrafo in celda.paragraphs:
            for trozo in parrafo.runs:
                trozo.bold = True
    for fila in informe.filas:
        celdas = tabla.add_row().cells
        for celda, valor, (_, formato) in zip(celdas, fila, informe.columnas):
            celda.text = formatear(valor, formato)
    documento.add_paragraph("")
    for etiqueta, valor, formato in informe.totales:
        documento.add_paragraph(f"{etiqueta}: {formatear(valor, formato)}")
    salida = io.BytesIO()
    documento.save(salida)
    return salida.getvalue()


EXPORTADORES = {"txt": _texto, "xlsx": _excel, "docx": _word}


def exportar(informe, formato):
    respuesta = HttpResponse(EXPORTADORES[formato](informe), content_type=TIPOS_MIME[formato])
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre_archivo(informe, formato)}"'
    return respuesta
