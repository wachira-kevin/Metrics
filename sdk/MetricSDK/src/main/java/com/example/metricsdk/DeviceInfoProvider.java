package com.example.metricsdk;

import android.content.Context;
import android.provider.Settings;

/**
 * Utility class responsible for providing device-related information.
 * This class is designed to offer methods that assist in retrieving device-specific
 * details, such as unique device identifiers.
 *
 * Note that this class cannot be instantiated as it contains only static methods.
 */
class DeviceInfoProvider {

    /**
     * Private constructor to prevent instantiation of the {@code DeviceInfoProvider} class.
     *
     * This class is intended to be used as a utility class with static methods only.
     * By design, instantiation of this class is restricted to enforce its static utility nature.
     */
    private DeviceInfoProvider() {
    }

    /**
     * Retrieves the unique device identifier (Android ID) for the current device.
     *
     * The Android ID is a 64-bit alphanumeric string that is generated when the device
     * is first set up. It serves as a unique identifier for the device. If the Android ID
     * is unavailable or cannot be retrieved, this method returns "unknown".
     *
     * @param context the application context used to access the content resolver and retrieve the Android ID.
     * @return the Android ID of the device, or "unknown" if the ID cannot be obtained.
     */
    static String getDeviceId(Context context) {
        String androidId = Settings.Secure.getString(
                context.getContentResolver(),
                Settings.Secure.ANDROID_ID
        );

        if (androidId == null || androidId.trim().isEmpty()) {
            return "unknown";
        }

        return androidId;
    }
}