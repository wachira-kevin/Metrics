package com.example.metricsdk;

import org.json.JSONException;
import org.json.JSONObject;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Represents a metric event that can be logged and tracked.
 * This class encapsulates details about a specific metric event, including its type, value, unit, and associated metadata.
 *
 * Instances of this class are built using the {@link MetricEvent.Builder} class, which enforces validation
 * and ensures all required fields are properly set before building the object.
 */
public class MetricEvent {


    private final String eventType;
    private final double value;
    private final String unit;
    private final long timestamp;
    private final UUID sessionId;
    private final String deviceId;
    private final Map<String, String> attributes;

    /**
     * Constructs a MetricEvent object using the Builder pattern.
     *
     * @param builder the {@link Builder} instance containing the initialized values
     *                for the MetricEvent's fields. The Builder ensures that required
     *                fields such as eventType, sessionId, and deviceId are set, and
     *                provides default values for optional fields like unit and attributes.
     */
    private MetricEvent(Builder builder) {
        this.eventType = builder.eventType;
        this.value = builder.value;
        this.unit = builder.unit;
        this.timestamp = builder.timestamp;
        this.sessionId = builder.sessionId;
        this.deviceId = builder.deviceId;
        this.attributes = builder.attributes;
    }

    public String getEventType() {
        return eventType;
    }

    public double getValue() {
        return value;
    }

    public String getUnit() {
        return unit;
    }

    public long getTimestamp() {
        return timestamp;
    }

    public UUID getSessionId() {
        return sessionId;
    }

    public String getDeviceId() {
        return deviceId;
    }

    public Map<String, String> getAttributes() {
        return attributes;
    }

    /**
     * Converts the current MetricEvent object into a JSONObject representation.
     *
     * The returned JSONObject contains key-value pairs for the metric's event type,
     * value, unit, timestamp, session ID, device ID, and a nested JSONObject
     * containing the attributes associated with the event.
     *
     * @return a JSONObject representation of the MetricEvent.
     * @throws JSONException if an error occurs during JSON object creation or population.
     */
    public JSONObject toJson() throws JSONException {
        JSONObject json = new JSONObject();
        json.put("event_type", eventType);
        json.put("value", value);
        json.put("unit", unit);
        json.put("timestamp", timestamp);
        json.put("session_id", sessionId.toString());
        json.put("device_id", deviceId);

        JSONObject attrs = new JSONObject();
        for (Map.Entry<String, String> entry : attributes.entrySet()) {
            attrs.put(entry.getKey(), entry.getValue());
        }

        json.put("attributes", attrs);
        return json;
    }

    /**
     * A Builder class for creating instances of {@code MetricEvent} with a fluent API.
     * The Builder ensures proper initialization of required fields and provides default
     * values for optional fields.
     */
    public static class Builder {
        private String eventType;
        private double value;
        private String unit;
        private long timestamp = System.currentTimeMillis();
        private UUID sessionId;
        private String deviceId;
        private Map<String, String> attributes = new HashMap<>();

        public Builder eventType(String eventType) {
            this.eventType = eventType;
            return this;
        }

        public Builder value(double value) {
            this.value = value;
            return this;
        }

        public Builder unit(String unit) {
            this.unit = unit;
            return this;
        }

        public Builder timestamp(long timestamp) {
            this.timestamp = timestamp;
            return this;
        }

        public Builder sessionId(UUID sessionId) {
            this.sessionId = sessionId;
            return this;
        }

        public Builder deviceId(String deviceId) {
            this.deviceId = deviceId;
            return this;
        }

        public Builder attribute(String key, String value) {
            this.attributes.put(key, value);
            return this;
        }

        public Builder attributes(Map<String, String> attributes) {
            if (attributes != null) {
                this.attributes.putAll(attributes);
            }
            return this;
        }

        /**
         * Builds and returns a fully initialized {@code MetricEvent} instance.
         *
         * The method validates that the required fields {@code eventType}, {@code sessionId},
         * and {@code deviceId} are properly set. If any of these fields is missing, an
         * {@link IllegalStateException} is thrown. Additionally, assigns a default value of
         * "count" to the {@code unit} field if it is not explicitly set.
         *
         * @return a new {@code MetricEvent} instance with the configured properties.
         * @throws IllegalStateException if {@code eventType}, {@code sessionId}, or
         *                               {@code deviceId} is not set.
         */
        public MetricEvent build() {
            if (eventType == null) {
                throw new IllegalStateException("eventType is required");
            }
            if (unit == null) {
                unit = "count";
            }
            if (sessionId == null) {
                throw new IllegalStateException("sessionId is required");
            }
            if (deviceId == null) {
                throw new IllegalStateException("deviceId is required");
            }

            return new MetricEvent(this);
        }
    }
}