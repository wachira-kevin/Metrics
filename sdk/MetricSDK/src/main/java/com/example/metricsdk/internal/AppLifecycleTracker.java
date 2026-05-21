package com.example.metricsdk.internal;

import android.app.Activity;
import android.app.Application;
import android.os.Bundle;
import android.os.SystemClock;

import com.example.metricsdk.MetricsCollector;

import java.util.HashMap;
import java.util.Map;

/**
 * Tracks Android application and activity lifecycle events for analytics collection.
 *
 * <p>
 * This class integrates with the Android lifecycle system through
 * {@link Application.ActivityLifecycleCallbacks} and is responsible for:
 * </p>
 *
 * <ul>
 *     <li>Detecting app foreground/background transitions</li>
 *     <li>Managing session lifecycle events</li>
 *     <li>Tracking app startup duration</li>
 *     <li>Measuring screen view durations</li>
 *     <li>Triggering metric flushes when the app backgrounds</li>
 * </ul>
 *
 * <p>
 * The tracker considers the app to be in the foreground when at least one
 * activity is started, and in the background when all activities are stopped.
 * </p>
 *
 * <p>
 * Screen view duration is measured from {@code onActivityResumed()} until
 * {@code onActivityPaused()} using {@link SystemClock#elapsedRealtime()}
 * to avoid issues caused by system clock changes.
 * </p>
 */
public class AppLifecycleTracker implements Application.ActivityLifecycleCallbacks {

    /**
     * Metrics collector used for tracking analytics events.
     */
    private final MetricsCollector metricsCollector;

    /**
     * Session manager responsible for session lifecycle tracking.
     */
    private final SessionManager sessionManager;

    /**
     * Timestamp captured during SDK initialization using
     * {@link SystemClock#elapsedRealtime()}.
     *
     * <p>
     * Used to calculate app startup duration.
     * </p>
     */
    private final long sdkInitElapsedRealtimeMs;

    /**
     * Stores screen start timestamps for active activities.
     *
     * <p>
     * The key is the activity instance and the value is the timestamp
     * when the activity entered the resumed state.
     * </p>
     */
    private final Map<Activity, Long> screenStartTimes = new HashMap<>();

    /**
     * Number of currently started activities.
     *
     * <p>
     * Used to determine whether the app is in the foreground.
     * </p>
     */
    private int startedActivityCount = 0;

    /**
     * Indicates whether the application is currently in the foreground.
     */
    private boolean appInForeground = false;

    /**
     * Indicates whether the first activity has already started.
     *
     * <p>
     * Used to ensure app startup metrics are only tracked once.
     * </p>
     */
    private boolean firstActivityStarted = false;

    /**
     * Creates a new {@link AppLifecycleTracker}.
     *
     * @param metricsCollector analytics collector used for recording metrics
     * @param sessionManager session lifecycle manager
     * @param sdkInitElapsedRealtimeMs SDK initialization timestamp captured
     *                                 using {@link SystemClock#elapsedRealtime()}
     */
    public AppLifecycleTracker(
            MetricsCollector metricsCollector,
            SessionManager sessionManager,
            long sdkInitElapsedRealtimeMs
    ) {
        this.metricsCollector = metricsCollector;
        this.sessionManager = sessionManager;
        this.sdkInitElapsedRealtimeMs = sdkInitElapsedRealtimeMs;
    }

    /**
     * Registers this tracker with the application lifecycle.
     *
     * @param application target application instance
     */
    public void register(Application application) {
        application.registerActivityLifecycleCallbacks(this);
    }

    /**
     * Unregisters this tracker from the application lifecycle.
     *
     * @param application target application instance
     */
    public void unregister(Application application) {
        application.unregisterActivityLifecycleCallbacks(this);
    }

    /**
     * Called when an activity is created.
     *
     * <p>
     * No tracking is performed at this stage.
     * </p>
     *
     * @param activity created activity
     * @param savedInstanceState optional saved instance state
     */
    @Override
    public void onActivityCreated(Activity activity, Bundle savedInstanceState) {
        // No-op.
    }

    /**
     * Called when an activity enters the started state.
     *
     * <p>
     * This method is used to detect app foreground transitions.
     * When the first activity starts:
     * </p>
     *
     * <ul>
     *     <li>The app is marked as foregrounded</li>
     *     <li>The session manager is notified</li>
     *     <li>App startup duration is recorded once</li>
     * </ul>
     *
     * @param activity started activity
     */
    @Override
    public void onActivityStarted(Activity activity) {
        startedActivityCount++;

        if (!appInForeground) {
            appInForeground = true;

            long nowMs = System.currentTimeMillis();
            sessionManager.onForeground(nowMs);

            if (!firstActivityStarted) {
                firstActivityStarted = true;

                long appStartMs = Math.max(
                        0L,
                        SystemClock.elapsedRealtime() - sdkInitElapsedRealtimeMs
                );

                metricsCollector.trackAppStart(appStartMs);
            }
        }
    }

    /**
     * Called when an activity enters the resumed state.
     *
     * <p>
     * Stores the activity start timestamp for screen duration tracking.
     * </p>
     *
     * @param activity resumed activity
     */
    @Override
    public void onActivityResumed(Activity activity) {
        screenStartTimes.put(activity, SystemClock.elapsedRealtime());
    }

    /**
     * Called when an activity enters the paused state.
     *
     * <p>
     * Calculates how long the activity remained visible and reports
     * the screen view metric to the metrics collector.
     * </p>
     *
     * @param activity paused activity
     */
    @Override
    public void onActivityPaused(Activity activity) {
        Long startTimeMs = screenStartTimes.remove(activity);

        if (startTimeMs == null) {
            return;
        }

        long timeSpentMs = Math.max(
                0L,
                SystemClock.elapsedRealtime() - startTimeMs
        );

        String screenName = activity.getClass().getSimpleName();

        metricsCollector.trackScreenView(screenName, timeSpentMs);
    }

    /**
     * Called when an activity enters the stopped state.
     *
     * <p>
     * When all activities are stopped, the application is considered
     * backgrounded. The tracker then:
     * </p>
     *
     * <ul>
     *     <li>Ends the active session</li>
     *     <li>Tracks total session duration</li>
     *     <li>Flushes pending metrics</li>
     * </ul>
     *
     * @param activity stopped activity
     */
    @Override
    public void onActivityStopped(Activity activity) {
        startedActivityCount = Math.max(0, startedActivityCount - 1);

        if (startedActivityCount == 0 && appInForeground) {
            appInForeground = false;

            long sessionDurationMs = sessionManager.onBackground(System.currentTimeMillis());
            metricsCollector.trackSessionDuration(sessionDurationMs);
            metricsCollector.flush();
        }
    }

    /**
     * Called when the system requests activity state persistence.
     *
     * <p>
     * No tracking is performed at this stage.
     * </p>
     *
     * @param activity target activity
     * @param outState bundle used to save state
     */
    @Override
    public void onActivitySaveInstanceState(Activity activity, Bundle outState) {
        // No-op.
    }

    /**
     * Called when an activity is destroyed.
     *
     * <p>
     * Removes any stored screen timing information associated with
     * the destroyed activity to prevent memory leaks.
     * </p>
     *
     * @param activity destroyed activity
     */
    @Override
    public void onActivityDestroyed(Activity activity) {
        screenStartTimes.remove(activity);
    }
}