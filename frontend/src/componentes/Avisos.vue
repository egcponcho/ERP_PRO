<script setup>
// Avisos breves (toasts) en una región viva para lectores de pantalla.
import { avisos, cerrarAviso } from '@/nucleo/avisos.js'
import Icono from './Icono.vue'

const ICONO = { ok: 'check', error: 'alerta', info: 'info' }
</script>

<template>
  <div class="toasts" role="status" aria-live="polite">
    <TransitionGroup name="toast">
      <div v-for="a in avisos.lista" :key="a.id" class="toast" :class="a.tipo">
        <Icono :nombre="ICONO[a.tipo] || 'info'" :tam="18" />
        <span class="crece">{{ a.texto }}</span>
        <button class="toast-cerrar" type="button" aria-label="Cerrar aviso" @click="cerrarAviso(a.id)"><Icono nombre="cerrar" :tam="14" /></button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toasts { position: fixed; inset-inline-end: 20px; bottom: 20px; display: flex; flex-direction: column; gap: 8px; z-index: 70; width: min(380px, calc(100vw - 32px)); }
.toast { display: flex; align-items: flex-start; gap: 10px; padding: 12px 14px; border-radius: var(--radio); background: var(--flotante); color: #e6ebf3; box-shadow: var(--sombra-flotante); font-size: 0.9rem; }
.toast.ok > svg:first-child { color: #4ade80; }
.toast.error { background: var(--toast-error); }
.toast.error > svg:first-child { color: #ffb4ae; }
.toast-cerrar { border: 0; background: none; color: inherit; opacity: 0.7; cursor: pointer; padding: 2px; border-radius: 4px; display: grid; }
.toast-cerrar:hover { opacity: 1; }
.toast-enter-active, .toast-leave-active { transition: all 0.2s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(8px); }
</style>
