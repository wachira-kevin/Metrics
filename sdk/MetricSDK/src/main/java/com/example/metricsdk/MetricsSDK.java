package com.example.metricsdk;

import android.app.Application;
import android.content.Context;
import android.os.SystemClock;
import com.example.metricsdk.internal.AppLifecycleTracker;
import com.example.metricsdk.internal.SessionManager;

/**
 * The {@code MetricsSDK} class serves as the entry point for initializing and accessing
 * the metrics collection functionality within an application. It provides methods
 * to initialize the SDK and retrieve the {@link MetricsCollector} instance.
 *
 * This class is designed to be thread-safe and guarantees that the SDK is initialized
 * only once. It is implemented as a utility class with no instantiation allowed.
 */
public final class MetricsSDK {

    private static volatile boolean initialized = false;
    private static MetricsCollector collector;
    private static SessionManager sessionManager;
    private static AppLifecycleTracker appLifecycleTracker;

    /**
     * Private constructor for the {@code MetricsSDK} class to prevent instantiation.
     *
     * This class is designed as a utility class and provides static methods
     * to initialize and access the metrics collection functionalities. The
     * private constructor ensures that no instances of this class can be created,
     * enforcing its purpose as a static utility class.
     */
    private MetricsSDK() {
    }

    /**
     * Initializes the MetricsSDK with the provided application context, API URL, and application token.
     * This method ensures that the SDK is initialized only once, even when accessed from multiple threads.
     * The method must be called before using other functionalities of the MetricsSDK.
     *
     * @param context  the application context used for SDK initialization
     * @param apiUrl   the API URL used by the MetricsCollector for metrics reporting
     * @param appToken the application token used to authenticate API requests
     */
    public static void init(Context context, String apiUrl, String appToken) {
        if (initialized) {
            return;
        }

        synchronized (MetricsSDK.class) {
            if (initialized) {
                return;
            }

            Context appContext = context.getApplicationContext();

            collector = MetricsCollector.getInstance();
            collector.initialize(appContext, apiUrl, appToken);

            sessionManager = new SessionManager();

            if (appContext instanceof Application) {
                appLifecycleTracker = new AppLifecycleTracker(
                        collector,
                        sessionManager,
                        SystemClock.elapsedRealtime()
                );

                appLifecycleTracker.register((Application) appContext);
            }

            initialized = true;
        }
    }

    /**
     * Retrieves the instance of {@link MetricsCollector} used for collecting and reporting metrics.
     * This method can only be called after the MetricsSDK has been initialized via the {@code init} method.
     *
     * @return the instance of {@link MetricsCollector} configured during SDK initialization
     * @throws IllegalStateException if the MetricsSDK has not been initialized prior to calling this method
     */
    public static MetricsCollector getCollector() {
        if (!initialized || collector == null) {
            throw new IllegalStateException("MetricsSDK.init() must be called first");
        }

        return collector;
    }

    /**
     * Retrieves the instance of {@code SessionManager} associated with the MetricsSDK.
     * This method can only be called after the MetricsSDK has been initialized
     * using the {@code init} method.
     *
     * @return the instance of {@code SessionManager} used for managing session-related data
     * @throws IllegalStateException if the MetricsSDK has not been initialized prior to calling this method
     */
    public static SessionManager getSessionManager() {
        if (!initialized || sessionManager == null) {
            throw new IllegalStateException("MetricsSDK.init() must be called first");
        }

        return sessionManager;
    }

    /**
     * Indicates whether the MetricsSDK has been successfully initialized.
     *
     * This method allows the caller to check if the SDK is ready for use
     * without requiring additional setup or performing unnecessary operations.
     *
     * @return {@code true} if the MetricsSDK is initialized, {@code false} otherwise
     */
    public static boolean isInitialized() {
        return initialized;
    }
}