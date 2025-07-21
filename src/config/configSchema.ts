/**
 * Centralized configuration schema for lsfg-vk frontend.
 * 
 * This mirrors the Python configuration schema to ensure consistency
 * between frontend and backend configuration handling.
 */

// Configuration field type enum
export enum ConfigFieldType {
  BOOLEAN = "boolean",
  INTEGER = "integer",
  FLOAT = "float",
  STRING = "string"
}

// Configuration field definition
export interface ConfigField {
  name: string;
  fieldType: ConfigFieldType;
  default: boolean | number | string;
  description: string;
}

// Configuration schema - must match Python CONFIG_SCHEMA
export const CONFIG_SCHEMA: Record<string, ConfigField> = {
  dll: {
    name: "dll",
    fieldType: ConfigFieldType.STRING,
    default: "/games/Lossless Scaling/Lossless.dll",
    description: "specify where Lossless.dll is stored"
  },
  
  multiplier: {
    name: "multiplier",
    fieldType: ConfigFieldType.INTEGER,
    default: 1,
    description: "change the fps multiplier"
  },
  
  flow_scale: {
    name: "flow_scale",
    fieldType: ConfigFieldType.FLOAT,
    default: 0.8,
    description: "change the flow scale"
  },
  
  performance_mode: {
    name: "performance_mode",
    fieldType: ConfigFieldType.BOOLEAN,
    default: true,
    description: "toggle performance mode"
  },
  
  hdr_mode: {
    name: "hdr_mode",
    fieldType: ConfigFieldType.BOOLEAN,
    default: false,
    description: "enable hdr in games that support it"
  },
  
  experimental_present_mode: {
    name: "experimental_present_mode",
    fieldType: ConfigFieldType.STRING,
    default: "fifo",
    description: "experimental: override vulkan present mode (fifo/mailbox/immediate)"
  },
  
  dxvk_frame_rate: {
    name: "dxvk_frame_rate",
    fieldType: ConfigFieldType.INTEGER,
    default: 0,
    description: "Base framerate cap for DirectX games, before frame multiplier (0 = disabled, requires game re-launch)"
  },
  
  enable_wow64: {
    name: "enable_wow64",
    fieldType: ConfigFieldType.BOOLEAN,
    default: false,
    description: "enable PROTON_USE_WOW64=1 for 32-bit games (use with ProtonGE to fix crashing)"
  },
  
  disable_steamdeck_mode: {
    name: "disable_steamdeck_mode",
    fieldType: ConfigFieldType.BOOLEAN,
    default: false,
    description: "disable Steam Deck mode (unlocks hidden settings in some games)"
  },
  
  per_game_profiles: {
    name: "per_game_profiles",
    fieldType: ConfigFieldType.BOOLEAN,
    default: false,
    description: "enable per-game profiles instead of global configuration"
  }
};

// Type-safe configuration data structure
export interface ConfigurationData {
  dll: string;
  multiplier: number;
  flow_scale: number;
  performance_mode: boolean;
  hdr_mode: boolean;
  experimental_present_mode: string;
  dxvk_frame_rate: number;
  enable_wow64: boolean;
  disable_steamdeck_mode: boolean;
  per_game_profiles: boolean;
}

// Centralized configuration manager
export class ConfigurationManager {
  /**
   * Get default configuration values
   */
  static getDefaults(): ConfigurationData {
    const defaults = {} as ConfigurationData;
    Object.values(CONFIG_SCHEMA).forEach(field => {
      (defaults as any)[field.name] = field.default;
    });
    return defaults;
  }

  /**
   * Get ordered list of configuration field names
   */
  static getFieldNames(): string[] {
    return Object.keys(CONFIG_SCHEMA);
  }

  /**
   * Get field type mapping
   */
  static getFieldTypes(): Record<string, ConfigFieldType> {
    return Object.values(CONFIG_SCHEMA).reduce((acc, field) => {
      acc[field.name] = field.fieldType;
      return acc;
    }, {} as Record<string, ConfigFieldType>);
  }

  /**
   * Create ordered arguments array from configuration object
   */
  static createArgsFromConfig(config: ConfigurationData): (boolean | number | string)[] {
    return [
      config.dll,
      config.multiplier,
      config.flow_scale,
      config.performance_mode,
      config.hdr_mode,
      config.experimental_present_mode,
      config.dxvk_frame_rate,
      config.enable_wow64,
      config.disable_steamdeck_mode,
      config.per_game_profiles
    ];
  }

  /**
   * Validate configuration object against schema
   */
  static validateConfig(config: Partial<ConfigurationData>): ConfigurationData {
    const defaults = this.getDefaults();
    const validated = { ...defaults };

    Object.entries(CONFIG_SCHEMA).forEach(([fieldName, fieldDef]) => {
      const value = config[fieldName as keyof ConfigurationData];
      if (value !== undefined) {
        // Type validation
        if (fieldDef.fieldType === ConfigFieldType.BOOLEAN) {
          (validated as any)[fieldName] = Boolean(value);
        } else if (fieldDef.fieldType === ConfigFieldType.INTEGER) {
          (validated as any)[fieldName] = parseInt(String(value), 10);
        } else if (fieldDef.fieldType === ConfigFieldType.FLOAT) {
          (validated as any)[fieldName] = parseFloat(String(value));
        } else if (fieldDef.fieldType === ConfigFieldType.STRING) {
          (validated as any)[fieldName] = String(value);
        }
      }
    });

    return validated;
  }

  /**
   * Get configuration field definition
   */
  static getFieldDef(fieldName: string): ConfigField | undefined {
    return CONFIG_SCHEMA[fieldName];
  }

  /**
   * Get all field definitions
   */
  static getAllFieldDefs(): ConfigField[] {
    return Object.values(CONFIG_SCHEMA);
  }
}
