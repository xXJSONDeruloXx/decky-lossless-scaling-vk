import { callable } from "@decky/api";
import { ConfigurationData } from "../config/configSchema";

// Type definitions for API responses
export interface InstallationResult {
  success: boolean;
  error?: string;
  message?: string;
  removed_files?: string[];
}

export interface InstallationStatus {
  installed: boolean;
  lib_exists: boolean;
  json_exists: boolean;
  script_exists: boolean;
  lib_path: string;
  json_path: string;
  script_path: string;
  error?: string;
}

export interface DllDetectionResult {
  detected: boolean;
  path?: string;
  source?: string;
  message?: string;
  error?: string;
}

export interface DllStatsResult {
  success: boolean;
  dll_path?: string;
  dll_sha256?: string;
  dll_source?: string;
  error?: string;
}

// Use centralized configuration data type
export type LsfgConfig = ConfigurationData;

export interface ConfigResult {
  success: boolean;
  config?: LsfgConfig;
  error?: string;
}

export interface ConfigUpdateResult {
  success: boolean;
  message?: string;
  error?: string;
}

export interface ConfigSchemaResult {
  field_names: string[];
  field_types: Record<string, string>;
  defaults: ConfigurationData;
}

export interface UpdateCheckResult {
  success: boolean;
  update_available: boolean;
  current_version: string;
  latest_version: string;
  release_notes: string;
  release_date: string;
  download_url: string;
  error?: string;
}

export interface UpdateDownloadResult {
  success: boolean;
  download_path?: string;
  error?: string;
}

export interface LaunchOptionResult {
  launch_option: string;
  instructions: string;
  explanation: string;
}

export interface FileContentResult {
  success: boolean;
  content?: string;
  path?: string;
  error?: string;
}

// API functions
export const installLsfgVk = callable<[], InstallationResult>("install_lsfg_vk");
export const uninstallLsfgVk = callable<[], InstallationResult>("uninstall_lsfg_vk");
export const checkLsfgVkInstalled = callable<[], InstallationStatus>("check_lsfg_vk_installed");
export const checkLosslessScalingDll = callable<[], DllDetectionResult>("check_lossless_scaling_dll");
export const getDllStats = callable<[], DllStatsResult>("get_dll_stats");
export const getLsfgConfig = callable<[], ConfigResult>("get_lsfg_config");
export const getConfigSchema = callable<[], ConfigSchemaResult>("get_config_schema");
export const getLaunchOption = callable<[], LaunchOptionResult>("get_launch_option");
export const getConfigFileContent = callable<[], FileContentResult>("get_config_file_content");
export const getLaunchScriptContent = callable<[], FileContentResult>("get_launch_script_content");

// Updated config function using object-based configuration (single source of truth)
export const updateLsfgConfig = callable<
  [ConfigurationData],
  ConfigUpdateResult
>("update_lsfg_config");

// Legacy helper function for backward compatibility
export const updateLsfgConfigFromObject = async (config: ConfigurationData): Promise<ConfigUpdateResult> => {
  return updateLsfgConfig(config);
};

// Self-updater API functions
export const checkForPluginUpdate = callable<[], UpdateCheckResult>("check_for_plugin_update");
export const downloadPluginUpdate = callable<[string], UpdateDownloadResult>("download_plugin_update");

// Flatpak API functions
export interface FlatpakExtensionStatus {
  success: boolean;
  message: string;
  error?: string;
  installed_23_08: boolean;
  installed_24_08: boolean;
}

export interface FlatpakApp {
  app_id: string;
  app_name: string;
  has_filesystem_override: boolean;
  has_env_override: boolean;
}

export interface FlatpakAppInfo {
  success: boolean;
  message: string;
  error?: string;
  apps: FlatpakApp[];
  total_apps: number;
}

export interface FlatpakOperationResult {
  success: boolean;
  message: string;
  error?: string;
  app_id?: string;
  operation?: string;
}

export const checkFlatpakExtensionStatus = callable<[], FlatpakExtensionStatus>("check_flatpak_extension_status");
export const installFlatpakExtension = callable<[string], FlatpakOperationResult>("install_flatpak_extension");
export const uninstallFlatpakExtension = callable<[string], FlatpakOperationResult>("uninstall_flatpak_extension");
export const getFlatpakApps = callable<[], FlatpakAppInfo>("get_flatpak_apps");
export const setFlatpakAppOverride = callable<[string], FlatpakOperationResult>("set_flatpak_app_override");
export const removeFlatpakAppOverride = callable<[string], FlatpakOperationResult>("remove_flatpak_app_override");
