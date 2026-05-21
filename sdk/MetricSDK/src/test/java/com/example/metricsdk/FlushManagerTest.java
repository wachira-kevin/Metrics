package com.example.metricsdk;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import android.content.Context;
import android.os.BatteryManager;

import mockwebserver3.MockResponse;
import mockwebserver3.MockWebServer;
import mockwebserver3.RecordedRequest;
import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.After;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;

// ... existing code ...

import java.util.UUID;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.TimeUnit;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

@RunWith(RobolectricTestRunner.class)
public class FlushManagerTest {

    private MockWebServer server;

    @After
    public void tearDown() throws Exception {
        if (server != null) {
            server.close();
        }
    }

    @Test
    public void flushAsync_whenQueueHasEvents_postsPayloadAndDrainsQueue() throws Exception {
        server = new MockWebServer();
        server.enqueue(new MockResponse.Builder().code(200).body("{}").build());
        server.start();

        ConcurrentLinkedQueue<MetricEvent> queue = new ConcurrentLinkedQueue<>();
        queue.add(new MetricEvent.Builder()
                .eventType("custom_event")
                .value(1)
                .unit("count")
                .timestamp(1000L)
                .sessionId(UUID.fromString("00000000-0000-0000-0000-000000000001"))
                .deviceId("device-123")
                .attribute("key", "value")
                .build());

        Context context = mockContext();

        FlushManager flushManager = new FlushManager(
                context,
                queue,
                server.url("/metrics").toString(),
                "token-123"
        );

        flushManager.flushAsync();

        RecordedRequest request = server.takeRequest(3, TimeUnit.SECONDS);

        flushManager.shutdown();

        assertNotNull("Expected FlushManager to POST a request to MockWebServer", request);
        assertTrue(queue.isEmpty());
        assertEquals("POST", request.getMethod());
        assertEquals("application/json", request.getHeaders().get("Content-Type"));
        assertEquals("token-123", request.getHeaders().get("app_token"));

        JSONObject payload = new JSONObject(request.getBody().utf8());
        JSONArray events = payload.getJSONArray("events");
        JSONObject event = events.getJSONObject(0);

        assertEquals(1, events.length());
        assertEquals("custom_event", event.getString("event_type"));
        assertEquals("device-123", event.getString("device_id"));
        assertEquals("value", event.getJSONObject("attributes").getString("key"));
        assertTrue(payload.has("memory_used_mb"));
        assertTrue(payload.has("battery_level_pct"));
        assertTrue(payload.has("network_type"));
    }

    @Test
    public void flushAsync_whenQueueIsEmpty_doesNotPostRequest() throws Exception {
        server = new MockWebServer();
        server.start();

        ConcurrentLinkedQueue<MetricEvent> queue = new ConcurrentLinkedQueue<>();

        FlushManager flushManager = new FlushManager(
                mockContext(),
                queue,
                server.url("/metrics").toString(),
                "token-123"
        );

        flushManager.flushAsync();

        RecordedRequest request = server.takeRequest(500, TimeUnit.MILLISECONDS);

        flushManager.shutdown();

        assertNull(request);
    }

    @Test
    public void flushIfNeeded_whenQueueReachesBatchSize_postsAtMostFiftyEvents() throws Exception {
        server = new MockWebServer();
        server.enqueue(new MockResponse.Builder().code(200).body("{}").build());
        server.start();

        ConcurrentLinkedQueue<MetricEvent> queue = new ConcurrentLinkedQueue<>();

        for (int i = 0; i < 55; i++) {
            queue.add(new MetricEvent.Builder()
                    .eventType("custom_event")
                    .value(i)
                    .sessionId(UUID.randomUUID())
                    .deviceId("device-" + i)
                    .build());
        }

        FlushManager flushManager = new FlushManager(
                mockContext(),
                queue,
                server.url("/metrics").toString(),
                "token-123"
        );

        flushManager.flushIfNeeded();

        RecordedRequest request = server.takeRequest(3, TimeUnit.SECONDS);

        flushManager.shutdown();

        assertNotNull("Expected FlushManager to POST a request to MockWebServer", request);

        JSONObject payload = new JSONObject(request.getBody().utf8());

        assertEquals(50, payload.getJSONArray("events").length());
        assertEquals(5, queue.size());
    }

    private Context mockContext() {
        Context context = mock(Context.class);
        Context applicationContext = mock(Context.class);
        BatteryManager batteryManager = mock(BatteryManager.class);

        when(context.getApplicationContext()).thenReturn(applicationContext);
        when(applicationContext.getSystemService(Context.BATTERY_SERVICE)).thenReturn(batteryManager);
        when(applicationContext.getSystemService(Context.CONNECTIVITY_SERVICE)).thenReturn(null);
        when(batteryManager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)).thenReturn(75);

        return context;
    }
}