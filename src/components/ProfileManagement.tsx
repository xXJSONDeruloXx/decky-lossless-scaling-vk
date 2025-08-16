import { useState, useEffect } from "react";
import {
  PanelSection,
  PanelSectionRow,
  Dropdown,
  DropdownOption,
  showModal,
  ConfirmModal,
  Field,
  DialogButton,
  ButtonItem,
  ModalRoot,
  TextField,
  Focusable
} from "@decky/ui";
import { 
  getProfiles, 
  createProfile, 
  deleteProfile, 
  renameProfile, 
  setCurrentProfile,
  ProfilesResult,
  ProfileResult
} from "../api/lsfgApi";
import { showSuccessToast, showErrorToast } from "../utils/toastUtils";

interface ProfileManagementProps {
  currentProfile?: string;
  onProfileChange?: (profileName: string) => void;
}

interface TextInputModalProps {
  title: string;
  description: string;
  defaultValue?: string;
  okText?: string;
  cancelText?: string;
  onOK: (value: string) => void;
  closeModal?: () => void;
}

function TextInputModal({ 
  title, 
  description, 
  defaultValue = "", 
  okText = "OK", 
  cancelText = "Cancel", 
  onOK, 
  closeModal 
}: TextInputModalProps) {
  const [value, setValue] = useState(defaultValue);

  const handleOK = () => {
    if (value.trim()) {
      onOK(value);
      closeModal?.();
    }
  };

  return (
    <ModalRoot>
      <div style={{ padding: "16px", minWidth: "400px" }}>
        <h2 style={{ marginBottom: "16px" }}>{title}</h2>
        <p style={{ marginBottom: "24px" }}>{description}</p>
        
        <div style={{ marginBottom: "24px" }}>
          <Field 
            label="Name"
            childrenLayout="below"
            childrenContainerWidth="max"
          >
            <TextField
              value={value}
              onChange={(e) => setValue(e?.target?.value || "")}
              style={{ width: "100%" }}
            />
          </Field>
        </div>
        
        <Focusable
          style={{
            display: "flex",
            justifyContent: "flex-end",
            gap: "8px",
            marginTop: "16px"
          }}
          flow-children="horizontal"
        >
          <DialogButton onClick={closeModal}>
            {cancelText}
          </DialogButton>
          <DialogButton 
            onClick={handleOK} 
            disabled={!value.trim()}
          >
            {okText}
          </DialogButton>
        </Focusable>
      </div>
    </ModalRoot>
  );
}

interface ProfileManagementProps {
  currentProfile?: string;
  onProfileChange?: (profileName: string) => void;
}

export function ProfileManagement({ currentProfile, onProfileChange }: ProfileManagementProps) {
  const [profiles, setProfiles] = useState<string[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<string>(currentProfile || "decky-lsfg-vk");
  const [isLoading, setIsLoading] = useState(false);

  // Load profiles on component mount
  useEffect(() => {
    loadProfiles();
  }, []);

  // Update selected profile when prop changes
  useEffect(() => {
    if (currentProfile) {
      setSelectedProfile(currentProfile);
    }
  }, [currentProfile]);

  const loadProfiles = async () => {
    try {
      const result: ProfilesResult = await getProfiles();
      if (result.success && result.profiles) {
        setProfiles(result.profiles);
        if (result.current_profile) {
          setSelectedProfile(result.current_profile);
        }
      } else {
        console.error("Failed to load profiles:", result.error);
        showErrorToast("Failed to load profiles", result.error || "Unknown error");
      }
    } catch (error) {
      console.error("Error loading profiles:", error);
      showErrorToast("Error loading profiles", String(error));
    }
  };

  const handleProfileChange = async (profileName: string) => {
    setIsLoading(true);
    try {
      const result: ProfileResult = await setCurrentProfile(profileName);
      if (result.success) {
        setSelectedProfile(profileName);
        showSuccessToast("Profile switched", `Switched to profile: ${profileName}`);
        onProfileChange?.(profileName);
      } else {
        console.error("Failed to switch profile:", result.error);
        showErrorToast("Failed to switch profile", result.error || "Unknown error");
      }
    } catch (error) {
      console.error("Error switching profile:", error);
      showErrorToast("Error switching profile", String(error));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateProfile = () => {
    showModal(
      <TextInputModal
        title="Create New Profile"
        description="Enter a name for the new profile. The current profile's settings will be copied."
        okText="Create"
        cancelText="Cancel"
        onOK={(name: string) => {
          if (name.trim()) {
            createNewProfile(name.trim());
          }
        }}
      />
    );
  };

  const createNewProfile = async (profileName: string) => {
    setIsLoading(true);
    try {
      const result: ProfileResult = await createProfile(profileName, selectedProfile);
      if (result.success) {
        showSuccessToast("Profile created", `Created profile: ${profileName}`);
        await loadProfiles();
        // Automatically switch to the newly created profile
        await handleProfileChange(profileName);
      } else {
        console.error("Failed to create profile:", result.error);
        showErrorToast("Failed to create profile", result.error || "Unknown error");
      }
    } catch (error) {
      console.error("Error creating profile:", error);
      showErrorToast("Error creating profile", String(error));
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteProfile = () => {
    if (selectedProfile === "decky-lsfg-vk") {
      showErrorToast("Cannot delete default profile", "The default profile cannot be deleted");
      return;
    }

    showModal(
      <ConfirmModal
        strTitle="Delete Profile"
        strDescription={`Are you sure you want to delete the profile "${selectedProfile}"? This action cannot be undone.`}
        strOKButtonText="Delete"
        strCancelButtonText="Cancel"
        onOK={() => deleteSelectedProfile()}
      />
    );
  };

  const deleteSelectedProfile = async () => {
    setIsLoading(true);
    try {
      const result: ProfileResult = await deleteProfile(selectedProfile);
      if (result.success) {
        showSuccessToast("Profile deleted", `Deleted profile: ${selectedProfile}`);
        await loadProfiles();
        // If we deleted the current profile, it should have switched to default
        setSelectedProfile("decky-lsfg-vk");
        onProfileChange?.("decky-lsfg-vk");
      } else {
        console.error("Failed to delete profile:", result.error);
        showErrorToast("Failed to delete profile", result.error || "Unknown error");
      }
    } catch (error) {
      console.error("Error deleting profile:", error);
      showErrorToast("Error deleting profile", String(error));
    } finally {
      setIsLoading(false);
    }
  };

  const handleDropdownChange = (option: DropdownOption) => {
    if (option.data === "__NEW_PROFILE__") {
      handleCreateProfile();
    } else {
      handleProfileChange(option.data);
    }
  };

  const handleRenameProfile = () => {
    if (selectedProfile === "decky-lsfg-vk") {
      showErrorToast("Cannot rename default profile", "The default profile cannot be renamed");
      return;
    }

    showModal(
      <TextInputModal
        title="Rename Profile"
        description={`Enter a new name for the profile "${selectedProfile}".`}
        defaultValue={selectedProfile}
        okText="Rename"
        cancelText="Cancel"
        onOK={(newName: string) => {
          if (newName.trim() && newName.trim() !== selectedProfile) {
            renameSelectedProfile(newName.trim());
          }
        }}
      />
    );
  };

  const renameSelectedProfile = async (newName: string) => {
    setIsLoading(true);
    try {
      const result: ProfileResult = await renameProfile(selectedProfile, newName);
      if (result.success) {
        showSuccessToast("Profile renamed", `Renamed profile to: ${newName}`);
        await loadProfiles();
        setSelectedProfile(newName);
        onProfileChange?.(newName);
      } else {
        console.error("Failed to rename profile:", result.error);
        showErrorToast("Failed to rename profile", result.error || "Unknown error");
      }
    } catch (error) {
      console.error("Error renaming profile:", error);
      showErrorToast("Error renaming profile", String(error));
    } finally {
      setIsLoading(false);
    }
  };

  const profileOptions: DropdownOption[] = [
    ...profiles.map((profile: string) => ({
      data: profile,
      label: profile === "decky-lsfg-vk" ? "Default" : profile
    })),
    {
      data: "__NEW_PROFILE__",
      label: "New Profile"
    }
  ];

  return (
    <PanelSection title="Select Profile">
      <PanelSectionRow>
        <Field
          label=""
          childrenLayout="below"
          childrenContainerWidth="max"
        >
          <Dropdown
            rgOptions={profileOptions}
            selectedOption={selectedProfile}
            onChange={handleDropdownChange}
            disabled={isLoading}
          />
        </Field>
      </PanelSectionRow>
      
      <PanelSectionRow>
        <ButtonItem
          layout="below"
          onClick={handleRenameProfile}
          disabled={isLoading || selectedProfile === "decky-lsfg-vk"}
        >
          Rename
        </ButtonItem>
      </PanelSectionRow>
      
      <PanelSectionRow>
        <ButtonItem
          layout="below"
          onClick={handleDeleteProfile}
          disabled={isLoading || selectedProfile === "decky-lsfg-vk"}
        >
          Delete
        </ButtonItem>
      </PanelSectionRow>
    </PanelSection>
  );
}
