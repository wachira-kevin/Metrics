package com.example.metricsdk;

import android.content.Context;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * A singleton class responsible for collecting and managing metrics related to application
 * events such as performance, user behavior, crashes, and custom-defined events.
 * MetricsCollected events are enqueued and sent to a backend server for analysis.
 * This class is thread-safe.
 */
public class MetricsCollector {

    private static final MetricsCollector INSTANCE = new MetricsCollector();

    private final ConcurrentLinkedQueue<MetricEvent> queue = new ConcurrentLinkedQueue<>();
    private final AtomicBoolean initialized = new AtomicBoolean(false);

    private Context context;
    private String apiUrl;
    private String appToken;
    private String deviceId;
    private UUID sessionId;
    private FlushManager flushManager;

    private final AtomicInteger httpRequestCount = new AtomicInteger(0);

    private final AtomicInteger httpErrorCount = new AtomicInteger(0);

    /**
     * Private constructor for the {@code MetricsCollector} class to prevent instantiation.
     *
     * This class acts as a singleton and provides centralized functionalities for
     * collecting and reporting various types of application metrics such as session
     * durations, crashes, screen views, HTTP requests, and custom events. The private
     * constructor ensures that instances of this class are only created internally
     * to preserve its singleton design.
     */
    private MetricsCollector() {
    }

    /**
     * Provides the singleton instance of the {@code MetricsCollector} class.
     * This method ensures that only one instance of the {@code MetricsCollector}
     * exists throughout the application lifecycle, following the singleton design pattern.
     *
     * @return the singleton instance of {@code MetricsCollector}
     */
    public static MetricsCollector getInstance() {
        return INSTANCE;
    }

    /**
     * Initializes the metrics collection system with the provided context, API URL, and application token.
     * This method sets up necessary configurations and starts the data flushing mechanism
     * to handle queued metric events. It ensures that the initialization logic is executed only once
     * to prevent redundant resource allocation.
     *
     * @param context the Android application context, used for accessing application-level resources and services.
     * @param apiUrl the base URL of the API endpoint where metric data will be sent.
     * @param appToken a unique token that authenticates the application with the API and associates the metrics.
     */
    public void initialize(Context context, String apiUrl, String appToken) {
        if (initialized.get()) {
            return;
        }

        this.context = context.getApplicationContext();
        this.apiUrl = apiUrl;
        this.appToken = appToken;
        this.deviceId = DeviceInfoProvider.getDeviceId(this.context);
        this.sessionId = UUID.randomUUID();

        this.flushManager = new FlushManager(
                this.context,
                queue,
                apiUrl,
                appToken
        );

        this.flushManager.start();

        initialized.set(true);
    }

    /**
     * Tracks the application start time in milliseconds and enqueues it as a metric event.
     * This method logs the duration it takes for the application to start, typically used
     * to monitor and analyze application performance during the startup phase.
     *
     * @param ms the application start time in milliseconds. This value represents the
     *           elapsed time from the initiation of the application process to when it becomes
     *           usable by the user.
     */
    public void trackAppStart(long ms) {
        enqueue(new MetricEvent.Builder()
                .eventType("app_start_time_ms")
                .value(ms)
                .unit("ms")
                .sessionId(sessionId)
                .deviceId(deviceId)
                .build());
    }

    /**
     * Tracks the duration of a user session and enqueues it as a metric event.
     * This method records the session duration in milliseconds, which can be
     * used for analytics or performance monitoring purposes.
     *
     * @param ms the duration of the session in milliseconds. This value represents
     *           the total time a user spent in the session.
     */
    public void trackSessionDuration(long ms) {
        enqueue(new MetricEvent.Builder()
                .eventType("session_duration_ms")
                .value(ms)
                .unit("ms")
                .sessionId(sessionId)
                .deviceId(deviceId)
                .build());
    }

    /**
     * Tracks a screen view event and enqueues it as a metric event for analytics.
     * This method records the time spent on a particular screen along with its name.
     *
     * @param name the name of the screen being tracked. This value is used to identify
     *             the screen in the analytics data for reporting and analysis purposes.
     * @param timeSpentMs the time, in milliseconds, that the user spent on the screen.
     *                    This value represents the duration of the screen view.
     */
    public void trackScreenView(String name, long timeSpentMs) {
        enqueue(new MetricEvent.Builder()
                .eventType("screen_view")
                .value(timeSpentMs)
                .unit("ms")
                .sessionId(sessionId)
                .deviceId(deviceId)
                .attribute("screen_name", name)
                .build());
    }

    /**
     * Tracks an HTTP request by logging its status code, latency, and derived metrics such as error rate.
     * This method increments the total count of HTTP requests, categorizes errors based on the status code,
     * and enqueues metric events for analytics purposes.
     *
     * @param statusCode the HTTP status code of the request. Values greater than or equal to 400
     *                   are categorized as errors.
     * @param latencyMs the time, in milliseconds, that it took for the HTTP request to complete.
     */
    public void trackHttpRequest(int statusCode, long latencyMs) {
        int total = httpRequestCount.incrementAndGet();

        if (statusCode >= 400) {
            httpErrorCount.incrementAndGet();
        }

        enqueue(new MetricEvent.Builder()
                .eventType("http_request_count")
                .value(1)
                .unit("count")
                .sessionId(sessionId)
                .deviceId(deviceId)
                .attribute("status_code", String.valueOf(statusCode))
                .attribute("latency_ms", String.valueOf(latencyMs))
                .build());

        float errorRate = total == 0
                ? 0f
                : ((float) httpErrorCount.get() / total) * 100f;

        enqueue(new MetricEvent.Builder()
                .eventType("http_error_rate")
                .value(errorRate)
                .unit("percent")
                .sessionId(sessionId)
                .deviceId(deviceId)
                .build());

        enqueue(new MetricEvent.Builder()
                .eventType("http_latency_ms")
                .value(latencyMs)
                .unit("ms")
                .sessionId(sessionId)
                .deviceId(deviceId)
                .build());
    }

    /**
     * Tracks a crash event and enqueues it as a metric event.
     * This method captures details about the exception, including its class name and message,
     * and logs the event for analytics purposes. It increments the crash count metric.
     *
     * @param throwable the {@code Throwable} instance that represents the exception
     *                  causing the crash. This object provides details such as the
     *                  class name and error message, which are logged as attributes
     *                  in the metric event.
     */
    public void trackCrash(Throwable throwable) {
        enqueue(new MetricEvent.Builder()
                .eventType("crash_count")
                .value(1)
                .unit("count")
                .sessionId(sessionId)
                .deviceId(deviceId)
                .attribute("exception", throwable.getClass().getName())
                .attribute("message", throwable.getMessage() == null ? "" : throwable.getMessage())
                .build());
    }

    /**
     * Tracks an Application Not Responding (ANR) event and enqueues it as a metric event.
     *
     * This method logs each occurrence of an ANR event by incrementing the count and
     * associating it with relevant attributes such as the session ID and device ID.
     * The resulting metric event is added to the internal queue for further processing.
     */
    public void trackAnr() {
        enqueue(new MetricEvent.Builder()
                .eventType("anr_count")
                .value(1)
                .unit("count")
                .sessionId(sessionId)
                .deviceId(deviceId)
                .build());
    }

    /**
     * Tracks the number of dropped frames and associates it with a specific screen.
     * This method records the dropped frame count and screen-related information
     * as part of the application's metric events for performance analysis purposes.
     *
     * @param count the number of frames dropped. This value represents the
     *              total dropped frames for the given screen during the session.
     * @param screenName the name of the screen where the frame drops occurred.
     *                   This value helps identify the context in which the issue
     *                   was experienced.
     */
    public void trackFrameDropCount(int count, String screenName) {
        enqueue(new MetricEvent.Builder()
                .eventType("frame_drop_count")
                .value(count)
                .unit("count")
                .sessionId(sessionId)
                .deviceId(deviceId)
                .attribute("screen_name", screenName)
                .build());
    }

    /**
     * Tracks a custom event and enqueues it for processing.
     * This method allows the user to log custom key-value pairs as attributes
     * for a custom metric event.
     *
     * @param key the key associated with the custom event attribute.
     *            This value identifies the attribute in the logged event.
     * @param value the value associated with the custom event attribute.
     *              This value represents the data or detail of the attribute.
     */
    public void trackCustomEvent(String key, String value) {
        Map<String, String> attributes = new HashMap<>();
        attributes.put(key, value);

        enqueue(new MetricEvent.Builder()
                .eventType("custom_event")
                .value(1)
                .unit("count")
                .sessionId(sessionId)
                .deviceId(deviceId)
                .attributes(attributes)
                .build());
    }

    /**
     * Tracks a custom event and enqueues it for processing.
     * This method allows users to log custom key-value pairs as attributes
     * for a custom metric event. The custom attributes provide flexibility
     * in capturing additional application-specific metrics or events.
     *
     * @param attributes a map containing key-value pairs representing the custom
     *                   event attributes. The keys are strings identifying the
     *                   attribute names, and the values are their corresponding
     *                   string details or data.
     */
    public void trackCustomEvent(Map<String, String> attributes) {
        enqueue(new MetricEvent.Builder()
                .eventType("custom_event")
                .value(1)
                .unit("count")
                .sessionId(sessionId)
                .deviceId(deviceId)
                .attributes(attributes)
                .build());
    }

    /**
     * Adds a {@code MetricEvent} to the internal event queue for processing.
     * This method ensures that the event is only enqueued if the metrics system
     * is initialized. If a {@code FlushManager} is present, it triggers the
     * flush check to process the queue if necessary.
     *
     * @param event the {@code MetricEvent} to be added to the queue. This event
     *              contains details about a specific metric to be logged or analyzed.
     */
    private void enqueue(MetricEvent event) {
        if (!initialized.get()) {
            return;
        }

        queue.add(event);

        if (flushManager != null) {
            flushManager.flushIfNeeded();
        }
    }

    /**
     * Flushes the metrics collected in the internal queue asynchronously.
     *
     * This method triggers the {@code FlushManager} (if initialized) to handle the
     * queued metric data and send it to the designated target, such as a server or
     * a remote analytics endpoint. The flushing operation is performed asynchronously
     * to avoid blocking the main thread or negatively impacting application performance.
     *
     * It ensures data is processed in batches, reducing the overhead of handling each
     * metric event individually. This operation is typically called periodically or
     * in response to specific triggers (e.g., application lifecycle events).
     */
    public void flush() {
        if (flushManager != null) {
            flushManager.flushAsync();
        }
    }
}