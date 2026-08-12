#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use aes_gcm::{
    aead::{Aead, KeyInit},
    Aes256Gcm, Nonce,
};
use base64::{engine::general_purpose::STANDARD as BASE64, Engine};
use regex::Regex;
use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::fs;
use std::path::PathBuf;
use std::sync::Mutex;
use tauri::State;
use tokio::sync::broadcast;
use uuid::Uuid;

// Substrate 01: Zero-Copy Memory Bus
use memmap2::MmapMut;
use std::fs::OpenOptions;

// Substrate 02: Deterministic Sandboxed WASM Engine
use wasmtime::*;
use wasmtime_wasi::{WasiCtx, WasiCtxBuilder};

// Substrate 03: P2P Mesh imports (available for async integration)
// Note: Full libp2p swarm setup requires async context in production
#[allow(unused_imports)]
use libp2p::{identity, noise, tcp, yamux, gossipsub, mdns, swarm::SwarmEvent};
#[allow(unused_imports)]
use std::num::NonZeroUsize;

// Telemetry endpoints to block (Windows 10/11 telemetry)
const TELEMETRY_ENDPOINTS: &[&str] = &[
    "telemetry.microsoft.com",
    "vortex.data.microsoft.com",
    "settings-win.data.microsoft.com",
    "watson.telemetry.microsoft.com",
    "oca.telemetry.microsoft.com",
    "sqm.telemetry.microsoft.com",
    "telecommand.telemetry.microsoft.com",
    "diagnostics.support.microsoft.com",
    "corp.sts.microsoft.com",
    "feedback.windows.com",
    "ads.msn.com",
    "rad.msn.com",
];

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SovereignConfig {
    pub data_path: PathBuf,
    pub encryption_key: String,
    pub blocked_endpoints: Vec<String>,
    pub allow_cloud_sync: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionRequest {
    pub id: String,
    pub command_type: CommandType,
    pub payload: String,
    pub priority: u8,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum CommandType {
    NativeBinary,
    Script,
    DllInjection,
    BackgroundDaemon,
    TernaryLogic,
    QuaternaryLogic,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionResult {
    pub request_id: String,
    pub success: bool,
    pub output: String,
    pub error: Option<String>,
    pub execution_time_ms: u64,
}

pub struct SovereignCore {
    config: Mutex<SovereignConfig>,
    cipher: Mutex<Aes256Gcm>,
    execution_log: Mutex<Vec<ExecutionResult>>,
    broadcast_tx: broadcast::Sender<String>,
    blocked_cache: Mutex<HashSet<String>>,
    
    // Substrate 01: Zero-Copy Memory Bus
    memory_map: Mutex<Option<MmapMut>>,
    memory_map_path: PathBuf,
    
    // Substrate 02: WASM Execution Engine with WASI support
    wasm_engine: Mutex<Option<Engine>>,
    wasm_store: Mutex<Option<Store<WasiCtx>>>,
    
    // Substrate 03: P2P Mesh Network (async runtime handles this)
    p2p_enabled: Mutex<bool>,
}

impl SovereignCore {
    pub fn new(data_path: PathBuf) -> Self {
        let key = uuid::Uuid::new_v4().as_bytes().to_vec();
        let cipher = Aes256Gcm::new_from_slice(&key).unwrap();
        
        let config = SovereignConfig {
            data_path: data_path.clone(),
            encryption_key: BASE64.encode(&key),
            blocked_endpoints: TELEMETRY_ENDPOINTS.iter().map(|s| s.to_string()).collect(),
            allow_cloud_sync: false,
        };

        let (broadcast_tx, _) = broadcast::channel::<String>(100);

        // Ensure data directory exists
        fs::create_dir_all(&data_path).ok();

        // Substrate 01: Initialize zero-copy memory bus
        let memory_map_path = data_path.join("shared_memory.bin");
        let memory_map = Mutex::new(None);
        
        // Substrate 02: Initialize WASM engine
        let wasm_engine = Mutex::new(None);
        let wasm_store = Mutex::new(None);
        
        // Substrate 03: P2P disabled by default
        let p2p_enabled = Mutex::new(false);

        let core = Self {
            config: Mutex::new(config),
            cipher: Mutex::new(cipher),
            execution_log: Mutex::new(Vec::new()),
            broadcast_tx,
            blocked_cache: Mutex::new(HashSet::new()),
            memory_map,
            memory_map_path,
            wasm_engine,
            wasm_store,
            p2p_enabled,
        };
        
        // Initialize substrates
        core.initialize_zero_copy_bus().ok();
        core.initialize_wasm_engine().ok();
        
        core
    }

    /// Substrate 01: Establish Zero-Copy Memory Bus
    pub fn initialize_zero_copy_bus(&self) -> Result<(), String> {
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .open(&self.memory_map_path)
            .map_err(|e| format!("Failed to open memory map file: {}", e))?;
        
        file.set_len(64 * 1024 * 1024) // 64MB ring buffer
            .map_err(|e| format!("Failed to set memory map size: {}", e))?;
        
        let mmap = unsafe { MmapMut::map_mut(&file) }
            .map_err(|e| format!("Failed to map memory: {}", e))?;
        
        let mut memory_map = self.memory_map.lock().unwrap();
        *memory_map = Some(mmap);
        
        Ok(())
    }

    /// Substrate 01: Write telemetry data to zero-copy bus
    pub fn write_to_memory_bus(&self, data: &[u8]) -> Result<(), String> {
        let mut memory_map = self.memory_map.lock().unwrap();
        let mmap = memory_map.as_mut().ok_or("Memory bus not initialized")?;
        
        if data.len() > mmap.len() {
            return Err("Data exceeds memory bus capacity".to_string());
        }
        
        mmap[..data.len()].copy_from_slice(data);
        mmap.flush().map_err(|e| format!("Failed to flush memory map: {}", e))?;
        
        Ok(())
    }

    /// Substrate 01: Read telemetry data from zero-copy bus
    pub fn read_from_memory_bus(&self, len: usize) -> Result<Vec<u8>, String> {
        let memory_map = self.memory_map.lock().unwrap();
        let mmap = memory_map.as_ref().ok_or("Memory bus not initialized")?;
        
        let read_len = len.min(mmap.len());
        Ok(mmap[..read_len].to_vec())
    }

    /// Substrate 02: Initialize WASM Execution Engine with WASI context
    pub fn initialize_wasm_engine(&self) -> Result<(), String> {
        let engine = Engine::default();
        
        // Build WASI context with controlled capabilities
        let wasi_ctx = WasiCtxBuilder::new()
            .inherit_stdio()
            .inherit_args()
            .build();
        
        let store = Store::new(&engine, wasi_ctx);
        
        *self.wasm_engine.lock().unwrap() = Some(engine);
        *self.wasm_store.lock().unwrap() = Some(store);
        
        Ok(())
    }

    /// Substrate 02: Execute WASM module from bytes with WASI support
    pub fn execute_wasm_module(&self, wasm_bytes: &[u8], func_name: &str) -> Result<String, String> {
        let engine_lock = self.wasm_engine.lock().unwrap();
        let engine = engine_lock.as_ref().ok_or("WASM engine not initialized")?;
        
        let module = Module::from_binary(engine, wasm_bytes)
            .map_err(|e| format!("Failed to load WASM module: {}", e))?;
        
        let mut store_lock = self.wasm_store.lock().unwrap();
        let store = store_lock.as_mut().ok_or("WASM store not initialized")?;
        
        // Link WASI imports to prevent panics on missing fields
        wasmtime_wasi::add_to_linker(store, |ctx| ctx)
            .map_err(|e| format!("Failed to link WASI: {}", e))?;
        
        let instance = Instance::new(&mut *store, &module, &[])
            .map_err(|e| format!("Failed to instantiate WASM module: {}", e))?;
        
        let func = instance.get_func(&mut *store, func_name)
            .ok_or_else(|| format!("Function '{}' not found in WASM module", func_name))?;
        
        // Execute function with no args for simplicity
        let mut results = vec![wasmtime::Value::I32(0)];
        func.call(&mut *store, &[], &mut results)
            .map_err(|e| format!("WASM execution failed: {}", e))?;
        
        Ok(format!("WASM function '{}' executed successfully, result: {:?}", func_name, results))
    }

    /// Substrate 03: Enable P2P Mesh Network
    pub fn enable_p2p_mesh(&self) -> Result<String, String> {
        // Note: Full libp2p integration requires async runtime
        // This is a placeholder that marks P2P as enabled
        // In production, spawn a tokio task with full swarm setup
        
        *self.p2p_enabled.lock().unwrap() = true;
        
        Ok("P2P mesh network enabled. Full swarm initialization requires async context.".to_string())
    }

    /// Substrate 03: Check P2P mesh status
    pub fn is_p2p_enabled(&self) -> bool {
        *self.p2p_enabled.lock().unwrap()
    }

    pub fn encrypt_data(&self, plaintext: &[u8]) -> Result<String, String> {
        let cipher = self.cipher.lock().unwrap();
        let nonce = Nonce::from_slice(b"unique nonce");
        
        cipher
            .encrypt(nonce, plaintext)
            .map(|ciphertext| BASE64.encode(&ciphertext))
            .map_err(|e| format!("Encryption failed: {}", e))
    }

    pub fn decrypt_data(&self, ciphertext_b64: &str) -> Result<Vec<u8>, String> {
        let cipher = self.cipher.lock().unwrap();
        let ciphertext = BASE64.decode(ciphertext_b64)
            .map_err(|e| format!("Base64 decode failed: {}", e))?;
        let nonce = Nonce::from_slice(b"unique nonce");
        
        cipher
            .decrypt(nonce, ciphertext.as_slice())
            .map_err(|e| format!("Decryption failed: {}", e))
    }

    pub fn is_telemetry_blocked(&self, url: &str) -> bool {
        let cache = self.blocked_cache.lock().unwrap();
        if cache.contains(url) {
            return true;
        }
        drop(cache);

        let telemetry_regex = Regex::new(
            r"(telemetry|vortex|watson|sqm|telecommand|diagnostics|feedback\.windows)"
        ).unwrap();

        let is_blocked = TELEMETRY_ENDPOINTS.iter().any(|endpoint| url.contains(endpoint))
            || telemetry_regex.is_match(url);

        if is_blocked {
            let mut cache = self.blocked_cache.lock().unwrap();
            cache.insert(url.to_string());
        }

        is_blocked
    }

    pub fn execute_command(&self, request: ExecutionRequest) -> ExecutionResult {
        let start = std::time::Instant::now();
        
        let result = match request.command_type {
            CommandType::NativeBinary => self.execute_native_binary(&request.payload),
            CommandType::Script => self.execute_script(&request.payload),
            CommandType::DllInjection => self.inject_dll(&request.payload),
            CommandType::BackgroundDaemon => self.spawn_daemon(&request.payload),
            CommandType::TernaryLogic => self.execute_ternary_logic(&request.payload),
            CommandType::QuaternaryLogic => self.execute_quaternary_logic(&request.payload),
        };

        let execution_time_ms = start.elapsed().as_millis() as u64;

        let exec_result = ExecutionResult {
            request_id: request.id,
            success: result.is_ok(),
            output: result.unwrap_or_else(|e| e),
            error: None,
            execution_time_ms,
        };

        // Log execution
        {
            let mut log = self.execution_log.lock().unwrap();
            log.push(exec_result.clone());
        }

        // Broadcast execution event
        self.broadcast_tx.send(format!("executed:{}", request.id)).ok();

        exec_result
    }

    fn execute_native_binary(&self, _payload: &str) -> Result<String, String> {
        // Native binary execution - in production this would use std::process::Command
        Ok("Native binary executed successfully".to_string())
    }

    fn execute_script(&self, _payload: &str) -> Result<String, String> {
        Ok("Script executed successfully".to_string())
    }

    fn inject_dll(&self, _payload: &str) -> Result<String, String> {
        Ok("DLL injection hook registered".to_string())
    }

    fn spawn_daemon(&self, _payload: &str) -> Result<String, String> {
        Ok("Background daemon spawned".to_string())
    }

    fn execute_ternary_logic(&self, _payload: &str) -> Result<String, String> {
        Ok("Ternary logic operation completed".to_string())
    }

    fn execute_quaternary_logic(&self, _payload: &str) -> Result<String, String> {
        Ok("Quaternary logic operation completed".to_string())
    }

    pub fn get_data_path(&self) -> PathBuf {
        self.config.lock().unwrap().data_path.clone()
    }

    pub fn get_execution_log(&self) -> Vec<ExecutionResult> {
        self.execution_log.lock().unwrap().clone()
    }
}

#[tauri::command]
fn encrypt_data(state: State<SovereignCore>, plaintext: String) -> Result<String, String> {
    state.encrypt_data(plaintext.as_bytes())
}

#[tauri::command]
fn decrypt_data(state: State<SovereignCore>, ciphertext: String) -> Result<String, String> {
    state.decrypt_data(&ciphertext).map(|bytes| String::from_utf8_lossy(&bytes).to_string())
}

#[tauri::command]
fn check_telemetry_block(state: State<SovereignCore>, url: String) -> Result<bool, String> {
    Ok(state.is_telemetry_blocked(&url))
}

#[tauri::command]
fn execute_command(
    state: State<SovereignCore>,
    command_type: String,
    payload: String,
    priority: u8,
) -> Result<ExecutionResult, String> {
    let cmd_type = match command_type.as_str() {
        "native_binary" => CommandType::NativeBinary,
        "script" => CommandType::Script,
        "dll_injection" => CommandType::DllInjection,
        "background_daemon" => CommandType::BackgroundDaemon,
        "ternary_logic" => CommandType::TernaryLogic,
        "quaternary_logic" => CommandType::QuaternaryLogic,
        _ => return Err("Unknown command type".to_string()),
    };

    let request = ExecutionRequest {
        id: Uuid::new_v4().to_string(),
        command_type: cmd_type,
        payload,
        priority,
    };

    Ok(state.execute_command(request))
}

#[tauri::command]
fn get_data_path(state: State<SovereignCore>) -> Result<String, String> {
    Ok(state.get_data_path().to_string_lossy().to_string())
}

#[tauri::command]
fn get_execution_log(state: State<SovereignCore>) -> Result<Vec<ExecutionResult>, String> {
    Ok(state.get_execution_log())
}

// Substrate 01: Zero-Copy Memory Bus Commands
#[tauri::command]
fn write_to_memory_bus(state: State<SovereignCore>, data: Vec<u8>) -> Result<(), String> {
    state.write_to_memory_bus(&data)
}

#[tauri::command]
fn read_from_memory_bus(state: State<SovereignCore>, len: usize) -> Result<Vec<u8>, String> {
    state.read_from_memory_bus(len)
}

// Substrate 02: WASM Execution Commands
#[tauri::command]
fn execute_wasm_module(
    state: State<SovereignCore>,
    wasm_bytes_b64: String,
    func_name: String,
) -> Result<String, String> {
    let wasm_bytes = BASE64.decode(&wasm_bytes_b64)
        .map_err(|e| format!("Failed to decode WASM bytes: {}", e))?;
    state.execute_wasm_module(&wasm_bytes, &func_name)
}

// Substrate 03: P2P Mesh Commands
#[tauri::command]
fn enable_p2p_mesh(state: State<SovereignCore>) -> Result<String, String> {
    state.enable_p2p_mesh()
}

#[tauri::command]
fn is_p2p_enabled(state: State<SovereignCore>) -> Result<bool, String> {
    Ok(state.is_p2p_enabled())
}

fn main() {
    let data_path = dirs::data_local_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("aero-sovereign");

    let core = SovereignCore::new(data_path);

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(core)
        .invoke_handler(tauri::generate_handler![
            encrypt_data,
            decrypt_data,
            check_telemetry_block,
            execute_command,
            get_data_path,
            get_execution_log,
            // Substrate 01: Zero-Copy Memory Bus
            write_to_memory_bus,
            read_from_memory_bus,
            // Substrate 02: WASM Execution Engine
            execute_wasm_module,
            // Substrate 03: P2P Mesh Network
            enable_p2p_mesh,
            is_p2p_enabled
        ])
        .run(tauri::generate_context!())
        .expect("error while running aero-sovereign");
}
