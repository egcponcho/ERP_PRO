import { createRouter, createWebHistory } from 'vue-router'
import { tituloPagina } from '@/nucleo/migas.js'

// Cada módulo es una sola entrada del menú; adentro tiene su tablero y sus apartados.
// meta.migas: ancestros para las migas de pan; meta.seccion: pestaña activa del módulo.
// meta.modulo: entrada del menú lateral que queda activa (ver MODULOS en App.vue).
const routes = [
  { path: '/', name: 'inicio', component: () => import('@/modulos/inicio/InicioView.vue'), meta: { titulo: 'Inicio' } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  // Volver atrás devuelve a donde estaba; cambiar solo los filtros o la pestaña (query) no mueve la página
  scrollBehavior: (to, from, guardada) => guardada || (to.path === from.path ? false : { top: 0 }),
})
router.afterEach((to, from) => {
  if (to.path !== from.path) tituloPagina.value = ''
  document.title = `${to.meta.titulo || 'ERP PRO'} · ERP PRO`
})
export default router
