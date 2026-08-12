<template>
  <div class="aero-taskbar">
    <!-- Start Button -->
    <div class="start-button" @click="$emit('start-click')" title="Start Menu"></div>

    <!-- Taskbar Items (Pinned/Active Apps) -->
    <div class="taskbar-items">
      <div
        v-for="(item, index) in taskbarItems"
        :key="index"
        class="taskbar-item"
        :class="{ active: item.active }"
        @click="handleItemClick(item)"
        :title="item.tooltip"
      >
        <span class="item-icon">{{ item.icon }}</span>
      </div>
    </div>

    <!-- System Tray with Hardware Status -->
    <div class="system-tray">
      <!-- Hardware Status Indicators -->
      <div class="hardware-status">
        <div class="status-indicator" title="CPU Usage">
          <div class="status-dot" :class="cpuStatus"></div>
          <span>{{ cpuUsage }}%</span>
        </div>
        <div class="status-indicator" title="Memory Usage">
          <div class="status-dot" :class="memStatus"></div>
          <span>{{ memoryUsage }}%</span>
        </div>
        <div class="status-indicator" title="Disk I/O">
          <div class="status-dot" :class="diskStatus"></div>
          <span>{{ diskIO }} MB/s</span>
        </div>
      </div>

      <!-- Tray Icons -->
      <div class="tray-icons">
        <span class="tray-icon" title="Network">🌐</span>
        <span class="tray-icon" title="Volume">🔊</span>
        <span class="tray-icon" title="Battery">🔋</span>
      </div>

      <!-- Clock -->
      <div class="taskbar-clock">
        <div class="clock-time">{{ currentTime }}</div>
        <div class="clock-date">{{ currentDate }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { invoke } from '@tauri-apps/api/core';

export default {
  name: 'AeroTaskbar',
  emits: ['start-click'],
  setup() {
    const currentTime = ref('');
    const currentDate = ref('');
    const cpuUsage = ref(0);
    const memoryUsage = ref(0);
    const diskIO = ref(0);

    const taskbarItems = ref([
      { icon: '💻', name: 'Terminal', active: true, tooltip: 'Terminal Substrate' },
      { icon: '📁', name: 'Explorer', active: false, tooltip: 'File Explorer' },
      { icon: '🌍', name: 'Browser', active: false, tooltip: 'Web Browser' },
      { icon: '⚙️', name: 'Settings', active: false, tooltip: 'System Settings' },
      { icon: '🛡️', name: 'Sovereign', active: false, tooltip: 'Sovereign Core' }
    ]);

    const updateClock = () => {
      const now = new Date();
      currentTime.value = now.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
      currentDate.value = now.toLocaleDateString([], { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric'
      });
    };

    const updateHardwareStats = async () => {
      if (window.__TAURI__) {
        try {
          // In production, these would call actual system APIs
          // For now, simulate realistic values
          cpuUsage.value = Math.floor(Math.random() * 30) + 5;
          memoryUsage.value = Math.floor(Math.random() * 20) + 30;
          diskIO.value = Math.floor(Math.random() * 100) + 10;
        } catch (error) {
          console.error('Failed to get hardware stats:', error);
        }
      } else {
        // Browser mode - simulated values
        cpuUsage.value = Math.floor(Math.random() * 25) + 8;
        memoryUsage.value = Math.floor(Math.random() * 15) + 35;
        diskIO.value = Math.floor(Math.random() * 50) + 20;
      }
    };

    const cpuStatus = computed(() => {
      if (cpuUsage.value > 80) return 'critical';
      if (cpuUsage.value > 60) return 'warning';
      return '';
    });

    const memStatus = computed(() => {
      if (memoryUsage.value > 85) return 'critical';
      if (memoryUsage.value > 70) return 'warning';
      return '';
    });

    const diskStatus = computed(() => {
      if (diskIO.value > 500) return 'critical';
      if (diskIO.value > 200) return 'warning';
      return '';
    });

    const handleItemClick = (item) => {
      taskbarItems.value.forEach(i => i.active = false);
      item.active = !item.active;
      
      // Emit event for window management
      if (item.active) {
        // Could emit to WindowManager to bring window to front
      }
    };

    let clockInterval;
    let statsInterval;

    onMounted(() => {
      updateClock();
      updateHardwareStats();
      
      clockInterval = setInterval(updateClock, 1000);
      statsInterval = setInterval(updateHardwareStats, 3000);
    });

    onUnmounted(() => {
      clearInterval(clockInterval);
      clearInterval(statsInterval);
    });

    return {
      currentTime,
      currentDate,
      cpuUsage,
      memoryUsage,
      diskIO,
      taskbarItems,
      cpuStatus,
      memStatus,
      diskStatus,
      handleItemClick
    };
  }
};
</script>

<style scoped>
.aero-taskbar {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 48px;
  background: linear-gradient(to bottom,
    rgba(20, 30, 45, 0.9) 0%,
    rgba(10, 14, 20, 0.95) 100%);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border-top: 1px solid rgba(100, 150, 200, 0.3);
  display: flex;
  align-items: center;
  padding: 0 12px;
  z-index: 10000;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.5);
}

.start-button {
  width: 44px;
  height: 44px;
  border-radius: 6px;
  background: linear-gradient(135deg,
    rgba(0, 245, 255, 0.15) 0%,
    rgba(0, 149, 255, 0.1) 100%);
  border: 1px solid rgba(0, 245, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-right: 12px;
}

.start-button:hover {
  background: linear-gradient(135deg,
    rgba(0, 245, 255, 0.25) 0%,
    rgba(0, 149, 255, 0.2) 100%);
  border-color: rgba(0, 245, 255, 0.6);
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.3);
}

.start-button::before {
  content: '❖';
  font-size: 24px;
  color: #00f5ff;
  text-shadow: 0 0 10px rgba(0, 245, 255, 0.6);
}

.taskbar-items {
  display: flex;
  flex: 1;
  gap: 4px;
  overflow-x: auto;
}

.taskbar-item {
  min-width: 52px;
  height: 40px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.taskbar-item:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.taskbar-item.active {
  background: rgba(0, 149, 255, 0.2);
  border-color: #0095ff;
}

.taskbar-item.active::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 3px;
  background: #0095ff;
  border-radius: 2px;
  box-shadow: 0 0 10px #0095ff;
}

.item-icon {
  font-size: 20px;
}

.system-tray {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-left: 16px;
  border-left: 1px solid rgba(255, 255, 255, 0.1);
}

.hardware-status {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 5px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #00ff9d;
  box-shadow: 0 0 8px #00ff9d;
  transition: all 0.3s ease;
}

.status-dot.warning {
  background: #ffb800;
  box-shadow: 0 0 8px #ffb800;
}

.status-dot.critical {
  background: #ff4757;
  box-shadow: 0 0 8px #ff4757;
}

.tray-icons {
  display: flex;
  gap: 10px;
}

.tray-icon {
  font-size: 16px;
  opacity: 0.8;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.tray-icon:hover {
  opacity: 1;
}

.taskbar-clock {
  text-align: right;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.3;
}

.clock-time {
  font-weight: 600;
}

.clock-date {
  opacity: 0.7;
  font-size: 10px;
}
</style>
