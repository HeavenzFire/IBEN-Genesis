<template>
  <div class="start-menu" :class="{ hidden: !visible }">
    <!-- Search Bar -->
    <input
      type="text"
      class="search-bar"
      v-model="searchQuery"
      placeholder="Search programs, files, settings..."
      ref="searchInput"
    />

    <!-- Left Column - Pinned Apps -->
    <div class="start-menu-section">
      <div class="section-title">Pinned Applications</div>
      <div
        v-for="(app, index) in pinnedApps"
        :key="index"
        class="menu-item"
        @click="launchApp(app)"
      >
        <div class="menu-item-icon">{{ app.icon }}</div>
        <div class="menu-item-label">{{ app.name }}</div>
      </div>
    </div>

    <!-- Right Column - System & Quick Access -->
    <div class="start-menu-section">
      <div class="section-title">System</div>
      <div
        v-for="(item, index) in systemItems"
        :key="index"
        class="menu-item"
        @click="executeSystemAction(item.action)"
      >
        <div class="menu-item-icon">{{ item.icon }}</div>
        <div class="menu-item-label">{{ item.name }}</div>
      </div>

      <div class="section-title" style="margin-top: 16px;">Sovereign Core</div>
      <div
        v-for="(core, index) in sovereignCoreItems"
        :key="index"
        class="menu-item"
        @click="executeCoreAction(core.action)"
      >
        <div class="menu-item-icon">{{ core.icon }}</div>
        <div class="menu-item-label">{{ core.name }}</div>
      </div>
    </div>

    <!-- User Profile & Power -->
    <div class="start-menu-footer">
      <div class="user-profile">
        <div class="user-avatar">👤</div>
        <span class="user-name">Sovereign User</span>
      </div>
      <div class="power-options">
        <button class="power-button" title="Sleep">💤</button>
        <button class="power-button" title="Shutdown">⏻</button>
        <button class="power-button" title="Restart">🔄</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, nextTick } from 'vue';
import { invoke } from '@tauri-apps/api/core';

export default {
  name: 'StartMenu',
  props: {
    visible: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close'],
  setup(props, { emit }) {
    const searchQuery = ref('');
    const searchInput = ref(null);

    const pinnedApps = ref([
      { icon: '💻', name: 'Terminal Substrate', action: 'launch-terminal' },
      { icon: '📁', name: 'File Explorer', action: 'launch-explorer' },
      { icon: '🌍', name: 'Web Browser', action: 'launch-browser' },
      { icon: '⚙️', name: 'System Settings', action: 'launch-settings' },
      { icon: '🛡️', name: 'Sovereign Core', action: 'launch-sovereign' },
      { icon: '📊', name: 'Task Manager', action: 'launch-taskmanager' },
      { icon: '🎨', name: 'Aero Themes', action: 'launch-themes' },
      { icon: '🔒', name: 'Encryption Manager', action: 'launch-encryption' }
    ]);

    const systemItems = ref([
      { icon: '📂', name: 'Documents', action: 'open-documents' },
      { icon: '🖼️', name: 'Pictures', action: 'open-pictures' },
      { icon: '🎵', name: 'Music', action: 'open-music' },
      { icon: '⬇️', name: 'Downloads', action: 'open-downloads' },
      { icon: '🗑️', name: 'Recycle Bin', action: 'open-recyclebin' }
    ]);

    const sovereignCoreItems = ref([
      { icon: '🔐', name: 'Encrypt Data', action: 'core-encrypt' },
      { icon: '🛡️', name: 'Telemetry Block Status', action: 'core-telemetry' },
      { icon: '📋', name: 'Execution Log', action: 'core-logs' },
      { icon: '⚡', name: 'Native Binary Runner', action: 'core-native' },
      { icon: '🔧', name: 'DLL Injection Hooks', action: 'core-dll' },
      { icon: '🤖', name: 'Background Daemons', action: 'core-daemons' }
    ]);

    const focusSearch = async () => {
      await nextTick();
      if (searchInput.value) {
        searchInput.value.focus();
      }
    };

    watch(() => props.visible, (newVal) => {
      if (newVal) {
        focusSearch();
      }
    });

    const launchApp = async (app) => {
      console.log('Launching app:', app.name);
      
      if (window.__TAURI__) {
        try {
          await invoke('execute_command', {
            commandType: 'nativeBinary',
            payload: app.action,
            priority: 5
          });
        } catch (error) {
          console.error('Failed to launch app:', error);
        }
      }
      
      emit('close');
    };

    const executeSystemAction = async (action) => {
      console.log('System action:', action);
      emit('close');
    };

    const executeCoreAction = async (action) => {
      console.log('Core action:', action);
      
      if (window.__TAURI__) {
        try {
          const cmdType = action.includes('encrypt') ? 'script' : 
                         action.includes('telemetry') ? 'script' : 'script';
          
          await invoke('execute_command', {
            commandType: cmdType,
            payload: action,
            priority: 5
          });
        } catch (error) {
          console.error('Core action failed:', error);
        }
      }
      
      emit('close');
    };

    return {
      searchQuery,
      searchInput,
      pinnedApps,
      systemItems,
      sovereignCoreItems,
      launchApp,
      executeSystemAction,
      executeCoreAction
    };
  }
};
</script>

<style scoped>
.start-menu {
  position: fixed;
  bottom: 56px;
  left: 12px;
  width: 480px;
  height: 560px;
  background: rgba(20, 30, 45, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(100, 150, 200, 0.4);
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  z-index: 9998;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto 1fr auto;
  padding: 16px;
  gap: 16px;
  transform-origin: bottom left;
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.start-menu.hidden {
  transform: scale(0.95) translateY(20px);
  opacity: 0;
  pointer-events: none;
}

.search-bar {
  grid-column: 1 / -1;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 6px;
  color: #ffffff;
  font-size: 14px;
  outline: none;
  transition: all 0.2s ease;
}

.search-bar:focus {
  border-color: #00f5ff;
  box-shadow: 0 0 15px rgba(0, 245, 255, 0.25);
}

.search-bar::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.start-menu-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow-y: auto;
}

.section-title {
  font-size: 11px;
  font-weight: 600;
  color: #00f5ff;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.menu-item {
  padding: 10px 12px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 12px;
}

.menu-item:hover {
  background: rgba(0, 149, 255, 0.15);
  border-color: #0095ff;
  transform: translateX(4px);
}

.menu-item-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.menu-item-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
}

.start-menu-footer {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(0, 149, 255, 0.2);
  border: 1px solid rgba(0, 149, 255, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.user-name {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.power-options {
  display: flex;
  gap: 8px;
}

.power-button {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
  font-size: 18px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.power-button:hover {
  background: rgba(255, 71, 87, 0.2);
  border-color: #ff4757;
  transform: scale(1.1);
}
</style>
