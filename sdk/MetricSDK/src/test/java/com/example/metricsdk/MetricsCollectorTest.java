package com.example.metricsdk;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import java.lang.reflect.Field;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.Assert.*;

public class MetricsCollectorTest {

    private MetricsCollector collector;
    private ConcurrentLinkedQueue<MetricEvent> queue;

    @Before
    public void setUp() throws Exception {
        collector = MetricsCollector.getInstance();
        resetCollector();

        queue = getQueue();
    }

    @After
    public void tearDown() throws Exception {
        resetCollector();
    }

    @Test
    public void trackAppStart_whenInitialized_enqueuesAppStartEvent() throws Exception {
        markInitialized("device-123", UUID.fromString("00000000-0000-0000-0000-000000000001"));

        collector.trackAppStart(1200);

        MetricEvent event = queue.poll();

        assertNotNull(event);
        assertEquals("app_start_time_ms", event.getEventType());
        assertEquals(1200, event.getValue(), 0.001);
        assertEquals("ms", event.getUnit());
        assertEquals("device-123", event.getDeviceId());
    }

    @Test
    public void trackSessionDuration_whenInitialized_enqueuesSessionDurationEvent() throws Exception {
        markInitialized("device-123", UUID.randomUUID());

        collector.trackSessionDuration(5000);

        MetricEvent event = queue.poll();

        assertNotNull(event);
        assertEquals("session_duration_ms", event.getEventType());
        assertEquals(5000, event.getValue(), 0.001);
        assertEquals("ms", event.getUnit());
    }

    @Test
    public void trackScreenView_whenInitialized_enqueuesScreenViewEvent() throws Exception {
        markInitialized("device-123", UUID.randomUUID());

        collector.trackScreenView("Home", 300);

        MetricEvent event = queue.poll();

        assertNotNull(event);
        assertEquals("screen_view", event.getEventType());
        assertEquals(300, event.getValue(), 0.001);
        assertEquals("ms", event.getUnit());
        assertEquals("Home", event.getAttributes().get("screen_name"));
    }

    @Test
    public void trackHttpRequest_whenSuccess_enqueuesRequestCountErrorRateAndLatency() throws Exception {
        markInitialized("device-123", UUID.randomUUID());

        collector.trackHttpRequest(200, 150);

        assertEquals(3, queue.size());

        MetricEvent requestCount = queue.poll();
        MetricEvent errorRate = queue.poll();
        MetricEvent latency = queue.poll();

        assertNotNull(requestCount);
        assertNotNull(errorRate);
        assertNotNull(latency);

        assertEquals("http_request_count", requestCount.getEventType());
        assertEquals(1, requestCount.getValue(), 0.001);
        assertEquals("200", requestCount.getAttributes().get("status_code"));
        assertEquals("150", requestCount.getAttributes().get("latency_ms"));

        assertEquals("http_error_rate", errorRate.getEventType());
        assertEquals(0, errorRate.getValue(), 0.001);
        assertEquals("percent", errorRate.getUnit());

        assertEquals("http_latency_ms", latency.getEventType());
        assertEquals(150, latency.getValue(), 0.001);
        assertEquals("ms", latency.getUnit());
    }

    @Test
    public void trackHttpRequest_whenError_enqueuesErrorRate() throws Exception {
        markInitialized("device-123", UUID.randomUUID());

        collector.trackHttpRequest(500, 250);

        MetricEvent requestCount = queue.poll();
        MetricEvent errorRate = queue.poll();
        MetricEvent latency = queue.poll();

        assertNotNull(requestCount);
        assertNotNull(errorRate);
        assertNotNull(latency);

        assertEquals("http_request_count", requestCount.getEventType());
        assertEquals("500", requestCount.getAttributes().get("status_code"));

        assertEquals("http_error_rate", errorRate.getEventType());
        assertEquals(100, errorRate.getValue(), 0.001);

        assertEquals("http_latency_ms", latency.getEventType());
        assertEquals(250, latency.getValue(), 0.001);
    }

    @Test
    public void trackCrash_whenInitialized_enqueuesCrashEvent() throws Exception {
        markInitialized("device-123", UUID.randomUUID());

        collector.trackCrash(new IllegalArgumentException("bad input"));

        MetricEvent event = queue.poll();

        assertNotNull(event);
        assertEquals("crash_count", event.getEventType());
        assertEquals(1, event.getValue(), 0.001);
        assertEquals("count", event.getUnit());
        assertEquals(IllegalArgumentException.class.getName(), event.getAttributes().get("exception"));
        assertEquals("bad input", event.getAttributes().get("message"));
    }

    @Test
    public void trackCrash_whenMessageIsNull_usesEmptyMessage() throws Exception {
        markInitialized("device-123", UUID.randomUUID());

        collector.trackCrash(new RuntimeException());

        MetricEvent event = queue.poll();

        assertNotNull(event);
        assertEquals("", event.getAttributes().get("message"));
    }

    @Test
    public void trackAnr_whenInitialized_enqueuesAnrEvent() throws Exception {
        markInitialized("device-123", UUID.randomUUID());

        collector.trackAnr();

        MetricEvent event = queue.poll();

        assertNotNull(event);
        assertEquals("anr_count", event.getEventType());
        assertEquals(1, event.getValue(), 0.001);
        assertEquals("count", event.getUnit());
    }

    @Test
    public void trackFrameDropCount_whenInitialized_enqueuesFrameDropEvent() throws Exception {
        markInitialized("device-123", UUID.randomUUID());

        collector.trackFrameDropCount(12, "Feed");

        MetricEvent event = queue.poll();

        assertNotNull(event);
        assertEquals("frame_drop_count", event.getEventType());
        assertEquals(12, event.getValue(), 0.001);
        assertEquals("count", event.getUnit());
        assertEquals("Feed", event.getAttributes().get("screen_name"));
    }

    @Test
    public void trackCustomEvent_withKeyValue_enqueuesCustomEvent() throws Exception {
        markInitialized("device-123", UUID.randomUUID());

        collector.trackCustomEvent("purchase_id", "123");

        MetricEvent event = queue.poll();

        assertNotNull(event);
        assertEquals("custom_event", event.getEventType());
        assertEquals(1, event.getValue(), 0.001);
        assertEquals("count", event.getUnit());
        assertEquals("123", event.getAttributes().get("purchase_id"));
    }

    @Test
    public void trackCustomEvent_withMap_enqueuesCustomEvent() throws Exception {
        markInitialized("device-123", UUID.randomUUID());

        collector.trackCustomEvent(Map.of(
                "feature", "checkout",
                "variant", "A"
        ));

        MetricEvent event = queue.poll();

        assertNotNull(event);
        assertEquals("custom_event", event.getEventType());
        assertEquals("checkout", event.getAttributes().get("feature"));
        assertEquals("A", event.getAttributes().get("variant"));
    }

    @Test
    public void trackEvent_whenNotInitialized_throwsAndDoesNotEnqueue() {
        IllegalStateException exception = assertThrows(
                IllegalStateException.class,
                () -> collector.trackAppStart(100)
        );

        assertEquals("sessionId is required", exception.getMessage());
        assertTrue(queue.isEmpty());
    }

    private void markInitialized(String deviceId, UUID sessionId) throws Exception {
        setField("deviceId", deviceId);
        setField("sessionId", sessionId);
        setAtomicBoolean("initialized", true);
    }

    @SuppressWarnings("unchecked")
    private ConcurrentLinkedQueue<MetricEvent> getQueue() throws Exception {
        Field field = MetricsCollector.class.getDeclaredField("queue");
        field.setAccessible(true);
        return (ConcurrentLinkedQueue<MetricEvent>) field.get(collector);
    }

    private void resetCollector() throws Exception {
        ConcurrentLinkedQueue<MetricEvent> currentQueue = getQueue();
        currentQueue.clear();

        setField("context", null);
        setField("apiUrl", null);
        setField("appToken", null);
        setField("deviceId", null);
        setField("sessionId", null);
        setField("flushManager", null);

        setAtomicBoolean("initialized", false);
        setAtomicInteger("httpRequestCount", 0);
        setAtomicInteger("httpErrorCount", 0);
    }

    private void setField(String name, Object value) throws Exception {
        Field field = MetricsCollector.class.getDeclaredField(name);
        field.setAccessible(true);
        field.set(collector, value);
    }

    private void setAtomicBoolean(String name, boolean value) throws Exception {
        Field field = MetricsCollector.class.getDeclaredField(name);
        field.setAccessible(true);
        AtomicBoolean atomicBoolean = (AtomicBoolean) field.get(collector);
        atomicBoolean.set(value);
    }

    private void setAtomicInteger(String name, int value) throws Exception {
        Field field = MetricsCollector.class.getDeclaredField(name);
        field.setAccessible(true);
        AtomicInteger atomicInteger = (AtomicInteger) field.get(collector);
        atomicInteger.set(value);
    }
}