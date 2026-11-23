# Stock ABI: ARM32 userspace with the 64-bit Binder transaction layout.
TARGET_ARCH := arm
TARGET_ARCH_VARIANT := armv7-a-neon
TARGET_CPU_ABI := armeabi-v7a
TARGET_CPU_ABI2 := armeabi
TARGET_CPU_VARIANT := generic
TARGET_USES_64_BIT_BINDER := true
TARGET_BOARD_PLATFORM := bigfish
TARGET_BOOTLOADER_BOARD_NAME := bigfish

# This preparation neither builds nor packages a kernel, bootloader or recovery.
TARGET_NO_KERNEL := true
TARGET_NO_BOOTLOADER := true
TARGET_NO_RADIOIMAGE := true
TARGET_NO_RECOVERY := true

# Normal stock boot mounts mmcblk0p20 as / and uses init=/init.
# Android 12 r34 still supports this flag for non-dynamic devices.
BOARD_BUILD_SYSTEM_ROOT_IMAGE := true
BOARD_SYSTEMIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_SYSTEMIMAGE_PARTITION_SIZE := 1862270976
TARGET_USERIMAGES_USE_EXT4 := true
TARGET_COPY_OUT_VENDOR := vendor
TARGET_COPY_OUT_SYSTEM_EXT := system/system_ext
TARGET_COPY_OUT_PRODUCT := system/product

# Use the platform implementation for stock Vendor's VNDK 31 on Android 12.
ifeq ($(PLATFORM_SDK_VERSION)/$(PLATFORM_VNDK_VERSION),31/31)
BOARD_VNDK_VERSION := current
else ifeq ($(PLATFORM_SDK_VERSION)/$(PLATFORM_VNDK_VERSION),32/32)
# The retained Android 12.1 reference supplies the VNDK 31 snapshot.
ifneq ($(PRODUCT_BUILD_SYSTEM_IMAGE),false)
$(error The API 32 reference is only supported for configuration checks)
endif
BOARD_VNDK_VERSION := 31
else
$(error Unsupported D9W platform SDK/VNDK: $(PLATFORM_SDK_VERSION)/$(PLATFORM_VNDK_VERSION))
endif
