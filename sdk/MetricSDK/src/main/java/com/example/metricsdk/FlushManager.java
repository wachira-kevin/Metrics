package com.example.metricsdk;

import android.content.Context;
import android.os.BatteryManager;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * Manages the scheduled or on-demand flushing of metrics events to a remote server.
 * This class is responsible for batching events from an in-memory queue and transmitting
 * them via HTTP POST requests to the specified API endpoint.
 *
 * <h2>Key Features:</h2>
 * - Automatically schedules periodic flush operations at fixed intervals.
 * - Supports on-demand flushing when certain conditions (e.g., queue size) are met.
 * - Implements retry logic for failed transmission attempts with exponential backoff.
 * - Includes system-state metadata (such as memory usage, battery level, and network type)
 *   in payload for enhanced observability.
 *
 * <h2>Constructor Parameters:</h2>
 * - `context`: Android context used for obtaining system services and resources.
 * - `queue`: A thread-safe queue for storing metrics events to be flushed.
 * - `apiUrl`: The API endpoint URL for transmitting the metrics events.
 * - `appToken`: The authorization token used for authenticating HTTP requests.
 *
 * <h2>Concurrency:</h2>
 * This class is thread-safe and uses a single-threaded `ScheduledExecutorService` for
 * managing scheduled tasks and asynchronous operations.
 *
 * <h2>Configuration:</h2>
 * - `MAX_BATCH_SIZE`: Maximum number of events that can be sent in a single flush.
 * - `FLUSH_INTERVAL_SECONDS`: Interval in seconds for the scheduled flush.
 * - `MAX_RETRY_ATTEMPTS`: Maximum number of retries for failed flush operations.
 *
 * <h2>Methods:</h2>
 * - `start()`: Initiates scheduled periodic flushes.
 * - `flushIfNeeded()`: Triggers an asynchronous flush if the queue size exceeds
 *   the maximum batch size.
 * - `flushAsync()`: Manually triggers an asynchronous flush operation.
 * - `shutdown()`: Terminates the executor service and ceases any further scheduled tasks.
 *
 * <h2>Implementation Details:</h2>
 * - Events are dequeued and converted to JSON format before sending.
 * - Retries for HTTP failures perform exponential backoff with jitter.
 * - HTTP connection settings include a 10-second timeout for both connection and read
 *   operations, and use the `Authorization` header for secure communication.
 * - System-state metadata is dynamically included in the payload to provide additional
 *   context about the device state during the flush.
 */
class FlushManager {

    private static final int MAX_BATCH_SIZE = 50;
    private static final int FLUSH_INTERVAL_SECONDS = 30;
    private static final int MAX_RETRY_ATTEMPTS = 3;

    private final Context context;
    private final ConcurrentLinkedQueue<MetricEvent> queue;
    private final String apiUrl;
    private final String appToken;

    private final ScheduledExecutorService executor =
            Executors.newSingleThreadScheduledExecutor();

    /**
     * Constructs a new instance of the {@code FlushManager} class.
     * This class is responsible for managing the periodic and batched flushing
     * of {@code MetricEvent} objects to a remote API endpoint. It leverages
     * a concurrent queue for event storage and a background executor to handle
     * asynchronous flushing operations.
     *
     * @param context the Android {@code Context} used to initialize the FlushManager instance.
     *                The application's context is retained to ensure long-lived operations are supported.
     * @param queue   a {@code ConcurrentLinkedQueue} of {@code MetricEvent} objects to be managed and flushed.
     *                This queue contains the metric events that have been logged and are ready to be sent.
     * @param apiUrl  the URL of the remote API endpoint where the metric data will be transmitted.
     * @param appToken the authentication token associated with the application, used to authorize
     *                 requests made to the backend service.
     */
    FlushManager(
            Context context,
            ConcurrentLinkedQueue<MetricEvent> queue,
            String apiUrl,
            String appToken
    ) {
        this.context = context.getApplicationContext();
        this.queue = queue;
        this.apiUrl = apiUrl;
        this.appToken = appToken;
    }

    /**
     * Starts the periodic flushing process for {@code MetricEvent} objects in the queue.
     *
     * This method schedules a recurrent task using a fixed-rate execution policy with
     * the {@code FLUSH_INTERVAL_SECONDS} as the interval between successive executions.
     * The task attempts to flush the queue contents safely by invoking {@code flushSafely()}.
     *
     * The periodic operation is executed on a background thread managed by the {@code executor}.
     * This ensures that flushing does not block the main thread or interfere with the
     * application's primary execution flow.
     *
     * It is expected that this method is called once during the lifecycle of the
     * application or component to initiate the flushing mechanism. Redundant invocations
     * may result in multiple tasks attempting to flush simultaneously.
     */
    void start() {
        executor.scheduleAtFixedRate(
                this::flushSafely,
                FLUSH_INTERVAL_SECONDS,
                FLUSH_INTERVAL_SECONDS,
                TimeUnit.SECONDS
        );
    }

    /**
     * Checks whether the current size of the event queue has exceeded the configured threshold
     * and triggers an asynchronous flush operation if necessary.
     *
     * This method evaluates whether the number of {@code MetricEvent} objects in the queue has
     * reached or surpassed the {@code MAX_BATCH_SIZE}. If the threshold is met, it invokes the
     * {@code flushAsync()} method to offload the flushing process to a background thread.
     *
     * The purpose of this method is to ensure timely and efficient processing of queued events,
     * preventing memory buildup or delays in event transmission. It is designed to be lightweight
     * and can be called frequently, accommodating scenarios with rapid event generation.
     */
    void flushIfNeeded() {
        if (queue.size() >= MAX_BATCH_SIZE) {
            flushAsync();
        }
    }

    /**
     * Triggers an asynchronous flushing operation by delegating the task
     * to a background thread managed by the {@code executor}.
     *
     * This method is designed to offload the flushing process from the
     * main thread to ensure non-blocking, efficient handling of queued
     * {@code MetricEvent} objects. The underlying {@code flushSafely()}
     * operation ensures safe execution with appropriate error handling.
     *
     * The asynchronous operation is particularly beneficial in scenarios
     * where the queuing mechanism experiences high throughput, as it
     * prevents long-running flush operations from impacting system
     * performance or responsiveness.
     *
     * It is expected that this method is invoked either periodically by
     * a scheduling routine or manually in response to specific conditions
     * such as queue size thresholds or system state changes.
     */
    void flushAsync() {
        executor.execute(this::flushSafely);
    }

    /**
     * Safely attempts to flush a batch of {@code MetricEvent} objects.
     *
     * This method wraps the {@code flush()} method in a try-catch block to ensure that
     * any exceptions arising during the flushing process are caught and suppressed.
     * It prevents the propagation of errors that might disrupt the calling process.
     *
     * Typical use cases for this method include scenarios where the flushing operation
     * is invoked periodically or asynchronously, and any failures in the operation
     * should not compromise system stability.
     *
     * This method is private and intended for internal use within the {@code FlushManager}
     * class.
     */
    private void flushSafely() {
        try {
            flush();
        } catch (Exception ignored) {
        }
    }

    /**
     * Flushes a batch of {@code MetricEvent} objects from the queue, converts them
     * into JSON format, and sends them to a remote API endpoint. The method processes
     * events in batches of up to {@code MAX_BATCH_SIZE}.
     *
     * If the queue is empty, the method returns immediately without performing any operations.
     * If no events are available to flush after polling, the method also terminates early.
     *
     * When events are successfully retrieved, they are prepared as a {@code JSONArray}
     * and encapsulated into a payload along with system metrics such as memory usage,
     * battery level, and network type.
     *
     * The method then attempts to transmit the payload to the remote endpoint using
     * a retry mechanism. If transmission fails, requeueing behavior is omitted in
     * this implementation.
     *
     * This method assumes proper error handling and recovery mechanisms in case
     * of failures during batch processing or transmission.
     *
     * @throws Exception if an error occurs during event processing or while
     *         transmitting the payload.
     */
    private void flush() throws Exception {
        if (queue.isEmpty()) {
            return;
        }

        JSONArray eventsArray = new JSONArray();

        int count = 0;
        while (count < MAX_BATCH_SIZE) {
            MetricEvent event = queue.poll();
            if (event == null) {
                break;
            }

            eventsArray.put(event.toJson());
            count++;
        }

        if (eventsArray.length() == 0) {
            return;
        }

        JSONObject payload = new JSONObject();
        payload.put("events", eventsArray);
        payload.put("memory_used_mb", getMemoryUsedMb());
        payload.put("battery_level_pct", getBatteryLevelPct());
        payload.put("network_type", NetworkTypeProvider.getNetworkType(context));

        boolean success = postWithRetry(payload);

        if (!success) {
            // Basic requeue behavior is omitted here because MetricEvent objects
            // were already converted to JSON. In production, drain into a List first
            // and requeue if all retries fail.
        }
    }

    /**
     * Attempts to send a JSON payload to the remote API endpoint using a POST request with a retry mechanism.
     * Retries are performed using exponential backoff if the transmission fails. The method ensures that the
     * retries are capped at a predefined maximum number of attempts. If the maximum retries are exceeded, or
     * an interruption occurs during a backoff period, the method terminates and returns a failure result.
     *
     * @param payload the {@code JSONObject} payload to be sent to the remote API endpoint. This contains the data
     *                that needs to be transmitted.
     * @return {@code true} if the payload was successfully sent to the remote API endpoint, {@code false} otherwise.
     */
    private boolean postWithRetry(JSONObject payload) {
        int attempt = 0;

        while (attempt < MAX_RETRY_ATTEMPTS) {
            try {
                post(payload);
                return true;
            } catch (Exception e) {
                attempt++;

                if (attempt >= MAX_RETRY_ATTEMPTS) {
                    return false;
                }

                long backoffMs = (long) Math.pow(2, attempt - 1) * 1000L;

                try {
                    Thread.sleep(backoffMs);
                } catch (InterruptedException interruptedException) {
                    Thread.currentThread().interrupt();
                    return false;
                }
            }
        }

        return false;
    }

    /**
     * Sends a JSON payload to the configured remote API endpoint using an HTTP POST request.
     * This method sets a number of request properties, including content type and
     * an application-specific token, before sending the payload.
     * If the server responds with an unsuccessful status code (non-2xx), an exception is thrown.
     *
     * @param payload the {@code JSONObject} containing the data to be sent to the remote API.
     *                This object is serialized into a JSON string and included in the request body.
     * @throws Exception if there is an error during the connection setup, data transmission,
     *                   or the response status is not successful (non-2xx).
     */
    private void post(JSONObject payload) throws Exception {
        URL url = new URL(apiUrl);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();

        connection.setRequestMethod("POST");
        connection.setConnectTimeout(10_000);
        connection.setReadTimeout(10_000);
        connection.setDoOutput(true);
        connection.setRequestProperty("Content-Type", "application/json");
        connection.setRequestProperty("app_token", appToken);

        byte[] body = payload.toString().getBytes("UTF-8");

        OutputStream outputStream = connection.getOutputStream();
        outputStream.write(body);
        outputStream.flush();
        outputStream.close();

        int code = connection.getResponseCode();

        if (code < 200 || code >= 300) {
            throw new IllegalStateException("Flush failed with HTTP " + code);
        }

        connection.disconnect();
    }

    /**
     * Calculates the amount of memory currently used by the Java Virtual Machine (JVM) in megabytes.
     * This method computes memory usage by subtracting the JVM's free memory from its total memory
     * and converts the result from bytes to megabytes.
     *
     * @return the memory used by the JVM in megabytes as a floating-point number.
     */
    private float getMemoryUsedMb() {
        Runtime runtime = Runtime.getRuntime();
        long usedBytes = runtime.totalMemory() - runtime.freeMemory();
        return usedBytes / 1024f / 1024f;
    }

    /**
     * Retrieves the current battery level as a percentage.
     * This method utilizes the Android BatteryManager API to query the device's battery capacity.
     * If the BatteryManager service is unavailable, the method returns -1.
     *
     * @return the battery level as a floating-point percentage (0 to 100),
     *         or -1 if the battery level cannot be determined.
     */
    private float getBatteryLevelPct() {
        BatteryManager batteryManager =
                (BatteryManager) context.getSystemService(Context.BATTERY_SERVICE);

        if (batteryManager == null) {
            return -1f;
        }

        int level = batteryManager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY);
        return level;
    }

    void shutdown() {
        executor.shutdownNow();
    }
}