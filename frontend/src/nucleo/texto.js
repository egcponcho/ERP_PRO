// Textos de los componentes traídos de facturacion: allá se escriben en inglés y
// se traducen; aquí van directo en español. t('Filter by {0}', ['Tipo']) → «Filtrar por Tipo».
const ES = {
  Compact: 'Compacta', Normal: 'Normal', Comfortable: 'Amplia', '(Empty)': '(Vacío)', Yes: 'Sí', No: 'No', '(+{0})': '(+{0})',
  'Fewer filters': 'Menos filtros', 'More filters': 'Más filtros', Density: 'Densidad', Columns: 'Columnas',
  'Show, hide and order the columns. Drag the edge of a header to make it wider.': 'Muestre, oculte y ordene las columnas. Arrastre el borde de un encabezado para ensancharlo.',
  'Move {0} up': 'Subir {0}', 'Move {0} down': 'Bajar {0}', 'Back to the initial view': 'Volver a la vista inicial',
  'Remove {0}': 'Quitar {0}', 'Clear filters': 'Limpiar filtros', 'Select all on this page': 'Elegir todas las de esta página',
  Detail: 'Detalle', 'Filter by {0}': 'Filtrar por {0}', 'Width of {0}': 'Ancho de {0}', Actions: 'Acciones', 'Select row': 'Elegir fila',
  'Show detail': 'Ver detalle', 'No records match these filters.': 'Ningún registro coincide con estos filtros.', 'No records yet.': 'Todavía no hay registros.',
  'Search values…': 'Buscar valores…', 'Search values': 'Buscar valores', Values: 'Valores', '(Select all results)': '(Elegir todos los resultados)',
  '(Select all)': '(Elegir todos)', 'No values match.': 'Ningún valor coincide.', 'Showing the first {0}; type to find the rest.': 'Se muestran los primeros {0}; escriba para encontrar el resto.',
  '{0} more selected outside this search.': '{0} elegidos más fuera de esta búsqueda.', Clear: 'Quitar', Apply: 'Aplicar',
  '{0}–{1} of {2} records': '{0}–{1} de {2} registros', Pages: 'Páginas', 'Previous page': 'Página anterior', 'Next page': 'Página siguiente',
  'Rows per page': 'Filas por página', 'Saved views': 'Vistas guardadas',
  'Save the filters you use often to come back to them in one click.': 'Guarde los filtros que usa seguido para volver a ellos con un clic.',
  'Delete view {0}': 'Borrar la vista {0}', 'Save current filters as a view': 'Guardar los filtros actuales como vista',
  'View “{0}” saved.': 'Vista «{0}» guardada.', 'View “{0}” deleted.': 'Vista «{0}» borrada.', 'Name of the view': 'Nombre de la vista',
  'Step {0} of {1}': 'Paso {0} de {1}', 'Close the assistant': 'Salir del asistente (el borrador queda guardado)', Exit: 'Salir', Progress: 'Avance', Steps: 'Pasos',
  '(needs attention)': '(necesita atención)', Back: 'Atrás', 'Save draft': 'Guardar borrador', Next: 'Siguiente', Finish: 'Terminar',
  Save: 'Guardar', Cancel: 'Cancelar', 'Clear selection': 'Quitar selección', 'Actions on the selection': 'Acciones sobre la selección',
}

export function t(texto, args) {
  if (texto === null || texto === undefined) return texto
  const base = ES[texto] ?? String(texto)
  return args ? base.replace(/\{(\d+)\}/g, (_, i) => args[i] ?? '') : base
}

// Los textos de datos ya vienen en español
export const tx = (texto) => texto
