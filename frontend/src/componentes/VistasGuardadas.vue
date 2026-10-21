<script setup>
import { t, tx } from '@/nucleo/texto.js'
import { computed, onBeforeUnmount, ref } from 'vue'
import { avisar } from '@/nucleo/avisos.js'
import { guardarVistas, preferencias } from '@/nucleo/preferencias.js'
import Icono from './Icono.vue'

// Vistas guardadas de una pantalla: los filtros (y la pestaña) que la persona
// usa a menudo, con un nombre («Calzado activo», «Químicos sin CAS»). Se guardan
// en sus preferencias (este navegador). El nombre se escribe en el mismo menú.
//   pantalla: clave de la pantalla; actual: filtros de ahora ({clave: valor});
//   evento «aplicar» con los filtros de la vista elegida.
const props = defineProps({ pantalla: { type: String, required: true }, actual: { type: Object, required: true } })
const emit = defineEmits(['aplicar'])
const abierto = ref(false)
const raiz = ref(null)
const nueva = ref(null)
const ocupado = ref(false)

const vistas = computed(() => preferencias.vistas[props.pantalla] || [])
const limpio = (q) => Object.fromEntries(Object.entries(q || {}).filter(([, v]) => v !== '' && v !== null && v !== undefined).map(([k, v]) => [k, String(v)]))
const igual = (a, b) => JSON.stringify(Object.entries(limpio(a)).sort()) === JSON.stringify(Object.entries(limpio(b)).sort())
const activa = computed(() => vistas.value.find((v) => igual(v.query, props.actual)))

function fuera(e) {
  if (raiz.value && !raiz.value.contains(e.target)) cerrar()
}
function alternar() {
  abierto.value = !abierto.value
  if (abierto.value) setTimeout(() => document.addEventListener('click', fuera), 0)
  else document.removeEventListener('click', fuera)
}
function cerrar() {
  abierto.value = false
  document.removeEventListener('click', fuera)
}
onBeforeUnmount(() => document.removeEventListener('click', fuera))

function guardar(lista, mensaje) {
  guardarVistas(props.pantalla, lista)
  if (mensaje) avisar(mensaje)
  return true
}
async function crear() {
  const nombre = (nueva.value?.nombre || '').trim()
  if (!nombre) return
  const otras = vistas.value.filter((v) => v.nombre.toLowerCase() !== nombre.toLowerCase())
  if (guardar([...otras, { nombre, query: limpio(props.actual) }], t('View “{0}” saved.', [nombre]))) { nueva.value = null; cerrar() }
}
function quitar(v) {
  guardar(vistas.value.filter((x) => x !== v), t('View “{0}” deleted.', [v.nombre]))
}
function elegir(v) {
  cerrar()
  emit('aplicar', { ...v.query })
}
</script>

<template>
  <div ref="raiz" class="vistas-guardadas" @keydown.esc="cerrar">
    <button type="button" class="btn" :aria-expanded="abierto" aria-haspopup="true" @click="alternar">
      <Icono nombre="lista" :tam="15" />{{ tx(activa ? activa.nombre : t('Saved views')) }}<Icono nombre="abajo" :tam="13" />
    </button>
    <div v-if="abierto" v-flotante class="vg-menu" role="menu">
      <p v-if="!vistas.length" class="ayuda vg-vacio">{{ t('Save the filters you use often to come back to them in one click.') }}</p>
      <div v-for="v in vistas" :key="v.nombre" class="vg-fila" :class="{ activa: activa === v }">
        <button type="button" class="vg-elegir" role="menuitem" @click="elegir(v)">{{ tx(v.nombre) }}</button>
        <button type="button" class="btn-icono" :aria-label="t('Delete view {0}', [v.nombre])" :disabled="ocupado" @click="quitar(v)"><Icono nombre="basura" :tam="14" /></button>
      </div>
      <form v-if="nueva" class="vg-form" @submit.prevent="crear">
        <input v-model="nueva.nombre" class="entrada entrada-chica" type="text" maxlength="60" :aria-label="t('Name of the view')"
               placeholder="Ej.: Calzado activo" autofocus />
        <div class="fila-flex">
          <button class="btn btn-chico btn-fantasma" type="button" @click="nueva = null">{{ t('Cancel') }}</button>
          <button class="btn btn-chico btn-primario" type="submit" :disabled="!nueva.nombre.trim()">{{ t('Save') }}</button>
        </div>
        <p class="ayuda">Guarda los filtros, el orden y las columnas de ahora.</p>
      </form>
      <button v-else type="button" class="btn btn-chico vg-nueva" role="menuitem" @click="nueva = { nombre: '' }"><Icono nombre="mas" :tam="14" />{{ t('Save current filters as a view') }}</button>
    </div>
  </div>
</template>

<style scoped>
.vistas-guardadas { position: relative; }
.vg-menu { position: absolute; z-index: 30; top: calc(100% + 4px); inset-inline-start: 0; min-width: 260px; max-width: 340px; background: var(--superficie);
  border: 1px solid var(--linea); border-radius: var(--radio-panel); box-shadow: var(--sombra-flotante); padding: 6px; display: flex; flex-direction: column; gap: 2px; }
.vg-fila { display: flex; align-items: center; gap: 4px; border-radius: var(--radio); }
.vg-fila.activa { background: var(--acento-claro); }
.vg-elegir { flex: 1; text-align: start; border: 0; background: none; font: inherit; color: inherit; padding: 8px 10px; cursor: pointer; border-radius: var(--radio); }
.vg-elegir:hover { background: var(--fila-hover); }
.vg-vacio { margin: 6px 8px; }
.vg-nueva { margin-top: 4px; justify-content: flex-start; }
.vg-form { display: flex; flex-direction: column; gap: 6px; padding: 6px; border-top: 1px solid var(--linea-suave); margin-top: 4px; }
.vg-form .fila-flex { justify-content: flex-end; }
</style>
