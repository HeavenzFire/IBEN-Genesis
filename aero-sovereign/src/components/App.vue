<template>
  <div id="app">
    <!-- Desktop Background -->
    <div class="desktop-background"></div>

    <!-- Floating Command Deck -->
    <FloatingCommandDeck />

    <!-- Window Manager -->
    <WindowManager />

    <!-- Start Menu -->
    <StartMenu :visible="isStartMenuOpen" @close="closeStartMenu" />

    <!-- Taskbar -->
    <AeroTaskbar @start-click="toggleStartMenu" />
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import FloatingCommandDeck from './FloatingCommandDeck.vue';
import WindowManager from './WindowManager.vue';
import StartMenu from './StartMenu.vue';
import AeroTaskbar from './AeroTaskbar.vue';

export default {
  name: 'App',
  components: {
    FloatingCommandDeck,
    WindowManager,
    StartMenu,
    AeroTaskbar
  },
  setup() {
    const isStartMenuOpen = ref(false);

    const toggleStartMenu = () => {
      isStartMenuOpen.value = !isStartMenuOpen.value;
    };

    const closeStartMenu = () => {
      isStartMenuOpen.value = false;
    };

    // Close start menu when clicking on desktop
    const handleDesktopClick = (event) => {
      if (isStartMenuOpen.value && 
          !event.target.closest('.start-menu') && 
          !event.target.closest('.start-button')) {
        closeStartMenu();
      }
    };

    onMounted(() => {
      document.addEventListener('click', handleDesktopClick);
      
      // Initialize Tauri API if available
      if (window.__TAURI__) {
        console.log('Aero Sovereign running in Tauri environment');
        // Initialize sovereign core connection
      }
    });

    return {
      isStartMenuOpen,
      toggleStartMenu,
      closeStartMenu
    };
  }
};
</script>

<style scoped>
#app {
  position: relative;
  width: 100%;
  height: 100%;
}
</style>
