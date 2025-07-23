import { useState, useEffect } from "react";
import { 
  ModalRoot, 
  Field,
  ButtonItem,
  PanelSectionRow
} from "@decky/ui";
import { FaCheck, FaTimes, FaDownload, FaTrash, FaCog } from "react-icons/fa";
import { getFlatpakStatus, configureFlatpak, removeFlatpakConfiguration, FlatpakAppStatus } from "../api/lsfgApi";
import { showSuccessToast, showErrorToast } from "../utils/toastUtils";

interface FlatpakModalProps {
  closeModal?: () => void;
}

export function FlatpakModal({ closeModal }: FlatpakModalProps) {
  const [flatpaks, setFlatpaks] = useState<FlatpakAppStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processingApp, setProcessingApp] = useState<string | null>(null);

  useEffect(() => {
    loadFlatpakStatus();
  }, []);

  const loadFlatpakStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await getFlatpakStatus();
      
      if (result.success) {
        setFlatpaks(result.flatpaks);
      } else {
        setError(result.error || "Failed to load Flatpak status");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load Flatpak status");
    } finally {
      setLoading(false);
    }
  };

  const handleConfigureFlatpak = async (appId: string) => {
    try {
      setProcessingApp(appId);
      
      const result = await configureFlatpak(appId);
      
      if (result.success) {
        showSuccessToast("Flatpak Configured", result.message || `Successfully configured ${appId}`);
        await loadFlatpakStatus(); // Reload status
      } else {
        showErrorToast("Configuration Failed", result.error || "Failed to configure Flatpak");
      }
    } catch (err) {
      showErrorToast("Configuration Failed", err instanceof Error ? err.message : "Failed to configure Flatpak");
    } finally {
      setProcessingApp(null);
    }
  };

  const handleRemoveFlatpakConfiguration = async (appId: string) => {
    try {
      setProcessingApp(appId);
      
      const result = await removeFlatpakConfiguration(appId);
      
      if (result.success) {
        showSuccessToast("Configuration Removed", result.message || `Removed configuration from ${appId}`);
        await loadFlatpakStatus(); // Reload status
      } else {
        showErrorToast("Removal Failed", result.error || "Failed to remove Flatpak configuration");
      }
    } catch (err) {
      showErrorToast("Removal Failed", err instanceof Error ? err.message : "Failed to remove Flatpak configuration");
    } finally {
      setProcessingApp(null);
    }
  };

  const getStatusIcon = (app: FlatpakAppStatus) => {
    if (!app.installed) {
      return <FaTimes style={{ color: "#888", fontSize: "0.9em" }} />;
    }
    
    if (app.configured && app.symlinks_exist) {
      return <FaCheck style={{ color: "#4CAF50", fontSize: "0.9em" }} />;
    }
    
    if (app.configured || app.symlinks_exist) {
      return <FaCog style={{ color: "#FF9800", fontSize: "0.9em" }} />;
    }
    
    return <FaTimes style={{ color: "#f44336", fontSize: "0.9em" }} />;
  };

  const getStatusText = (app: FlatpakAppStatus) => {
    if (!app.installed) {
      return "Not Installed";
    }
    
    if (app.configured && app.symlinks_exist) {
      return "Configured";
    }
    
    if (app.configured || app.symlinks_exist) {
      return "Partially Configured";
    }
    
    return "Not Configured";
  };

  const renderFlatpakItem = (app: FlatpakAppStatus) => {
    const isProcessing = processingApp === app.id;
    const canConfigure = app.installed && (!app.configured || !app.symlinks_exist);
    const canRemove = app.installed && (app.configured || app.symlinks_exist);

    return (
      <Field key={app.id} label={app.name}>
        <div style={{ 
          display: "flex", 
          alignItems: "center", 
          justifyContent: "space-between",
          gap: "10px"
        }}>
          <div style={{ 
            display: "flex", 
            alignItems: "center", 
            gap: "8px",
            flex: 1
          }}>
            {getStatusIcon(app)}
            <span style={{ fontSize: "0.9em", opacity: 0.8 }}>
              {getStatusText(app)}
            </span>
          </div>
          
          <div style={{ 
            display: "flex", 
            gap: "5px" 
          }}>
            {canConfigure && (
              <ButtonItem
                layout="inline"
                onClick={() => handleConfigureFlatpak(app.id)}
                disabled={isProcessing}
              >
                {isProcessing ? (
                  "..."
                ) : (
                  <>
                    <FaDownload style={{ marginRight: "4px" }} />
                    Setup
                  </>
                )}
              </ButtonItem>
            )}
            
            {canRemove && (
              <ButtonItem
                layout="inline"
                onClick={() => handleRemoveFlatpakConfiguration(app.id)}
                disabled={isProcessing}
              >
                {isProcessing ? (
                  "..."
                ) : (
                  <>
                    <FaTrash style={{ marginRight: "4px" }} />
                    Remove
                  </>
                )}
              </ButtonItem>
            )}
          </div>
        </div>
      </Field>
    );
  };

  return (
    <ModalRoot 
      onCancel={closeModal} 
      onOK={closeModal}
    >
      <div style={{ padding: "10px" }}>
        <h2 style={{ marginBottom: "15px", textAlign: "center" }}>
          Flatpak Management
        </h2>
        
        {loading && (
          <div style={{ textAlign: "center", padding: "20px" }}>
            Loading Flatpak applications...
          </div>
        )}
        
        {error && (
          <div style={{ 
            textAlign: "center", 
            padding: "20px",
            color: "#f44336"
          }}>
            Error: {error}
          </div>
        )}
        
        {!loading && !error && (
          <>
            <div style={{ marginBottom: "15px", fontSize: "0.9em", opacity: 0.8 }}>
              Configure gaming applications to work with lsfg-vk. Only installed applications can be configured.
            </div>
            
            <div style={{ maxHeight: "400px", overflowY: "auto" }}>
              {flatpaks.map(renderFlatpakItem)}
            </div>
            
            <div style={{ 
              marginTop: "15px", 
              padding: "10px", 
              background: "rgba(255, 255, 255, 0.1)", 
              borderRadius: "4px",
              fontSize: "0.8em",
              opacity: 0.8
            }}>
              <div style={{ marginBottom: "5px" }}>
                <strong>Legend:</strong>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "5px", marginBottom: "3px" }}>
                <FaCheck style={{ color: "#4CAF50" }} />
                <span>Fully configured</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "5px", marginBottom: "3px" }}>
                <FaCog style={{ color: "#FF9800" }} />
                <span>Partially configured</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                <FaTimes style={{ color: "#f44336" }} />
                <span>Not configured / not installed</span>
              </div>
            </div>
            
            <PanelSectionRow>
              <ButtonItem
                layout="below"
                onClick={loadFlatpakStatus}
                disabled={loading}
              >
                Refresh Status
              </ButtonItem>
            </PanelSectionRow>
          </>
        )}
      </div>
    </ModalRoot>
  );
}
