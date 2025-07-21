import { useState, useEffect } from "react";
import { 
  ModalRoot, 
  Field,
  Focusable
} from "@decky/ui";
import { getDllStats, DllStatsResult, getConfigFileContent, getLaunchScriptContent, FileContentResult } from "../api/lsfgApi";
import { useProcessDetection } from "../hooks/useProcessDetection";

interface NerdStuffModalProps {
  closeModal?: () => void;
}

export function NerdStuffModal({ closeModal }: NerdStuffModalProps) {
  const [dllStats, setDllStats] = useState<DllStatsResult | null>(null);
  const [configContent, setConfigContent] = useState<FileContentResult | null>(null);
  const [scriptContent, setScriptContent] = useState<FileContentResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Add process detection
  const { processInfo, launchInfo, loading: processLoading } = useProcessDetection();

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Load all data in parallel
        const [dllResult, configResult, scriptResult] = await Promise.all([
          getDllStats(),
          getConfigFileContent(),
          getLaunchScriptContent()
        ]);
        
        setDllStats(dllResult);
        setConfigContent(configResult);
        setScriptContent(scriptResult);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const formatSHA256 = (hash: string) => {
    // Format SHA256 hash for better readability (add spaces every 8 characters)
    return hash.replace(/(.{8})/g, '$1 ').trim();
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      // Could add a toast notification here if desired
    } catch (err) {
      console.error("Failed to copy to clipboard:", err);
    }
  };

  return (
    <ModalRoot onCancel={closeModal} onOK={closeModal}>
      {loading && (
        <div>Loading information...</div>
      )}
      
      {error && (
        <div>Error: {error}</div>
      )}
      
      {!loading && !error && (
        <>
          {/* DLL Stats Section */}
          {dllStats && (
            <>
              {!dllStats.success ? (
                <div>{dllStats.error || "Failed to get DLL stats"}</div>
              ) : (
                <div>
                  <Field label="DLL Path">
                    <Focusable
                      onClick={() => dllStats.dll_path && copyToClipboard(dllStats.dll_path)}
                      onActivate={() => dllStats.dll_path && copyToClipboard(dllStats.dll_path)}
                    >
                      {dllStats.dll_path || "Not available"}
                    </Focusable>
                  </Field>
                  
                  <Field label="SHA256 Hash">
                    <Focusable
                      onClick={() => dllStats.dll_sha256 && copyToClipboard(dllStats.dll_sha256)}
                      onActivate={() => dllStats.dll_sha256 && copyToClipboard(dllStats.dll_sha256)}
                    >
                      {dllStats.dll_sha256 ? formatSHA256(dllStats.dll_sha256) : "Not available"}
                    </Focusable>
                  </Field>
                  
                  {dllStats.dll_source && (
                    <Field label="Detection Source">
                      <div>{dllStats.dll_source}</div>
                    </Field>
                  )}
                </div>
              )}
            </>
          )}

          {/* Launch Script Section */}
          {scriptContent && (
            <Field label="Launch Script">
              {!scriptContent.success ? (
                <div>Script not found: {scriptContent.error}</div>
              ) : (
                <div>
                  <div style={{ marginBottom: "8px", fontSize: "0.9em", opacity: 0.8 }}>
                    Path: {scriptContent.path}
                  </div>
                  <Focusable
                    onClick={() => scriptContent.content && copyToClipboard(scriptContent.content)}
                    onActivate={() => scriptContent.content && copyToClipboard(scriptContent.content)}
                  >
                    <pre style={{ 
                      background: "rgba(255, 255, 255, 0.1)", 
                      padding: "8px", 
                      borderRadius: "4px", 
                      fontSize: "0.8em",
                      whiteSpace: "pre-wrap",
                      overflow: "auto",
                      maxHeight: "150px"
                    }}>
                      {scriptContent.content || "No content"}
                    </pre>
                  </Focusable>
                </div>
              )}
            </Field>
          )}

          {/* Config File Section */}
          {configContent && (
            <Field label="Configuration File">
              {!configContent.success ? (
                <div>Config not found: {configContent.error}</div>
              ) : (
                <div>
                  <div style={{ marginBottom: "8px", fontSize: "0.9em", opacity: 0.8 }}>
                    Path: {configContent.path}
                  </div>
                  <Focusable
                    onClick={() => configContent.content && copyToClipboard(configContent.content)}
                    onActivate={() => configContent.content && copyToClipboard(configContent.content)}
                  >
                    <pre style={{ 
                      background: "rgba(255, 255, 255, 0.1)", 
                      padding: "8px", 
                      borderRadius: "4px", 
                      fontSize: "0.8em",
                      whiteSpace: "pre-wrap",
                      overflow: "auto",
                      maxHeight: "200px"
                    }}>
                      {configContent.content || "No content"}
                    </pre>
                  </Focusable>
                </div>
              )}
            </Field>
          )}

          {/* Process Information Section */}
          <Field label="Process Information">
            {processLoading ? (
              <div>Loading process info...</div>
            ) : (
              <>
                {/* Last Launch Info */}
                {launchInfo && (
                  <div style={{ marginBottom: "12px" }}>
                    <div style={{ fontSize: "0.9em", fontWeight: "bold", marginBottom: "4px" }}>
                      Last Launch Information:
                    </div>
                    {launchInfo.success ? (
                      <>
                        {launchInfo.last_basename && (
                          <div style={{ fontSize: "0.8em", marginBottom: "4px" }}>
                            <strong>Last Game:</strong> {launchInfo.last_basename}
                          </div>
                        )}
                        {launchInfo.recent_basenames && launchInfo.recent_basenames.length > 0 && (
                          <div style={{ fontSize: "0.8em", marginBottom: "4px" }}>
                            <strong>Recent Games:</strong> {launchInfo.recent_basenames.join(", ")}
                          </div>
                        )}
                        {launchInfo.last_launch_command && (
                          <div style={{ fontSize: "0.8em" }}>
                            <strong>Last Command:</strong>
                            <div style={{ 
                              background: "rgba(255, 255, 255, 0.1)", 
                              padding: "4px", 
                              marginTop: "2px",
                              borderRadius: "2px",
                              fontSize: "0.7em",
                              wordBreak: "break-all",
                              maxHeight: "60px",
                              overflow: "auto"
                            }}>
                              {launchInfo.last_launch_command}
                            </div>
                          </div>
                        )}
                      </>
                    ) : (
                      <div style={{ fontSize: "0.8em", color: "#ff6b6b" }}>
                        {launchInfo.error || "No launch information available"}
                      </div>
                    )}
                  </div>
                )}

                {/* Running Processes */}
                {processInfo && (
                  <div>
                    <div style={{ fontSize: "0.9em", fontWeight: "bold", marginBottom: "4px" }}>
                      LSFG Processes:
                    </div>
                    {processInfo.success ? (
                      <>
                        {processInfo.lsfg_processes && processInfo.lsfg_processes.length > 0 ? (
                          <div style={{ 
                            background: "rgba(255, 255, 255, 0.1)", 
                            padding: "8px", 
                            borderRadius: "4px",
                            fontSize: "0.7em",
                            maxHeight: "100px",
                            overflow: "auto"
                          }}>
                            {processInfo.lsfg_processes.map((proc, index) => (
                              <div key={index} style={{ marginBottom: "4px" }}>
                                PID {proc.pid}: {proc.comm} ({proc.args.substring(0, 80)}...)
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div style={{ fontSize: "0.8em", color: "#ffa500" }}>
                            No LSFG processes currently running
                          </div>
                        )}
                        <div style={{ fontSize: "0.7em", marginTop: "4px", opacity: 0.7 }}>
                          Total game processes found: {processInfo.total_processes || 0}
                        </div>
                      </>
                    ) : (
                      <div style={{ fontSize: "0.8em", color: "#ff6b6b" }}>
                        {processInfo.error || "Failed to get process information"}
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </Field>
        </>
      )}
    </ModalRoot>
  );
}
