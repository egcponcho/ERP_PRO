import { ref } from 'vue'

// 'sistema' | 'light' | 'dark'
export const tema = ref(leer())

function leer() {
  try { return localStorage.getItem('erp.tema') || 'sistema' } catch { return 'sistema' }
}

export function fijarTema(valor) {
  tema.value = valor
  const raiz = document.documentElement
  if (valor === 'sistema') delete raiz.dataset.theme
  else raiz.dataset.theme = valor
  try {
    if (valor === 'sistema') localStorage.removeItem('erp.tema')
    else localStorage.setItem('erp.tema', valor)
  } catch { /* sin almacenamiento: el tema dura la sesión */ }
}
