package com.example.metricsdk;

import java.io.IOException;

import okhttp3.Interceptor;
import okhttp3.Response;

/**
 * An OkHttp interceptor that tracks HTTP request metrics such as latency and status codes.
 * This interceptor measures the time taken for each HTTP request and logs the metrics using
 * the MetricsSDK if it is initialized. The collected metrics are sent to a central metrics
 * collection service for further analysis.
 *
 * The following metrics are captured and tracked:
 * - HTTP status code: Indicates the result of the HTTP request (e.g., 200 for success, 404 for not found).
 * - Request latency: The time taken to complete the HTTP request, measured in milliseconds.
 *
 * If an error occurs during the request (e.g., network failure), a synthetic status code of 599 is logged,
 * along with the request latency.
 *
 * Usage of this interceptor requires that the MetricsSDK is properly initialized before the interceptor
 * processes any requests. If the MetricsSDK is not initialized, no metrics will be tracked.
 *
 * The interceptor performs the following steps:
 * 1. Records the start time of the HTTP request.
 * 2. Processes the request by proceeding with the OkHttp chain.
 * 3. Measures the request latency and logs the status code and latency to the MetricsSDK if it is available.
 * 4. If an IOException occurs during the request, logs the latency with a synthetic status code of 599.
 *
 * This interceptor is designed to be added to an OkHttpClient instance as part of its interceptor chain.
 */
public class MetricsOkHttpInterceptor implements Interceptor {

    /**
     * Intercepts and processes HTTP requests, measuring latency and logging metrics
     * such as status codes and request duration. This method tracks the HTTP request
     * metrics using the MetricsSDK if it is initialized. If an exception occurs during
     * the request, a synthetic status code of 599 is used to log the failure.
     *
     * @param chain the {@link Interceptor.Chain} object used to process the request and response
     * @return the {@link Response} object obtained after the request is processed
     * @throws IOException if an I/O error occurs during the request
     */
    @Override
    public Response intercept(Chain chain) throws IOException {
        long startNs = System.nanoTime();

        try {
            Response response = chain.proceed(chain.request());

            long latencyMs = (System.nanoTime() - startNs) / 1_000_000L;

            if (MetricsSDK.isInitialized()) {
                MetricsSDK.getCollector().trackHttpRequest(
                        response.code(),
                        latencyMs
                );
            }

            return response;
        } catch (IOException e) {
            long latencyMs = (System.nanoTime() - startNs) / 1_000_000L;

            if (MetricsSDK.isInitialized()) {
                MetricsSDK.getCollector().trackHttpRequest(
                        599,
                        latencyMs
                );
            }

            throw e;
        }
    }
}