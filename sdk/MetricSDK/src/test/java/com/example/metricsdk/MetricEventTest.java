package com.example.metricsdk;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

import org.json.JSONObject;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

@RunWith(RobolectricTestRunner.class)
public class MetricEventTest {

    @Test
    public void build_withRequiredFields_createsMetricEvent() throws Exception {
        UUID sessionId = UUID.randomUUID();

        MetricEvent event = new MetricEvent.Builder()
                .eventType("screen_view")
                .value(250)
                .unit("ms")
                .timestamp(123456789L)
                .sessionId(sessionId)
                .deviceId("device-123")
                .attribute("screen_name", "Home")
                .build();

        assertEquals("screen_view", event.getEventType());
        assertEquals(250, event.getValue(), 0.001);
        assertEquals("ms", event.getUnit());
        assertEquals(123456789L, event.getTimestamp());
        assertEquals(sessionId, event.getSessionId());
        assertEquals("device-123", event.getDeviceId());
        assertEquals("Home", event.getAttributes().get("screen_name"));
    }

    @Test
    public void build_withoutUnit_defaultsToCount() {
        MetricEvent event = new MetricEvent.Builder()
                .eventType("custom_event")
                .value(1)
                .sessionId(UUID.randomUUID())
                .deviceId("device-123")
                .build();

        assertEquals("count", event.getUnit());
    }

    @Test
    public void build_withoutEventType_throwsException() {
        IllegalStateException exception = assertThrows(
                IllegalStateException.class,
                () -> new MetricEvent.Builder()
                        .sessionId(UUID.randomUUID())
                        .deviceId("device-123")
                        .build()
        );

        assertEquals("eventType is required", exception.getMessage());
    }

    @Test
    public void build_withoutSessionId_throwsException() {
        IllegalStateException exception = assertThrows(
                IllegalStateException.class,
                () -> new MetricEvent.Builder()
                        .eventType("custom_event")
                        .deviceId("device-123")
                        .build()
        );

        assertEquals("sessionId is required", exception.getMessage());
    }

    @Test
    public void build_withoutDeviceId_throwsException() {
        IllegalStateException exception = assertThrows(
                IllegalStateException.class,
                () -> new MetricEvent.Builder()
                        .eventType("custom_event")
                        .sessionId(UUID.randomUUID())
                        .build()
        );

        assertEquals("deviceId is required", exception.getMessage());
    }

    @Test
    public void toJson_containsExpectedFields() throws Exception {
        UUID sessionId = UUID.randomUUID();

        Map<String, String> attributes = new HashMap<>();
        attributes.put("key", "value");

        MetricEvent event = new MetricEvent.Builder()
                .eventType("custom_event")
                .value(42)
                .unit("count")
                .timestamp(1000L)
                .sessionId(sessionId)
                .deviceId("device-123")
                .attributes(attributes)
                .build();

        JSONObject json = event.toJson();

        assertEquals("custom_event", json.getString("event_type"));
        assertEquals(42, json.getDouble("value"), 0.001);
        assertEquals("count", json.getString("unit"));
        assertEquals(1000L, json.getLong("timestamp"));
        assertEquals(sessionId.toString(), json.getString("session_id"));
        assertEquals("device-123", json.getString("device_id"));
        assertEquals("value", json.getJSONObject("attributes").getString("key"));
        assertTrue(json.has("attributes"));
    }
}