#!/bin/bash

# Original script credit: https://github.com/psygreg/lsfg-vk/blob/develop/flatpak-enabler.sh


# set up function
flatpak_enabler () {

    # initialize variables with locations
    DLL_FIND=$(find / -name Lossless.dll 2>/dev/null | head -n 1)
    DLL_ABSOLUTE_PATH=$(dirname "$(realpath "$DLL_FIND")")
    ESCAPED_DLL_PATH=$(printf '%s\n' "$DLL_ABSOLUTE_PATH" | sed 's/[&/\]/\\&/g')
    CONF_LOC="${HOME}/.config/lsfg-vk/conf.toml"
    # check if config exists, and if not, create it


    Defines the flatpak_enabler Function

All main logic is inside this function.
Finds the DLL Location

Searches the filesystem for Lossless.dll.
Gets its absolute directory path.
Escapes special characters for use in sed.
Config File Setup

Sets the config file location (~/.config/lsfg-vk/conf.toml).
If the config file doesn’t exist:
Creates the config directory.
generates from the way we do it with our install lsfg function in the plugin proper
Moves it to the config directory.

Uses sed to update the DLL path in the config file.
Flatpak App List

Defines a list of Flatpak app IDs to process.
Iterates Over Flatpak Apps

For each app:
Checks if it’s installed (flatpak list | grep -q).
Sets up app-specific directories for symlinks.
Flatpak Overrides


Else, if installed via script (checks for files in ~/.local):
Sets Flatpak overrides for those locations.
Adds DLL path override for non-Steam apps.
Creates Symlinks

Ensures necessary directories exist in the Flatpak app’s sandbox.
Creates symlinks to the required files and config, depending on installation method.
Success Message

Prints a message for each app where usage is enabled.
Runs the Function if Flatpak is Installed

Checks if flatpak is available.
Runs flatpak_enabler if so.



#!/bin/bash
# set up function
flatpak_enabler () {

    # initialize variables with locations
    DLL_FIND=$(find / -name Lossless.dll 2>/dev/null | head -n 1)
    DLL_ABSOLUTE_PATH=$(dirname "$(realpath "$DLL_FIND")")
    ESCAPED_DLL_PATH=$(printf '%s\n' "$DLL_ABSOLUTE_PATH" | sed 's/[&/\]/\\&/g')

    fi
    # register dll location in config file
    sed -i -E "s|^# dll = \".*\"|dll = \"$ESCAPED_DLL_PATH\"|" ${HOME}/.config/lsfg-vk/conf.toml
    # apply flatpak overrides -- Lutris has permission for /home, so won't need any, but still needs the symlinks
    _flatpaks=(com.heroicgameslauncher.hgl com.valvesoftware.Steam net.lutris.Lutris org.prismlauncher.PrismLauncher com.atlauncher.ATLauncher org.polymc.PolyMC com.mojang.Minecraft)
    for flat in "${_flatpaks[@]}"; do
        if flatpak list | grep -q "$flat"; then
            APP_DIR="$HOME/.var/app/$flat"
            # overrides for AUR/CachyOS packages
            if pacman -Qi lsfg-vk 2>/dev/null 1>&2; then
                flatpak override \
                  --user \
                  --filesystem="/usr/lib/liblsfg-vk.so:ro" \
                  --filesystem="/etc/vulkan/implicit_layer.d/VkLayer_LS_frame_generation.json:ro" \
                  --filesystem="$HOME/.config/lsfg-vk:ro" \
                  "$flat"
                # only set override with dll path if not Steam
                if [ "$flat" != "com.valvesoftware.Steam" ]; then
                    flatpak override --user --filesystem="$DLL_ABSOLUTE_PATH:ro"
                fi
            # overrides for install script
            elif [ -f "$HOME/.local/lib/liblsfg-vk.so" ] && [ -f "$HOME/.local/share/vulkan/implicit_layer.d/VkLayer_LS_frame_generation.json" ]; then
                flatpak override \
                  --user \
                  --filesystem="$HOME/.local/lib/liblsfg-vk.so:ro" \
                  --filesystem="$HOME/.local/share/vulkan/implicit_layer.d/VkLayer_LS_frame_generation.json:ro" \
                  --filesystem="$HOME/.config/lsfg-vk:ro" \
                  "$flat"
                if [ "$flat" != "com.valvesoftware.Steam" ]; then
                    flatpak override --user --filesystem="$DLL_ABSOLUTE_PATH:ro"
                fi
            fi
            # set up directories for symlinks
            mkdir -p "$APP_DIR/lib"
            mkdir -p "$APP_DIR/config/vulkan/implicit_layer.d/"
            mkdir -p "$APP_DIR/config/lsfg-vk/"
            # symlinks for AUR/CachyOS packages
            if pacman -Qi lsfg-vk 2>/dev/null 1>&2; then
                ln -sf "/usr/lib/liblsfg-vk.so" "$APP_DIR/lib/liblsfg-vk.so"
                ln -sf "/etc/vulkan/implicit_layer.d/VkLayer_LS_frame_generation.json" "$APP_DIR/config/vulkan/implicit_layer.d/VkLayer_LS_frame_generation.json"
                ln -sf "$HOME/.config/lsfg-vk/conf.toml" "$APP_DIR/config/lsfg-vk/conf.toml"
            # symlinks for installation script -- elif so it only creates the symlinks if files exist at the expected locations
            elif [ -f "$HOME/.local/lib/liblsfg-vk.so" ] && [ -f "$HOME/.local/share/vulkan/implicit_layer.d/VkLayer_LS_frame_generation.json" ]; then
                ln -sf "$HOME/.local/lib/liblsfg-vk.so" "$APP_DIR/lib/liblsfg-vk.so"
                ln -sf "$HOME/.local/share/vulkan/implicit_layer.d/VkLayer_LS_frame_generation.json" "$APP_DIR/config/vulkan/implicit_layer.d/VkLayer_LS_frame_generation.json"
                ln -sf "$HOME/.config/lsfg-vk/conf.toml" "$APP_DIR/config/lsfg-vk/conf.toml"
            fi
            echo "Usage enabled successfully for $flat."
        fi
    done

}

# run function only if flatpak is present
if command -v flatpak &> /dev/null; then
    flatpak_enabler
fi