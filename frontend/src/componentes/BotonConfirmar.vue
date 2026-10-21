<script setup>
// Acción que pide confirmación en el mismo lugar (sin abrir una ventana):
// el botón se convierte en «¿Borrar? Sí · No». Escape o salir del control cancela.
import { nextTick, ref } from 'vue'
import Icono from './Icono.vue'

const props = defineProps({
  etiqueta: { type: String, required: true }, // para lectores de pantalla y el título: «Borrar Kilogramo»
  pregunta: { type: String, default: '¿Borrar?' },
  confirmar: { type: String, default: 'Sí, borrar' },
  icono: { type: String, default: 'basura' },
  texto: { type: String, default: '' }, // si se da, botón con texto en lugar de solo ícono
  chico: { type: Boolean, default: true },
})
const emit = defineEmits(['confirmar'])
const preguntando = ref(false)
const si = ref(null)

async function preguntar() {
  preguntando.value = true
  await nextTick()
  si.value?.focus()
}
function salir(e) {
  if (!e.currentTarget.contains(e.relatedTarget)) preguntando.value = false
}
function aceptar() {
  preguntando.value = false
  emit('confirmar')
}
</script>

<template>
  <span class="confirmar" @focusout="salir" @keydown.esc="preguntando = false">
    <template v-if="!preguntando">
      <button v-if="texto" type="button" class="btn btn-peligro" :class="{ 'btn-chico': chico }" :title="etiqueta" @click="preguntar">
        <Icono :nombre="icono" :tam="15" />{{ texto }}</button>
      <button v-else type="button" class="btn-icono texto-error" :aria-label="etiqueta" :title="etiqueta" @click="preguntar"><Icono :nombre="icono" :tam="16" /></button>
    </template>
    <span v-else class="confirmar-pregunta" role="group" :aria-label="etiqueta">
      <span>{{ pregunta }}</span>
      <button ref="si" type="button" class="btn btn-chico btn-peligro" @click="aceptar">{{ props.confirmar }}</button>
      <button type="button" class="btn btn-chico btn-fantasma" @click="preguntando = false">No</button>
    </span>
  </span>
</template>

<style scoped>
.confirmar { display: inline-flex; align-items: center; }
.confirmar-pregunta { display: inline-flex; align-items: center; gap: 6px; font-size: 0.84rem; font-weight: 600; color: var(--error); white-space: nowrap; animation: aparecer 0.12s ease-out; }
</style>
