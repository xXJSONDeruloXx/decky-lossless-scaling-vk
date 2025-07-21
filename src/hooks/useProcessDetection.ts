import { useState, useEffect, useCallback } from "react";
import { 
  getRunningProcesses, 
  getLastLaunchInfo, 
  parseLaunchCommandBasename,
  type ProcessInfoResult,
  type LaunchInfoResult,
  type ParseBasenameResult
} from "../api/lsfgApi";

export function useProcessDetection() {
  const [processInfo, setProcessInfo] = useState<ProcessInfoResult | null>(null);
  const [launchInfo, setLaunchInfo] = useState<LaunchInfoResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadProcessInfo = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [processResult, launchResult] = await Promise.all([
        getRunningProcesses(),
        getLastLaunchInfo()
      ]);
      
      setProcessInfo(processResult);
      setLaunchInfo(launchResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load process info");
    } finally {
      setLoading(false);
    }
  }, []);

  const parseBasename = useCallback(async (launchCommand: string): Promise<ParseBasenameResult> => {
    return await parseLaunchCommandBasename(launchCommand);
  }, []);

  useEffect(() => {
    loadProcessInfo();
  }, [loadProcessInfo]);

  return {
    processInfo,
    launchInfo,
    loading,
    error,
    loadProcessInfo,
    parseBasename
  };
}
