# MetricSDK

MetricSDK is a lightweight Android Java SDK for collecting application performance, lifecycle, session, network, crash, and custom analytics metrics.

The SDK is designed to run inside Android applications with minimal setup. Metrics are batched in memory and periodically flushed to a configured backend API.

---

# Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Project Structure](#project-structure)
- [Installation](#installation)
  - [Option 1: Local AAR](#option-1-local-aar)
  - [Option 2: Local Gradle Module](#option-2-local-gradle-module)
  - [Option 3: Maven Dependency](#option-3-maven-dependency)
- [SDK Initialization](#sdk-initialization)
- [Automatic Tracking](#automatic-tracking)
- [Manual Metric Tracking](#manual-metric-tracking)
- [HTTP Tracking with OkHttp](#http-tracking-with-okhttp)
- [Batching and Retry Behaviour](#batching-and-retry-behaviour)
- [Permissions](#permissions)
- [Public API Reference](#public-api-reference)
- [ProGuard / R8](#proguard--r8)
- [Troubleshooting](#troubleshooting)
- [Production Recommendations](#production-recommendations)

---

# Features

MetricSDK automatically and manually collects:

| Metric | Description |
|---|---|
| App Start Time | Cold/warm app startup duration |
| Session Duration | Active application session duration |
| Screen Views | Activity name and time spent |
| HTTP Metrics | Request count, latency, and errors |
| Crash Metrics | Unhandled exceptions |
| ANR Metrics | Application Not Responding events |
| Memory Usage | Heap usage during flush |
| Battery Level | Device battery percentage |
| Network Type | WIFI, CELLULAR, or NONE |
| Frame Drops | UI rendering frame drops |
| Custom Events | Product and analytics events |

---

# Requirements

## SDK Requirements

- Android API 21+
- Java-based Android project
- Android Gradle Plugin-compatible library module

## Client App Requirements

- Android API 21+
- Internet permission
- Gradle-based Android application

---

# Project Structure

```text
MetricSDK/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/example/metricsdk/
│   │   │       ├── MetricsSDK.java
│   │   │       ├── MetricsCollector.java
│   │   │       ├── MetricEvent.java
│   │   │       ├── FlushManager.java
│   │   │       ├── DeviceInfoProvider.java
│   │   │       ├── NetworkTypeProvider.java
│   │   │       ├── MetricsOkHttpInterceptor.java
│   │   │       └── internal/
│   │   │           ├── AppLifecycleTracker.java
│   │   │           └── SessionManager.java
│   │   └── AndroidManifest.xml
│   ├── androidTest/
│   └── test/
├── build.gradle.kts
├── consumer-rules.pro
└── proguard-rules.pro
```

---

# SDK Initialization

Initialize the SDK once in your custom `Application` class.

```java
public class ClientApplication extends Application {

    @Override
    public void onCreate() {
        super.onCreate();

        MetricsSDK.init(
                this,
                "https://api.example.com/mobile-metrics",
                "YOUR_APP_TOKEN"
        );
    }
}
```

---

# Manual Metric Tracking

## Track Screen View

```java
MetricsSDK.getCollector()
        .trackScreenView("HomeActivity", 15_000L);
```

## Track HTTP Request

```java
MetricsSDK.getCollector()
        .trackHttpRequest(200, 320L);
```

## Track Crash

```java
try {
    riskyOperation();
} catch (Exception exception) {
    MetricsSDK.getCollector().trackCrash(exception);
}
```

## Track Custom Event

```java
MetricsSDK.getCollector()
        .trackCustomEvent("checkout_started", "true");
```

---

# HTTP Tracking with OkHttp

```java
OkHttpClient client = new OkHttpClient.Builder()
        .addInterceptor(new MetricsOkHttpInterceptor())
        .build();
```

---

# Batching and Retry Behaviour

MetricSDK flushes events:

- Every 30 seconds
- When 50 events are queued

Retry strategy:

| Attempt | Delay |
|---|---|
| 1 | Immediate |
| 2 | 1 second |
| 3 | 2 seconds |
| 4 | 4 seconds |

---

# Permissions

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

---

# ProGuard / R8

```proguard
-keep class com.example.metricsdk.** { *; }
-dontwarn com.example.metricsdk.*
```

---

# Troubleshooting

## SDK does not send events

Verify that:

- `MetricsSDK.init(...)` is called before tracking events
- The API URL is valid
- The app has internet permission
- The backend accepts JSON requests

---

# Production Recommendations

Consider adding:

- Persistent disk queue
- Offline retry support
- Payload compression
- SDK version metadata
- App version metadata
- ANR watchdog implementation
- Configurable batch size
- Unit and instrumentation tests
