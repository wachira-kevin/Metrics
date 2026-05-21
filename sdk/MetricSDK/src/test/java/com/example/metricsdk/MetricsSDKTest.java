package com.example.metricsdk;

import static org.junit.Assert.assertSame;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertFalse;

import org.junit.Test;

public class MetricsSDKTest {

    @Test
    public void isInitialized_beforeInit_returnsFalse() {
        assertFalse(MetricsSDK.isInitialized());
    }

    @Test
    public void getCollector_beforeInit_throwsException() {
        IllegalStateException exception = assertThrows(
                IllegalStateException.class,
                MetricsSDK::getCollector
        );

        assertSame("MetricsSDK.init() must be called first", exception.getMessage());
    }

    @Test
    public void getSessionManager_beforeInit_throwsException() {
        IllegalStateException exception = assertThrows(
                IllegalStateException.class,
                MetricsSDK::getSessionManager
        );

        assertSame("MetricsSDK.init() must be called first", exception.getMessage());
    }
}