import { PanelSectionRow, ToggleField, SliderField, DropdownItem } from "@decky/ui";
import { ConfigurationData } from "../config/configSchema";

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
            marginBottom: "8px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.2)",
            paddingBottom: "4px",
            color: "white"
          }}
        >
          LSFG Configuration
        </div>
      </PanelSectionRow>

      <PanelSectionRow>
        <ToggleField
          label="Per-Game Profiles"
          description="Enable different settings for each game instead of global configuration (requires game restart)"
          checked={config.per_game_profiles}
          onChange={(value) => onConfigChange('per_game_profiles', value)}
        />
      </PanelSectionRow>

      <PanelSectionRow>
        <SliderField
          label="FPS Multiplier"
          description="Traditional FPS multiplier value"
          value={config.multiplier}
          min={1}
          max={4}
          step={1}
          notchCount={4}
          notchLabels={[
            { notchIndex: 0, label: "OFF", value: 1 },
            { notchIndex: 1, label: "2X", value: 2 },
            { notchIndex: 2, label: "3X", value: 3 },
            { notchIndex: 3, label: "4X", value: 4 }
          ]}
          showValue={false}
          notchTicksVisible={true}
          onChange={(value) => onConfigChange('multiplier', value)}
        />
      </PanelSectionRow>

      <PanelSectionRow>
        <SliderField
          label={`Flow Scale ${Math.round(config.flow_scale * 100)}%`}
          description="Lowers internal motion estimation resolution, improving performance slightly"
          value={config.flow_scale}
          min={0.25}
          max={1.0}
          step={0.01}
          onChange={(value) => onConfigChange('flow_scale', value)}
        />
      </PanelSectionRow>

      <PanelSectionRow>
        <ToggleField
          label="Performance Mode"
          description="Uses a lighter model for FG (Recommended for most games)"
          checked={config.performance_mode}
          onChange={(value) => onConfigChange('performance_mode', value)}
        />
      </PanelSectionRow>

      <PanelSectionRow>
        <ToggleField
          label="HDR Mode"
          description="Enables HDR mode (only for games that support HDR)"
          checked={config.hdr_mode}
          onChange={(value) => onConfigChange('hdr_mode', value)}
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
          onChange={(value) => onConfigChange('experimental_present_mode', value.data)}
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
            marginBottom: "8px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.2)",
            paddingBottom: "4px",
            color: "white"
          }}
        >
          Environment Variables (Requires re-launch)
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
          onChange={(value) => onConfigChange('dxvk_frame_rate', value)}
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
          onChange={(value) => onConfigChange('disable_steamdeck_mode', value)}
        />
      </PanelSectionRow>
    </>
  );
}
