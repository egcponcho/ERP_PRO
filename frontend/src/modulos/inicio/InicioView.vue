<script setup>
// Inicio general: una tarjeta por módulo con sus cifras clave y a dónde ir.
// Mientras no haya módulos muestra el estado de la instalación.
import { onMounted, ref } from 'vue'
import { api } from '@/nucleo/api.js'
import EstadoVacio from '@/componentes/EstadoVacio.vue'

const salud = ref(null)

onMounted(async () => {
  try { salud.value = await api.get('/salud') } catch { salud.value = { estado: 'sin conexión' } }
})
</script>

<template>
  <div>
    <header class="pagina-cabeza">
      <div><h1>Inicio</h1><p>Sus módulos y lo último que se movió. Cada módulo tiene su propio resumen.</p></div>
    </header>

    <section class="panel">
      <EstadoVacio icono="caja" titulo="Todavía no hay módulos"
                   :texto="`El núcleo está listo (API: ${salud?.estado ?? '…'}). El primer módulo aparecerá aquí y en el menú lateral.`" />
    </section>
  </div>
</template>
