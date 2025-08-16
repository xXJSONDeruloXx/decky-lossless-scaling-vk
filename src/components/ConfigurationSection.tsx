import { PanelSectionRow, ToggleField, SliderField, ButtonItem } from "@decky/ui";
import { useState, useEffect } from "react";
import { RiArrowDownSFill, RiArrowUpSFill } from "react-icons/ri";
import { ConfigurationData } from "../config/configSchema";
import { FpsMultiplierControl } from "./FpsMultiplierControl";
import {
  NO_FP16, FLOW_SCALE, PERFORMANCE_MODE, HDR_MODE, 
  EXPERIMENTAL_PRESENT_MODE, DXVK_FRAME_RATE, DISABLE_STEAMDECK_MODE,
  MANGOHUD_WORKAROUND, DISABLE_VKBASALT, FORCE_ENABLE_VKBASALT, ENABLE_WSI
} from "../config/generatedConfigSchema";

interface ConfigurationSectionProps {
  config: ConfigurationData;
  onConfigChange: (fieldName: keyof ConfigurationData, value: boolean | number | string) => Promise<void>;
}

const WORKAROUNDS_COLLAPSED_KEY = 'lsfg-workarounds-collapsed';

export function ConfigurationSection({
  config,
  onConfigChange
}: ConfigurationSectionProps) {
  // Initialize with localStorage value, fallback to true if not found
  const [workaroundsCollapsed, setWorkaroundsCollapsed] = useState(() => {
    try {
      const saved = localStorage.getItem(WORKAROUNDS_COLLAPSED_KEY);
      return saved !== null ? JSON.parse(saved) : true;
    } catch {
      return true;
    }
  });

  // Persist workarounds collapse state to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(WORKAROUNDS_COLLAPSED_KEY, JSON.stringify(workaroundsCollapsed));
    } catch (error) {
      console.warn('Failed to save workarounds collapse state:', error);
    }
  }, [workaroundsCollapsed]);

  return (
    <>
      <style>
        {`
        .LSFG_WorkaroundsCollapseButton_Container > div > div > div > button {
          height: 10px !important;
        }
        .LSFG_WorkaroundsCollapseButton_Container > div > div > div > div > button {
          height: 10px !important;
        }
        `}
      </style>

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
          label={`Flow Scale (${Math.round(config.flow_scale * 100)}%)`}
          description="Lowers internal motion estimation resolution, improving performance slightly"
          value={config.flow_scale}
          min={0.25}
          max={1.0}
          step={0.01}
          onChange={(value) => onConfigChange(FLOW_SCALE, value)}
        />
      </PanelSectionRow>

      <PanelSectionRow>
        <SliderField
          label={`Base FPS Cap${config.dxvk_frame_rate > 0 ? ` (${config.dxvk_frame_rate} FPS)` : ' (Off)'}`}
          description="Base framerate cap for DirectX games, before frame multiplier. (Requires game restart to apply)"
          value={config.dxvk_frame_rate}
          min={0}
          max={60}
          step={1}
          onChange={(value) => onConfigChange(DXVK_FRAME_RATE, value)}
        />
      </PanelSectionRow>

      <PanelSectionRow>
        <ToggleField
          label={`Present Mode (${(config.experimental_present_mode || "fifo") === "fifo" ? "FIFO - VSync" : "Mailbox"})`}
          description="Toggle between FIFO - VSync (default) and Mailbox presentation modes for better performance or compatibility"
          checked={(config.experimental_present_mode || "fifo") === "fifo"}
          onChange={(value) => onConfigChange(EXPERIMENTAL_PRESENT_MODE, value ? "fifo" : "mailbox")}
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

      {/* <PanelSectionRow>
        <ToggleField
          label="Force Disable FP16"
          description="Force-disable FP16 acceleration"
          checked={config.no_fp16}
          onChange={(value) => onConfigChange(NO_FP16, value)}
        />
      </PanelSectionRow> */}

      <PanelSectionRow>
        <ToggleField
          label="HDR Mode"
          description={config.enable_wsi ? "Enables HDR mode (only for games that support HDR)" : "Enable WSI in the workarounds menu to unlock HDR toggle"}
          checked={config.hdr_mode}
          disabled={!config.enable_wsi}
          onChange={(value) => onConfigChange(HDR_MODE, value)}
        />
      </PanelSectionRow>

      {/* Workarounds Section */}
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
          Workarounds
        </div>
      </PanelSectionRow>

      <PanelSectionRow>
        <div className="LSFG_WorkaroundsCollapseButton_Container">
          <ButtonItem
            layout="below"
            bottomSeparator={workaroundsCollapsed ? "standard" : "none"}
            onClick={() => setWorkaroundsCollapsed(!workaroundsCollapsed)}
          >
            {workaroundsCollapsed ? (
              <RiArrowDownSFill
                style={{ transform: "translate(0, -13px)", fontSize: "1.5em" }}
              />
            ) : (
              <RiArrowUpSFill
                style={{ transform: "translate(0, -12px)", fontSize: "1.5em" }}
              />
            )}
          </ButtonItem>
        </div>
      </PanelSectionRow>

      {!workaroundsCollapsed && (
        <>
        <PanelSectionRow>
            <ToggleField
              label="Enable WSI"
              description="Re-Enable Gamescope WSI Layer. Requires game restart to apply."
              checked={config.enable_wsi}
              disabled={config.hdr_mode}
              onChange={(value) => {
                if (!value && config.hdr_mode) {
                  // Turn off HDR when disabling WSI
                  onConfigChange(HDR_MODE, false);
                }
                onConfigChange(ENABLE_WSI, value);
              }}
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
              disabled={config.force_enable_vkbasalt}
              onChange={(value) => {
                if (value && config.force_enable_vkbasalt) {
                  // Turn off force enable when enabling disable
                  onConfigChange(FORCE_ENABLE_VKBASALT, false);
                }
                onConfigChange(DISABLE_VKBASALT, value);
              }}
            />
          </PanelSectionRow>

          <PanelSectionRow>
            <ToggleField
              label="Force Enable vkBasalt"
              description="Force vkBasalt to engage to fix framepacing issues in gamemode"
              checked={config.force_enable_vkbasalt}
              disabled={config.disable_vkbasalt}
              onChange={(value) => {
                if (value && config.disable_vkbasalt) {
                  // Turn off disable when enabling force enable
                  onConfigChange(DISABLE_VKBASALT, false);
                }
                onConfigChange(FORCE_ENABLE_VKBASALT, value);
              }}
            />
          </PanelSectionRow>
        </>
      )}
    </>
  );
}
