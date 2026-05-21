package com.example.metricsdk;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;

/**
 * The NetworkTypeProvider class provides functionality to determine the type of active network
 * connection on a device.
 *
 * This class is designed to be utility-like and cannot be instantiated.
 */
class NetworkTypeProvider {

    /**
     * Private constructor for the NetworkTypeProvider class.
     *
     * This constructor prevents instantiation of the class, as all functionality
     * is provided through its static methods. The NetworkTypeProvider class is
     * intended to be used as a utility class.
     */
    private NetworkTypeProvider() {
    }

    /**
     * Determines the type of active network connection on the device.
     *
     * @param context the application context used to retrieve the current network status
     * @return a string representing the network type; "WIFI" if connected via WiFi,
     *         "CELLULAR" if connected via cellular data, or "NONE" if no active network is available
     */
    static String getNetworkType(Context context) {
        ConnectivityManager connectivityManager =
                (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);

        if (connectivityManager == null) {
            return "NONE";
        }

        Network network = connectivityManager.getActiveNetwork();

        if (network == null) {
            return "NONE";
        }

        NetworkCapabilities capabilities =
                connectivityManager.getNetworkCapabilities(network);

        if (capabilities == null) {
            return "NONE";
        }

        if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)) {
            return "WIFI";
        }

        if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)) {
            return "CELLULAR";
        }

        return "NONE";
    }
}