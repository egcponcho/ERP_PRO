// Migas de pan: las rutas dicen sus ancestros (meta.migas) y su título (meta.titulo);
// una página cuyo título sale de sus datos (un producto, un tipo) lo fija aquí.
import { ref } from 'vue'

export const tituloPagina = ref('')

export function fijarTitulo(texto) {
  tituloPagina.value = texto || ''
  if (texto) document.title = `${texto} · ERP PRO`
}
