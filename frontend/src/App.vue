<script setup>
// Marco de la aplicación: menú lateral con una entrada por módulo (cada módulo
// lleva adentro su tablero y sus apartados, así el menú no crece de más),
// barra superior con las migas de pan y el contenido.
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import Avisos from '@/componentes/Avisos.vue'
import Icono from '@/componentes/Icono.vue'
import { tituloPagina } from '@/nucleo/migas.js'
import { fijarTema, tema } from '@/nucleo/tema.js'

const route = useRoute()
const abierta = ref(false)
const principal = ref(null)

// Al cambiar de página: se cierra el menú del celular y el foco pasa al contenido (lectores de pantalla)
watch(() => route.path, async (a, de) => {
  abierta.value = false
  if (de === undefined) return
  await nextTick()
  principal.value?.focus({ preventScroll: true })
})

// Una entrada por módulo: { a: '/ruta', nombre, icono, modulo } (modulo = meta.modulo de sus rutas)
const MODULOS = []
const TEMAS = [{ v: 'light', i: 'sol', n: 'Claro' }, { v: 'dark', i: 'luna', n: 'Oscuro' }, { v: 'sistema', i: 'monitor', n: 'Según el sistema' }]
const activo = (m) => route.meta.modulo === m.modulo

const migas = computed(() => [...(route.meta.migas || []), { texto: tituloPagina.value || route.meta.titulo || '' }])
</script>

<template>
  <a class="saltar" href="#principal">Ir al contenido</a>
  <div class="marco">
    <aside class="lateral" :class="{ abierta }" aria-label="Menú principal">
      <div class="lateral-cabeza">
        <RouterLink to="/" class="marca">
          <span class="marca-logo"><Icono nombre="cuadricula" :tam="18" /></span>
          <span class="marca-texto">ERP PRO<span>Gestión empresarial</span></span>
        </RouterLink>
        <button type="button" class="btn-icono lateral-cerrar" aria-label="Cerrar menú" @click="abierta = false"><Icono nombre="cerrar" :tam="18" /></button>
      </div>
      <nav class="lateral-nav" aria-label="Módulos">
        <RouterLink to="/" class="lateral-item" :class="{ activo: route.name === 'inicio' }" :aria-current="route.name === 'inicio' ? 'page' : undefined">
          <Icono nombre="inicio" /><span class="lateral-texto">Inicio</span></RouterLink>
        <p v-if="MODULOS.length" class="lateral-grupo">Módulos</p>
        <RouterLink v-for="m in MODULOS" :key="m.a" :to="m.a" class="lateral-item" :class="{ activo: activo(m) }" :aria-current="activo(m) ? 'location' : undefined">
          <Icono :nombre="m.icono" /><span class="lateral-texto">{{ m.nombre }}</span></RouterLink>
      </nav>
      <div class="lateral-pie">
        <div class="tema" role="group" aria-label="Tema de colores">
          <button v-for="x in TEMAS" :key="x.v" type="button" :aria-pressed="tema === x.v" :title="x.n" :aria-label="`Tema ${x.n.toLowerCase()}`" @click="fijarTema(x.v)">
            <Icono :nombre="x.i" :tam="16" /></button>
        </div>
      </div>
    </aside>
    <div v-if="abierta" class="lateral-velo" @click="abierta = false" />
    <div class="area">
      <header class="cabecera">
        <button type="button" class="btn btn-fantasma btn-cuadrado boton-menu" aria-label="Abrir menú" :aria-expanded="abierta" @click="abierta = true"><Icono nombre="menu" :tam="20" /></button>
        <nav class="migas" aria-label="Ubicación">
          <ol>
            <li v-for="(m, i) in migas" :key="i">
              <RouterLink v-if="m.a && i < migas.length - 1" :to="m.a"><Icono v-if="i === 0 && route.meta.modulo" :nombre="MODULOS.find((x) => x.modulo === route.meta.modulo)?.icono || 'caja'" :tam="15" />{{ m.texto }}</RouterLink>
              <span v-else aria-current="page">{{ m.texto }}</span>
            </li>
          </ol>
        </nav>
      </header>
      <main id="principal" ref="principal" class="contenido" tabindex="-1">
        <RouterView />
      </main>
    </div>
  </div>
  <Avisos />
</template>

<style scoped>
.saltar { position: absolute; inset-inline-start: -9999px; top: 8px; z-index: 100; background: var(--acento); color: var(--sobre-acento); padding: 8px 12px; border-radius: 6px; }
.saltar:focus { inset-inline-start: 8px; }
main:focus { outline: none; }
</style>
