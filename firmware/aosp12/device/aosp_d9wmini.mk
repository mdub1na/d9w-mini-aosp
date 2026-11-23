# Configuration preparation only. No image target is enabled.
$(call inherit-product, $(SRC_TARGET_DIR)/product/base_system.mk)
$(call inherit-product, device/flixtone/d9wmini_aosp/device.mk)

PRODUCT_NAME := aosp_d9wmini
PRODUCT_DEVICE := d9wmini_aosp
PRODUCT_BRAND := Flixtone
PRODUCT_MODEL := D9W Mini AOSP preparation
PRODUCT_MANUFACTURER := Flixtone
PRODUCT_CHARACTERISTICS := tv

# Shipping API/FCM history is unresolved. Do not invent launch compliance.
# r34 derives VINTF/linker/sepolicy requirements from this when shipping API is
# unknown. Request the observed Treble contract; do not waive its validation.
PRODUCT_FULL_TREBLE_OVERRIDE := true
PRODUCT_USE_DYNAMIC_PARTITIONS := false
PRODUCT_RETROFIT_DYNAMIC_PARTITIONS := false
PRODUCT_BUILD_SUPER_PARTITION := false
PRODUCT_BUILD_SUPER_EMPTY_IMAGE := false

# Enable only System in a later reviewed build after source/OEM integration.
PRODUCT_BUILD_SYSTEM_IMAGE := false
PRODUCT_BUILD_SYSTEM_OTHER_IMAGE := false
PRODUCT_BUILD_SYSTEM_EXT_IMAGE := false
PRODUCT_BUILD_PRODUCT_IMAGE := false
PRODUCT_BUILD_VENDOR_IMAGE := false
PRODUCT_BUILD_ODM_IMAGE := false
PRODUCT_BUILD_VENDOR_DLKM_IMAGE := false
PRODUCT_BUILD_ODM_DLKM_IMAGE := false
PRODUCT_BUILD_BOOT_IMAGE := false
PRODUCT_BUILD_VENDOR_BOOT_IMAGE := false
PRODUCT_BUILD_RECOVERY_IMAGE := false
PRODUCT_BUILD_RAMDISK_IMAGE := false
PRODUCT_BUILD_USERDATA_IMAGE := false
PRODUCT_BUILD_CACHE_IMAGE := false
PRODUCT_BUILD_VBMETA_IMAGE := false
