package com.example.metricsdk.internal;

import java.util.UUID;

/**
 * Manages application session lifecycle and active session duration tracking.
 *
 * <p>
 * A session represents a continuous period of user interaction with the application.
 * The session starts when the {@link SessionManager} is initialized or when a new
 * session is explicitly created.
 * </p>
 *
 * <p>
 * The manager tracks:
 * </p>
 * <ul>
 *     <li>Current session identifier</li>
 *     <li>Session start timestamp</li>
 *     <li>Foreground/background transitions</li>
 *     <li>Total active session duration</li>
 * </ul>
 *
 * <p>
 * A new session is automatically created when the application returns to the
 * foreground after remaining in the background longer than the configured
 * session timeout.
 * </p>
 *
 * <p>
 * This class is thread-safe. All public methods are synchronized.
 * </p>
 */
public class SessionManager {

    /**
     * Default inactivity timeout used to determine when a new session should begin.
     *
     * <p>
     * If the application stays in the background longer than this duration,
     * the next foreground event will trigger a new session.
     * </p>
     */
    private static final long DEFAULT_SESSION_TIMEOUT_MS = 30_000L;

    /**
     * Configured session timeout duration in milliseconds.
     */
    private final long sessionTimeoutMs;

    /**
     * Unique identifier for the current session.
     */
    private UUID sessionId;

    /**
     * Timestamp when the current session started.
     */
    private long sessionStartTimeMs;

    /**
     * Timestamp of the last foreground event.
     */
    private long lastForegroundTimeMs;

    /**
     * Total accumulated active session duration.
     *
     * <p>
     * This value only increases while the application is considered active.
     * </p>
     */
    private long accumulatedActiveDurationMs;

    /**
     * Indicates whether the session is currently active (foregrounded).
     */
    private boolean sessionActive;

    /**
     * Creates a new {@link SessionManager} using the default session timeout.
     *
     * <p>
     * A new session is started immediately upon initialization.
     * </p>
     */
    public SessionManager() {
        this(DEFAULT_SESSION_TIMEOUT_MS);
    }

    /**
     * Creates a new {@link SessionManager} with a custom session timeout.
     *
     * @param sessionTimeoutMs duration in milliseconds after which a backgrounded
     *                         application is considered to have ended its session
     */
    public SessionManager(long sessionTimeoutMs) {
        this.sessionTimeoutMs = sessionTimeoutMs;
        startNewSession(System.currentTimeMillis());
    }

    /**
     * Returns the unique identifier of the current session.
     *
     * @return current session UUID
     */
    public synchronized UUID getSessionId() {
        return sessionId;
    }

    /**
     * Marks the application as foregrounded.
     *
     * <p>
     * If the application was previously backgrounded for longer than the configured
     * session timeout, a completely new session is created.
     * Otherwise, the existing session is resumed.
     * </p>
     *
     * @param timestampMs timestamp when the application entered the foreground
     */
    public synchronized void onForeground(long timestampMs) {
        if (!sessionActive) {
            long backgroundDurationMs = timestampMs - lastForegroundTimeMs;

            if (backgroundDurationMs >= sessionTimeoutMs) {
                startNewSession(timestampMs);
            } else {
                sessionActive = true;
                lastForegroundTimeMs = timestampMs;
            }
        }
    }

    /**
     * Marks the application as backgrounded and updates active session duration.
     *
     * <p>
     * The active duration between the last foreground event and the provided
     * background timestamp is added to the accumulated session duration.
     * </p>
     *
     * @param timestampMs timestamp when the application entered the background
     * @return total accumulated active session duration in milliseconds
     */
    public synchronized long onBackground(long timestampMs) {
        if (!sessionActive) {
            return accumulatedActiveDurationMs;
        }

        long activeDurationMs = Math.max(0L, timestampMs - lastForegroundTimeMs);
        accumulatedActiveDurationMs += activeDurationMs;
        lastForegroundTimeMs = timestampMs;
        sessionActive = false;

        return accumulatedActiveDurationMs;
    }

    /**
     * Returns the current total active duration for the session.
     *
     * <p>
     * If the session is currently active, the duration since the last foreground
     * event is included in the returned value.
     * </p>
     *
     * @return current session active duration in milliseconds
     */
    public synchronized long getCurrentSessionDurationMs() {
        long durationMs = accumulatedActiveDurationMs;

        if (sessionActive) {
            durationMs += Math.max(0L, System.currentTimeMillis() - lastForegroundTimeMs);
        }

        return durationMs;
    }

    /**
     * Indicates whether the session is currently active.
     *
     * @return {@code true} if the application is in the foreground,
     *         otherwise {@code false}
     */
    public synchronized boolean isSessionActive() {
        return sessionActive;
    }

    /**
     * Forces creation of a completely new session.
     *
     * <p>
     * This resets:
     * </p>
     * <ul>
     *     <li>Session identifier</li>
     *     <li>Session start time</li>
     *     <li>Accumulated active duration</li>
     * </ul>
     */
    public synchronized void forceNewSession() {
        startNewSession(System.currentTimeMillis());
    }

    /**
     * Initializes a new session and resets session state.
     *
     * @param timestampMs timestamp used as the session start time
     */
    private void startNewSession(long timestampMs) {
        this.sessionId = UUID.randomUUID();
        this.sessionStartTimeMs = timestampMs;
        this.lastForegroundTimeMs = timestampMs;
        this.accumulatedActiveDurationMs = 0L;
        this.sessionActive = true;
    }

    /**
     * Returns the timestamp when the current session started.
     *
     * @return session start timestamp in milliseconds
     */
    public synchronized long getSessionStartTimeMs() {
        return sessionStartTimeMs;
    }
}