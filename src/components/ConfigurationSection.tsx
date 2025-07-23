import { PanelSectionRow, ToggleField, SliderField, DropdownItem } from "@decky/ui";
import { ConfigurationData } from "../config/configSchema";
import { FpsMultiplierControl } from "./FpsMultiplierControl";
import {
  FLOW_SCALE, PERFORMANCE_MODE, HDR_MODE, 
  EXPERIMENTAL_PRESENT_MODE, DXVK_FRAME_RATE, DISABLE_STEAMDECK_MODE,
  MANGOHUD_WORKAROUND, DISABLE_VKBASALT
} from "../config/generatedConfigSchema";

interface ConfigurationSectionProps {
  config: ConfigurationData;
  onConfigChange: (fieldName: keyof ConfigurationData, value: boolean | number | string) => Promise<void>;
}

export function ConfigurationSection({
  config,
  onConfigChange
}: ConfigurationSectionProps) {
  return (
    <>
      <PanelSectionRow>
        <div
          style={{
            fontSize: "14px",
            fontWeight: "bold",
            marginTop: "16px",
            marginBottom: "16px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.2)",
            paddingBottom: "4px",
            color: "white"
          }}
        >
          LSFG Configuration
        </div>
      </PanelSectionRow>

      {/* FPS Multiplier */}
      <FpsMultiplierControl config={config} onConfigChange={onConfigChange} />

      <PanelSectionRow>
        <SliderField
          label={`Flow Scale ${Math.round(config.flow_scale * 100)}%`}
          description="Lowers internal motion estimation resolution, improving performance slightly"
          value={config.flow_scale}
          min={0.25}
          max={3.0}
          step={0.01}
          onChange={(value) => onConfigChange(FLOW_SCALE, value)}
        />
      </PanelSectionRow>

      <PanelSectionRow>
        <ToggleField
          label="Performance Mode"
          description="Uses a lighter model for FG (Recommended for most games)"
          checked={config.performance_mode}
          onChange={(value) => onConfigChange(PERFORMANCE_MODE, value)}
        />
      </PanelSectionRow>

      <PanelSectionRow>
        <ToggleField
          label="HDR Mode"
          description="Enables HDR mode (only for games that support HDR)"
          checked={config.hdr_mode}
          onChange={(value) => onConfigChange(HDR_MODE, value)}
        />
      </PanelSectionRow>

      <PanelSectionRow>
        <div
          style={{
            fontSize: "14px",
            fontWeight: "bold",
            marginTop: "16px",
            marginBottom: "8px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.2)",
            paddingBottom: "4px",
            color: "white"
          }}
        >
          Experimental Features
        </div>
      </PanelSectionRow>

      <PanelSectionRow>
        <DropdownItem
          label="Override Vulkan present mode"
          description="Select a specific Vulkan presentation mode for better performance or compatibility (May cause crashes)"
          menuLabel="Select presentation mode"
          selectedOption={config.experimental_present_mode || "fifo"}
          onChange={(value) => onConfigChange(EXPERIMENTAL_PRESENT_MODE, value.data)}
          rgOptions={[
            { data: "fifo", label: "FIFO (VSync) - Default" },
            { data: "mailbox", label: "Mailbox" }
          ]}
        />
      </PanelSectionRow>

      <PanelSectionRow>
        <div
          style={{
        fontSize: "14px",
        fontWeight: "bold",
        marginTop: "16px",
        marginBottom: "2px",
        borderBottom: "1px solid rgba(255, 255, 255, 0.2)",
        paddingBottom: "2px",
        color: "white"
          }}
        >
          Environment Variables
        </div>
        <div
          style={{
        fontSize: "12px",
        color: "#cccccc",
        marginTop: "2px",
        marginBottom: "8px"
          }}
        >
          Must be toggled before game start or restart game to take effect
        </div>
      </PanelSectionRow>

      <PanelSectionRow>
        <SliderField
          label={`Base FPS Cap${config.dxvk_frame_rate > 0 ? ` (${config.dxvk_frame_rate} FPS)` : ' (Off)'}`}
          description="Base framerate cap for DirectX games, before frame multiplier"
          value={config.dxvk_frame_rate}
          min={0}
          max={60}
          step={1}
          onChange={(value) => onConfigChange(DXVK_FRAME_RATE, value)}
        />
      </PanelSectionRow>

      <PanelSectionRow>
        <ToggleField
          label="Enable WOW64 for 32-bit games"
          description="Enables PROTON_USE_WOW64=1 for 32-bit games (Use with ProtonGE to fix crashing)"
          checked={config.enable_wow64}
          onChange={(value) => onConfigChange('enable_wow64', value)}
        />
      </PanelSectionRow>

      <PanelSectionRow>
        <ToggleField
          label="Disable Steam Deck Mode"
          description="Disables Steam Deck mode (Unlocks hidden settings in some games)"
          checked={config.disable_steamdeck_mode}
          onChange={(value) => onConfigChange(DISABLE_STEAMDECK_MODE, value)}
        />
      </PanelSectionRow>

      <PanelSectionRow>
        <ToggleField
          label="MangoHud Workaround"
          description="Enables a transparent mangohud overlay, sometimes fixes issues with 2X multiplier in game mode"
          checked={config.mangohud_workaround}
          onChange={(value) => onConfigChange(MANGOHUD_WORKAROUND, value)}
        />
      </PanelSectionRow>

      <PanelSectionRow>
        <ToggleField
          label="Disable vkBasalt"
          description="Disables vkBasalt layer which can conflict with LSFG (Reshade, some Decky plugins)"
          checked={config.disable_vkbasalt}
          onChange={(value) => onConfigChange(DISABLE_VKBASALT, value)}
        />
      </PanelSectionRow>
    </>
  );
}
