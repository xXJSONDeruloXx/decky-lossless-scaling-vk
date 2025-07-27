import { FC, useState, useEffect } from 'react';
import {
  ModalRoot,
  DialogBody,
  DialogHeader,
  DialogControlsSection,
  DialogControlsSectionHeader,
  ButtonItem,
  PanelSectionRow,
  Field,
  Toggle,
  Spinner,
  Focusable,
  showModal,
  ConfirmModal
} from '@decky/ui';
import { FaCheck, FaTimes, FaDownload, FaTrash, FaCog } from 'react-icons/fa';
import { 
  checkFlatpakExtensionStatus, 
  installFlatpakExtension, 
  uninstallFlatpakExtension,
  getFlatpakApps,
  setFlatpakAppOverride,
  removeFlatpakAppOverride,
  FlatpakExtensionStatus,
  FlatpakApp,
  FlatpakAppInfo
} from '../api/lsfgApi';

interface FlatpaksModalProps {
  closeModal?: () => void;
}

const FlatpaksModal: FC<FlatpaksModalProps> = ({ closeModal }) => {
  const [extensionStatus, setExtensionStatus] = useState<FlatpakExtensionStatus | null>(null);
  const [flatpakApps, setFlatpakApps] = useState<FlatpakAppInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [operationInProgress, setOperationInProgress] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statusResult, appsResult] = await Promise.all([
        checkFlatpakExtensionStatus(),
        getFlatpakApps()
      ]);
      
      setExtensionStatus(statusResult);
      setFlatpakApps(appsResult);
    } catch (error) {
      console.error('Error loading Flatpak data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleExtensionOperation = async (operation: 'install' | 'uninstall', version: string) => {
    const operationId = `${operation}-${version}`;
    setOperationInProgress(operationId);
    
    try {
      const result = operation === 'install' 
        ? await installFlatpakExtension(version)
        : await uninstallFlatpakExtension(version);
      
      if (result.success) {
        // Reload status after operation
        const newStatus = await checkFlatpakExtensionStatus();
        setExtensionStatus(newStatus);
      }
    } catch (error) {
      console.error(`Error ${operation}ing extension:`, error);
    } finally {
      setOperationInProgress(null);
    }
  };

  const handleAppOverrideToggle = async (app: FlatpakApp) => {
    const hasOverrides = app.has_filesystem_override && app.has_env_override;
    const operationId = `app-${app.app_id}`;
    setOperationInProgress(operationId);
    
    try {
      const result = hasOverrides 
        ? await removeFlatpakAppOverride(app.app_id)
        : await setFlatpakAppOverride(app.app_id);
      
      if (result.success) {
        // Reload apps data after operation
        const newApps = await getFlatpakApps();
        setFlatpakApps(newApps);
      }
    } catch (error) {
      console.error('Error toggling app override:', error);
    } finally {
      setOperationInProgress(null);
    }
  };

  const confirmOperation = (operation: () => void, title: string, description: string) => {
    showModal(
      <ConfirmModal
        strTitle={title}
        strDescription={description}
        onOK={operation}
        onCancel={() => {}}
      />
    );
  };

  if (loading) {
    return (
      <ModalRoot closeModal={closeModal}>
        <DialogHeader>Flatpak Extensions</DialogHeader>
        <DialogBody>
          <div style={{ display: 'flex', justifyContent: 'center', padding: '20px' }}>
            <Spinner />
          </div>
        </DialogBody>
      </ModalRoot>
    );
  }

  return (
    <ModalRoot closeModal={closeModal}>
      <DialogHeader>Flatpak Extensions</DialogHeader>
      <DialogBody>
        <Focusable>
          {/* Extension Status Section */}
          <DialogControlsSection>
            <DialogControlsSectionHeader>Runtime Extensions</DialogControlsSectionHeader>
            
            {extensionStatus && extensionStatus.success ? (
              <>
                {/* 23.08 Runtime */}
                <PanelSectionRow>
                  <Field 
                    label="Runtime 23.08"
                    description={extensionStatus.installed_23_08 ? "Installed" : "Not installed"}
                    icon={extensionStatus.installed_23_08 ? <FaCheck style={{color: 'green'}} /> : <FaTimes style={{color: 'red'}} />}
                  >
                    <ButtonItem
                      layout="below"
                      onClick={() => {
                        const operation = extensionStatus.installed_23_08 ? 'uninstall' : 'install';
                        const action = () => handleExtensionOperation(operation, '23.08');
                        
                        if (operation === 'uninstall') {
                          confirmOperation(
                            action,
                            'Uninstall Runtime Extension',
                            'Are you sure you want to uninstall the 23.08 runtime extension?'
                          );
                        } else {
                          action();
                        }
                      }}
                      disabled={operationInProgress === 'install-23.08' || operationInProgress === 'uninstall-23.08'}
                    >
                      {operationInProgress === 'install-23.08' || operationInProgress === 'uninstall-23.08' ? (
                        <Spinner />
                      ) : extensionStatus.installed_23_08 ? (
                        <>
                          <FaTrash /> Uninstall
                        </>
                      ) : (
                        <>
                          <FaDownload /> Install
                        </>
                      )}
                    </ButtonItem>
                  </Field>
                </PanelSectionRow>

                {/* 24.08 Runtime */}
                <PanelSectionRow>
                  <Field 
                    label="Runtime 24.08"
                    description={extensionStatus.installed_24_08 ? "Installed" : "Not installed"}
                    icon={extensionStatus.installed_24_08 ? <FaCheck style={{color: 'green'}} /> : <FaTimes style={{color: 'red'}} />}
                  >
                    <ButtonItem
                      layout="below"
                      onClick={() => {
                        const operation = extensionStatus.installed_24_08 ? 'uninstall' : 'install';
                        const action = () => handleExtensionOperation(operation, '24.08');
                        
                        if (operation === 'uninstall') {
                          confirmOperation(
                            action,
                            'Uninstall Runtime Extension',
                            'Are you sure you want to uninstall the 24.08 runtime extension?'
                          );
                        } else {
                          action();
                        }
                      }}
                      disabled={operationInProgress === 'install-24.08' || operationInProgress === 'uninstall-24.08'}
                    >
                      {operationInProgress === 'install-24.08' || operationInProgress === 'uninstall-24.08' ? (
                        <Spinner />
                      ) : extensionStatus.installed_24_08 ? (
                        <>
                          <FaTrash /> Uninstall
                        </>
                      ) : (
                        <>
                          <FaDownload /> Install
                        </>
                      )}
                    </ButtonItem>
                  </Field>
                </PanelSectionRow>
              </>
            ) : (
              <PanelSectionRow>
                <Field 
                  label="Error"
                  description={extensionStatus?.error || 'Failed to check extension status'}
                  icon={<FaTimes style={{color: 'red'}} />}
                />
              </PanelSectionRow>
            )}
          </DialogControlsSection>

          {/* Flatpak Apps Section */}
          <DialogControlsSection>
            <DialogControlsSectionHeader>Flatpak Applications</DialogControlsSectionHeader>
            
            {flatpakApps && flatpakApps.success ? (
              flatpakApps.apps.length > 0 ? (
                flatpakApps.apps.map((app) => {
                  const hasOverrides = app.has_filesystem_override && app.has_env_override;
                  const partialOverrides = app.has_filesystem_override || app.has_env_override;
                  
                  let statusColor = 'red';
                  let statusText = 'No overrides';
                  
                  if (hasOverrides) {
                    statusColor = 'green';
                    statusText = 'Configured';
                  } else if (partialOverrides) {
                    statusColor = 'orange';
                    statusText = 'Partial';
                  }

                  return (
                    <PanelSectionRow key={app.app_id}>
                      <Field 
                        label={app.app_name || app.app_id}
                        description={`${app.app_id} - ${statusText}`}
                        icon={<FaCog style={{color: statusColor}} />}
                      >
                        <Toggle
                          value={hasOverrides}
                          onChange={() => handleAppOverrideToggle(app)}
                          disabled={operationInProgress === `app-${app.app_id}`}
                        />
                      </Field>
                    </PanelSectionRow>
                  );
                })
              ) : (
                <PanelSectionRow>
                  <Field 
                    label="No Flatpak Apps Found"
                    description="No Flatpak applications are currently installed"
                  />
                </PanelSectionRow>
              )
            ) : (
              <PanelSectionRow>
                <Field 
                  label="Error"
                  description={flatpakApps?.error || 'Failed to load Flatpak applications'}
                  icon={<FaTimes style={{color: 'red'}} />}
                />
              </PanelSectionRow>
            )}
          </DialogControlsSection>
        </Focusable>
      </DialogBody>
    </ModalRoot>
  );
};

export default FlatpaksModal;
