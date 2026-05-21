package com.example.metricsdk;

import static org.junit.Assert.assertEquals;

import android.content.Context;
import android.provider.Settings;

import androidx.test.core.app.ApplicationProvider;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;

@RunWith(RobolectricTestRunner.class)
public class DeviceInfoProviderTest {

    @Test
    public void getDeviceId_whenAndroidIdExists_returnsAndroidId() {
        Context context = ApplicationProvider.getApplicationContext();

        Settings.Secure.putString(
                context.getContentResolver(),
                Settings.Secure.ANDROID_ID,
                "android-id-123"
        );

        String deviceId = DeviceInfoProvider.getDeviceId(context);

        assertEquals("android-id-123", deviceId);
    }

    @Test
    public void getDeviceId_whenAndroidIdIsNull_returnsUnknown() {
        Context context = ApplicationProvider.getApplicationContext();

        Settings.Secure.putString(
                context.getContentResolver(),
                Settings.Secure.ANDROID_ID,
                null
        );

        String deviceId = DeviceInfoProvider.getDeviceId(context);

        assertEquals("unknown", deviceId);
    }

    @Test
    public void getDeviceId_whenAndroidIdIsBlank_returnsUnknown() {
        Context context = ApplicationProvider.getApplicationContext();

        Settings.Secure.putString(
                context.getContentResolver(),
                Settings.Secure.ANDROID_ID,
                "   "
        );

        String deviceId = DeviceInfoProvider.getDeviceId(context);

        assertEquals("unknown", deviceId);
    }
}