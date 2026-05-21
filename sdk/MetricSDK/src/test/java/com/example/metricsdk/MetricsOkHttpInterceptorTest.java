package com.example.metricsdk;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertThrows;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import java.io.IOException;
import java.lang.reflect.Field;
import java.util.UUID;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

import mockwebserver3.MockResponse;
import mockwebserver3.MockWebServer;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

public class MetricsOkHttpInterceptorTest {

    private MockWebServer server;
    private MetricsCollector collector;
    private ConcurrentLinkedQueue<MetricEvent> queue;

    @Before
    public void setUp() throws Exception {
        server = new MockWebServer();
        server.start();

        collector = MetricsCollector.getInstance();
        resetCollector();
        resetMetricsSDK();

        queue = getQueue();
    }

    @After
    public void tearDown() throws Exception {
        resetCollector();
        resetMetricsSDK();

        if (server != null) {
            server.close();
        }
    }

    @Test
    public void intercept_whenSdkIsNotInitialized_doesNotTrackMetrics() throws Exception {
        server.enqueue(new MockResponse.Builder().code(200).body("OK").build());

        OkHttpClient client = new OkHttpClient.Builder()
                .addInterceptor(new MetricsOkHttpInterceptor())
                .build();

        Request request = new Request.Builder()
                .url(server.url("/success"))
                .build();

        try (Response response = client.newCall(request).execute()) {
            assertEquals(200, response.code());
        }

        assertEquals(0, queue.size());
    }

    @Test
    public void intercept_whenRequestSucceeds_tracksStatusCodeAndLatency() throws Exception {
        markCollectorInitialized("device-123", UUID.randomUUID());
        markMetricsSDKInitialized(collector);

        server.enqueue(new MockResponse.Builder().code(201).body("Created").build());

        OkHttpClient client = new OkHttpClient.Builder()
                .addInterceptor(new MetricsOkHttpInterceptor())
                .build();

        Request request = new Request.Builder()
                .url(server.url("/created"))
                .build();

        try (Response response = client.newCall(request).execute()) {
            assertEquals(201, response.code());
        }

        assertEquals(3, queue.size());

        MetricEvent requestCount = queue.poll();
        MetricEvent errorRate = queue.poll();
        MetricEvent latency = queue.poll();

        assertEquals("http_request_count", requestCount.getEventType());
        assertEquals("201", requestCount.getAttributes().get("status_code"));

        assertEquals("http_error_rate", errorRate.getEventType());
        assertEquals(0, errorRate.getValue(), 0.001);

        assertEquals("http_latency_ms", latency.getEventType());
        assertEquals("ms", latency.getUnit());
    }

    @Test
    public void intercept_whenRequestFails_tracksSynthetic599AndRethrows() throws Exception {
        markCollectorInitialized("device-123", UUID.randomUUID());
        markMetricsSDKInitialized(collector);

        server.close();

        OkHttpClient client = new OkHttpClient.Builder()
                .addInterceptor(new MetricsOkHttpInterceptor())
                .build();

        Request request = new Request.Builder()
                .url(server.url("/failure"))
                .build();

        assertThrows(IOException.class, () -> client.newCall(request).execute());

        assertEquals(3, queue.size());

        MetricEvent requestCount = queue.poll();
        MetricEvent errorRate = queue.poll();
        MetricEvent latency = queue.poll();

        assertEquals("http_request_count", requestCount.getEventType());
        assertEquals("599", requestCount.getAttributes().get("status_code"));

        assertEquals("http_error_rate", errorRate.getEventType());
        assertEquals(100, errorRate.getValue(), 0.001);

        assertEquals("http_latency_ms", latency.getEventType());
    }

    private void markCollectorInitialized(String deviceId, UUID sessionId) throws Exception {
        setCollectorField("deviceId", deviceId);
        setCollectorField("sessionId", sessionId);
        setCollectorAtomicBoolean("initialized", true);
    }

    @SuppressWarnings("unchecked")
    private ConcurrentLinkedQueue<MetricEvent> getQueue() throws Exception {
        Field field = MetricsCollector.class.getDeclaredField("queue");
        field.setAccessible(true);
        return (ConcurrentLinkedQueue<MetricEvent>) field.get(collector);
    }

    private void resetCollector() throws Exception {
        getQueue().clear();

        setCollectorField("context", null);
        setCollectorField("apiUrl", null);
        setCollectorField("appToken", null);
        setCollectorField("deviceId", null);
        setCollectorField("sessionId", null);
        setCollectorField("flushManager", null);

        setCollectorAtomicBoolean("initialized", false);
        setCollectorAtomicInteger("httpRequestCount", 0);
        setCollectorAtomicInteger("httpErrorCount", 0);
    }

    private void setCollectorField(String name, Object value) throws Exception {
        Field field = MetricsCollector.class.getDeclaredField(name);
        field.setAccessible(true);
        field.set(collector, value);
    }

    private void setCollectorAtomicBoolean(String name, boolean value) throws Exception {
        Field field = MetricsCollector.class.getDeclaredField(name);
        field.setAccessible(true);
        AtomicBoolean atomicBoolean = (AtomicBoolean) field.get(collector);
        atomicBoolean.set(value);
    }

    private void setCollectorAtomicInteger(String name, int value) throws Exception {
        Field field = MetricsCollector.class.getDeclaredField(name);
        field.setAccessible(true);
        AtomicInteger atomicInteger = (AtomicInteger) field.get(collector);
        atomicInteger.set(value);
    }

    private void markMetricsSDKInitialized(MetricsCollector collector) throws Exception {
        setMetricsSDKField("collector", collector);
        setMetricsSDKField("initialized", true);
    }

    private void resetMetricsSDK() throws Exception {
        setMetricsSDKField("collector", null);
        setMetricsSDKField("sessionManager", null);
        setMetricsSDKField("appLifecycleTracker", null);
        setMetricsSDKField("initialized", false);
    }

    private void setMetricsSDKField(String name, Object value) throws Exception {
        Field field = MetricsSDK.class.getDeclaredField(name);
        field.setAccessible(true);
        field.set(null, value);
    }
}