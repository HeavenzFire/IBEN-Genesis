<template>
  <div class="window-manager">
    <div
      v-for="window in windows"
      :key="window.id"
      class="aero-window"
      :class="{ focused: window.id === focusedWindowId }"
      :style="getWindowStyle(window)"
      @mousedown="focusWindow(window.id)"
    >
      <!-- Window Title Bar -->
      <div class="window-titlebar" @mousedown="startDrag($event, window.id)">
        <span class="window-title">{{ window.title }}</span>
        <div class="window-controls">
          <div
            class="window-control minimize"
            @click.stop="minimizeWindow(window.id)"
            title="Minimize"
          ></div>
          <div
            class="window-control maximize"
            @click.stop="maximizeWindow(window.id)"
            title="Maximize"
          ></div>
          <div
            class="window-control close"
            @click.stop="closeWindow(window.id)"
            title="Close"
          ></div>
        </div>
      </div>

      <!-- Window Content -->
      <div class="window-content">
        <component :is="window.component" v-bind="window.props" />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue';

export default {
  name: 'WindowManager',
  setup() {
    const windows = ref([
      {
        id: 'terminal-1',
        title: 'Terminal Substrate',
        x: 100,
        y: 80,
        width: 700,
        height: 450,
        minimized: false,
        maximized: false,
        component: 'terminal-view'
      },
      {
        id: 'explorer-1',
        title: 'File Explorer',
        x: 200,
        y: 120,
        width: 800,
        height: 500,
        minimized: false,
        maximized: false,
        component: 'explorer-view'
      }
    ]);

    const focusedWindowId = ref('terminal-1');
    const dragState = ref(null);

    const getWindowStyle = (window) => {
      if (window.minimized) {
        return {
          display: 'none'
        };
      }

      if (window.maximized) {
        return {
          top: '0',
          left: '0',
          width: '100%',
          height: 'calc(100% - 48px)', // Subtract taskbar height
          zIndex: focusedWindowId.value === window.id ? 100 : 10
        };
      }

      return {
        top: `${window.y}px`,
        left: `${window.x}px`,
        width: `${window.width}px`,
        height: `${window.height}px`,
        zIndex: focusedWindowId.value === window.id ? 100 : 10
      };
    };

    const focusWindow = (id) => {
      focusedWindowId.value = id;
    };

    const closeWindow = (id) => {
      const index = windows.value.findIndex(w => w.id === id);
      if (index !== -1) {
        windows.value.splice(index, 1);
        if (windows.value.length > 0) {
          focusedWindowId.value = windows.value[windows.value.length - 1].id;
        }
      }
    };

    const minimizeWindow = (id) => {
      const window = windows.value.find(w => w.id === id);
      if (window) {
        window.minimized = true;
        if (focusedWindowId.value === id) {
          const visibleWindows = windows.value.filter(w => !w.minimized && w.id !== id);
          if (visibleWindows.length > 0) {
            focusedWindowId.value = visibleWindows[visibleWindows.length - 1].id;
          } else {
            focusedWindowId.value = null;
          }
        }
      }
    };

    const maximizeWindow = (id) => {
      const window = windows.value.find(w => w.id === id);
      if (window) {
        window.maximized = !window.maximized;
        focusWindow(id);
      }
    };

    const startDrag = (event, id) => {
      const window = windows.value.find(w => w.id === id);
      if (window && !window.maximized) {
        focusWindow(id);
        dragState.value = {
          windowId: id,
          startX: event.clientX,
          startY: event.clientY,
          initialX: window.x,
          initialY: window.y
        };

        document.addEventListener('mousemove', handleDrag);
        document.addEventListener('mouseup', stopDrag);
      }
    };

    const handleDrag = (event) => {
      if (!dragState.value) return;

      const dx = event.clientX - dragState.value.startX;
      const dy = event.clientY - dragState.value.startY;

      const window = windows.value.find(w => w.id === dragState.value.windowId);
      if (window) {
        window.x = dragState.value.initialX + dx;
        window.y = dragState.value.initialY + dy;
      }
    };

    const stopDrag = () => {
      dragState.value = null;
      document.removeEventListener('mousemove', handleDrag);
      document.removeEventListener('mouseup', stopDrag);
    };

    const createWindow = (config) => {
      const newWindow = {
        id: `${config.type}-${Date.now()}`,
        title: config.title || 'New Window',
        x: config.x || 100,
        y: config.y || 100,
        width: config.width || 600,
        height: config.height || 400,
        minimized: false,
        maximized: false,
        component: config.component || 'default-view',
        props: config.props || {}
      };

      windows.value.push(newWindow);
      focusWindow(newWindow.id);
      return newWindow.id;
    };

    return {
      windows,
      focusedWindowId,
      getWindowStyle,
      focusWindow,
      closeWindow,
      minimizeWindow,
      maximizeWindow,
      startDrag,
      createWindow
    };
  }
};
</script>

<style scoped>
.window-manager {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: calc(100% - 48px);
  z-index: 1;
}

.aero-window {
  position: absolute;
  min-width: 300px;
  min-height: 200px;
  background: rgba(20, 30, 45, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(100, 150, 200, 0.4);
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: box-shadow 0.2s ease;
}

.aero-window.focused {
  box-shadow: 0 8px 40px rgba(0, 245, 255, 0.15),
              0 8px 32px rgba(0, 0, 0, 0.4);
  border-color: rgba(0, 245, 255, 0.5);
}

.window-titlebar {
  height: 36px;
  background: linear-gradient(to bottom,
    rgba(255, 255, 255, 0.1) 0%,
    rgba(255, 255, 255, 0.02) 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  cursor: move;
  user-select: none;
}

.window-title {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 0 10px rgba(0, 245, 255, 0.3);
}

.window-controls {
  display: flex;
  gap: 8px;
}

.window-control {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.1s ease, box-shadow 0.2s ease;
}

.window-control:hover {
  transform: scale(1.2);
}

.window-control.minimize {
  background: #ffb800;
  box-shadow: 0 0 8px #ffb800;
}

.window-control.maximize {
  background: #00ff9d;
  box-shadow: 0 0 8px #00ff9d;
}

.window-control.close {
  background: #ff4757;
  box-shadow: 0 0 8px #ff4757;
}

.window-content {
  flex: 1;
  padding: 16px;
  overflow: auto;
  color: rgba(255, 255, 255, 0.9);
}
</style>
