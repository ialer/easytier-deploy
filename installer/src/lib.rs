use tauri::command;
use std::path::PathBuf;
use std::fs;
use std::process::Command;

#[command]
fn get_install_path() -> String {
    // 默认安装路径
    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("C:\\"));
    home.join("EasyTier").to_string_lossy().to_string()
}

#[command]
fn check_easytier_installed(path: String) -> bool {
    let core_path = PathBuf::from(&path).join("bin").join("easytier-core.exe");
    core_path.exists()
}

#[command]
fn extract_easytier(path: String) -> Result<String, String> {
    let install_path = PathBuf::from(&path);
    let bin_path = install_path.join("bin");
    
    // 创建目录
    fs::create_dir_all(&bin_path).map_err(|e| e.to_string())?;
    
    // 从EXE所在目录的resources文件夹中获取easytier.zip
    let exe_path = std::env::current_exe().map_err(|e| e.to_string())?;
    let resource_dir = exe_path.parent().ok_or("无法获取EXE目录")?.join("resources");
    let zip_path = resource_dir.join("easytier.zip");
    
    if !zip_path.exists() {
        return Err(format!("找不到EasyTier安装包: {}", zip_path.display()));
    }
    
    // 解压EasyTier
    let output = Command::new("powershell")
        .args(&[
            "-NoProfile",
            "-Command",
            &format!(
                "Expand-Archive -Path '{}' -DestinationPath '{}' -Force",
                zip_path.to_string_lossy(),
                install_path.to_string_lossy()
            ),
        ])
        .output()
        .map_err(|e| e.to_string())?;
    
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    
    // 复制文件到bin目录
    let files = [
        "easytier-core.exe",
        "easytier-cli.exe",
        "Packet.dll",
        "WinDivert64.sys",
        "wintun.dll",
    ];
    
    for file in &files {
        let src = install_path.join(file);
        if src.exists() {
            fs::rename(&src, bin_path.join(file)).map_err(|e| e.to_string())?;
        }
    }
    
    // 清理解压的临时目录
    let _ = fs::remove_dir_all(install_path.join("easytier-windows-x86_64-v2.6.4"));
    
    Ok("EasyTier安装完成".to_string())
}

#[command]
fn write_config(path: String, config: String) -> Result<String, String> {
    let config_path = PathBuf::from(&path).join("config.toml");
    fs::write(&config_path, config).map_err(|e| e.to_string())?;
    Ok("配置文件写入成功".to_string())
}

#[command]
fn register_autostart(path: String) -> Result<String, String> {
    let install_path = PathBuf::from(&path);
    let core_vbs = install_path.join("easytier-core.vbs");
    let dashboard_vbs = install_path.join("dashboard.vbs");
    
    // 创建VBS启动脚本
    let core_vbs_content = format!(
        r#"Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """{}\bin\easytier-core.exe"" -c ""{}\config.toml""", 0, False"#,
        path, path
    );
    fs::write(&core_vbs, core_vbs_content).map_err(|e| e.to_string())?;
    
    let dashboard_vbs_content = format!(
        r#"Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """python"" ""{}\dashboard.py""", 0, False"#,
        path
    );
    fs::write(&dashboard_vbs, dashboard_vbs_content).map_err(|e| e.to_string())?;
    
    // 注册计划任务
    let output = Command::new("schtasks")
        .args(&[
            "/Create",
            "/TN",
            "EasyTeam-Core",
            "/TR",
            &format!("wscript.exe \"{}\"", core_vbs.to_string_lossy()),
            "/SC",
            "ONLOGON",
            "/RL",
            "HIGHEST",
            "/F",
        ])
        .output()
        .map_err(|e| e.to_string())?;
    
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    
    Ok("开机自启注册成功".to_string())
}

#[command]
fn start_service(path: String) -> Result<String, String> {
    let install_path = PathBuf::from(&path);
    let core_vbs = install_path.join("easytier-core.vbs");
    
    // 启动EasyTier Core
    let output = Command::new("wscript")
        .arg(&core_vbs)
        .output()
        .map_err(|e| e.to_string())?;
    
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    
    Ok("服务启动成功".to_string())
}

#[command]
fn check_service_status() -> Result<String, String> {
    let output = Command::new("tasklist")
        .args(&["/FI", "IMAGENAME eq easytier-core.exe"])
        .output()
        .map_err(|e| e.to_string())?;
    
    let stdout = String::from_utf8_lossy(&output.stdout);
    if stdout.contains("easytier-core.exe") {
        Ok("运行中".to_string())
    } else {
        Ok("未运行".to_string())
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            get_install_path,
            check_easytier_installed,
            extract_easytier,
            write_config,
            register_autostart,
            start_service,
            check_service_status
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
