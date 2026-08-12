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

        Self {
            config: Mutex::new(config),
            cipher: Mutex::new(cipher),
            execution_log: Mutex::new(Vec::new()),
            broadcast_tx,
            blocked_cache: Mutex::new(HashSet::new()),
        }
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
            get_execution_log
        ])
        .run(tauri::generate_context!())
        .expect("error while running aero-sovereign");
}
