<template>
  <div class="py-20 text-center flex flex-col items-center gap-4">
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="w-20 h-20 text-base-content/20"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      stroke-width="1"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
      />
    </svg>
    <h2 class="text-2xl font-bold">{{ title }}</h2>
    <p v-if="message" class="text-base-content/60">{{ message }}</p>
    <RouterLink v-if="homeLink" to="/" class="btn btn-primary btn-sm mt-2">
      Wróć do strony głównej
    </RouterLink>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  message: { type: String, default: '' },
  homeLink: { type: Boolean, default: true },
})
</script>
