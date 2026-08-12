<template>
  <div class="floating-command-deck aero-glass">
    <div class="command-deck-header">
      <span class="command-deck-title">⌘ Command Deck</span>
      <span class="deck-status" :class="statusClass">{{ statusText }}</span>
    </div>

    <input
      type="text"
      class="command-input"
      v-model="commandInput"
      @keyup.enter="executeCommand"
      placeholder="Enter command..."
      ref="inputRef"
    />

    <div class="command-history" ref="historyRef">
      <div
        v-for="(entry, index) in commandHistory"
        :key="index"
        class="command-entry"
        :class="entry.type"
      >
        <span class="command-prefix">{{ entry.prefix }}</span>
        <span class="command-text">{{ entry.text }}</span>
      </div>
    </div>

    <div class="quick-actions">
      <button
        v-for="(action, index) in quickActions"
        :key="index"
        class="action-button"
        @click="executeQuickAction(action)"
        :title="action.tooltip"
      >
        {{ action.icon }}
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, nextTick } from 'vue';
import { invoke } from '@tauri-apps/api/core';

export default {
  name: 'FloatingCommandDeck',
  setup() {
    const commandInput = ref('');
    const commandHistory = ref([
      { prefix: '>', text: 'System initialized', type: 'success' },
      { prefix: 'ℹ', text: 'Sovereign core active - zero telemetry', type: 'info' }
    ]);
    const isProcessing = ref(false);
    const historyRef = ref(null);
    const inputRef = ref(null);

    const quickActions = [
      { icon: '⚡', command: 'status', tooltip: 'System Status' },
      { icon: '🔒', command: 'encrypt', tooltip: 'Encrypt Data' },
      { icon: '🛡️', command: 'telemetry-check', tooltip: 'Check Telemetry Block' },
      { icon: '⚙️', command: 'config', tooltip: 'Configuration' },
      { icon: '📊', command: 'metrics', tooltip: 'Performance Metrics' },
      { icon: '🧹', command: 'clear', tooltip: 'Clear History' }
    ];

    const statusText = computed(() => isProcessing.value ? 'EXECUTING' : 'READY');
    const statusClass = computed(() => isProcessing.value ? 'processing' : 'ready');

    const scrollToBottom = async () => {
      await nextTick();
      if (historyRef.value) {
        historyRef.value.scrollTop = historyRef.value.scrollHeight;
      }
    };

    const addHistoryEntry = (text, type = 'info', prefix = '>') => {
      commandHistory.value.push({ prefix, text, type });
      if (commandHistory.value.length > 50) {
        commandHistory.value.shift();
      }
      scrollToBottom();
    };

    const executeCommand = async () => {
      const cmd = commandInput.value.trim();
      if (!cmd || isProcessing.value) return;

      isProcessing.value = true;
      addHistoryEntry(cmd, 'command', '⌘');

      try {
        // Check if running in Tauri environment
        if (window.__TAURI__) {
          const result = await invoke('execute_command', {
            commandType: 'script',
            payload: cmd,
            priority: 5
          });
          
          if (result.success) {
            addHistoryEntry(result.output, 'success');
          } else {
            addHistoryEntry(result.error || 'Command failed', 'error');
          }
        } else {
          // Browser fallback - simulate execution
          await new Promise(resolve => setTimeout(resolve, 100));
          addHistoryEntry(`[Browser Mode] Command queued: ${cmd}`, 'success');
        }
      } catch (error) {
        addHistoryEntry(`Error: ${error.message}`, 'error');
      } finally {
        isProcessing.value = false;
        commandInput.value = '';
        inputRef.value?.focus();
      }
    };

    const executeQuickAction = async (action) => {
      if (action.command === 'clear') {
        commandHistory.value = [];
        return;
      }

      commandInput.value = action.command;
      await executeCommand();
    };

    return {
      commandInput,
      commandHistory,
      isProcessing,
      statusText,
      statusClass,
      quickActions,
      historyRef,
      inputRef,
      executeCommand,
      executeQuickAction
    };
  }
};
</script>

<style scoped>
.floating-command-deck {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 380px;
  padding: 16px;
  z-index: 9999;
}

.command-deck-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.command-deck-title {
  font-size: 13px;
  font-weight: 600;
  color: #00f5ff;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.deck-status {
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 3px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.deck-status.ready {
  background: rgba(0, 255, 157, 0.2);
  color: #00ff9d;
  border: 1px solid rgba(0, 255, 157, 0.4);
}

.deck-status.processing {
  background: rgba(255, 184, 0, 0.2);
  color: #ffb800;
  border: 1px solid rgba(255, 184, 0, 0.4);
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.command-input {
  width: 100%;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 4px;
  color: #ffffff;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  outline: none;
  transition: all 0.2s ease;
}

.command-input:focus {
  border-color: #00f5ff;
  box-shadow: 0 0 15px rgba(0, 245, 255, 0.25);
}

.command-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.command-history {
  margin-top: 12px;
  max-height: 220px;
  overflow-y: auto;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 11px;
}

.command-entry {
  padding: 6px 8px;
  margin-bottom: 4px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.03);
  border-left: 2px solid #0095ff;
  display: flex;
  gap: 8px;
}

.command-prefix {
  color: rgba(255, 255, 255, 0.5);
  font-weight: 600;
}

.command-text {
  color: rgba(255, 255, 255, 0.9);
  flex: 1;
  word-break: break-all;
}

.command-entry.command {
  border-left-color: #0095ff;
  background: rgba(0, 149, 255, 0.05);
}

.command-entry.success {
  border-left-color: #00ff9d;
  background: rgba(0, 255, 157, 0.05);
}

.command-entry.error {
  border-left-color: #ff4757;
  background: rgba(255, 71, 87, 0.05);
}

.command-entry.info {
  border-left-color: #b967ff;
  background: rgba(185, 103, 255, 0.05);
}

.quick-actions {
  display: flex;
  gap: 6px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.action-button {
  flex: 1;
  height: 32px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-button:hover {
  background: rgba(0, 149, 255, 0.2);
  border-color: #0095ff;
  transform: translateY(-2px);
}

.action-button:active {
  transform: translateY(0);
}
</style>
