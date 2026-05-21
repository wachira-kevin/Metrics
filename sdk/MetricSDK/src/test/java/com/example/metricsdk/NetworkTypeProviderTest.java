package com.example.metricsdk;

import static org.junit.Assert.assertEquals;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;

import org.junit.Test;

public class NetworkTypeProviderTest {

    @Test
    public void getNetworkType_whenConnectivityManagerIsNull_returnsNone() {
        Context context = mock(Context.class);

        when(context.getSystemService(Context.CONNECTIVITY_SERVICE)).thenReturn(null);

        String networkType = NetworkTypeProvider.getNetworkType(context);

        assertEquals("NONE", networkType);
    }

    @Test
    public void getNetworkType_whenActiveNetworkIsNull_returnsNone() {
        Context context = mock(Context.class);
        ConnectivityManager connectivityManager = mock(ConnectivityManager.class);

        when(context.getSystemService(Context.CONNECTIVITY_SERVICE)).thenReturn(connectivityManager);
        when(connectivityManager.getActiveNetwork()).thenReturn(null);

        String networkType = NetworkTypeProvider.getNetworkType(context);

        assertEquals("NONE", networkType);
    }

    @Test
    public void getNetworkType_whenCapabilitiesAreNull_returnsNone() {
        Context context = mock(Context.class);
        ConnectivityManager connectivityManager = mock(ConnectivityManager.class);
        Network network = mock(Network.class);

        when(context.getSystemService(Context.CONNECTIVITY_SERVICE)).thenReturn(connectivityManager);
        when(connectivityManager.getActiveNetwork()).thenReturn(network);
        when(connectivityManager.getNetworkCapabilities(network)).thenReturn(null);

        String networkType = NetworkTypeProvider.getNetworkType(context);

        assertEquals("NONE", networkType);
    }

    @Test
    public void getNetworkType_whenWifi_returnsWifi() {
        Context context = mock(Context.class);
        ConnectivityManager connectivityManager = mock(ConnectivityManager.class);
        Network network = mock(Network.class);
        NetworkCapabilities capabilities = mock(NetworkCapabilities.class);

        when(context.getSystemService(Context.CONNECTIVITY_SERVICE)).thenReturn(connectivityManager);
        when(connectivityManager.getActiveNetwork()).thenReturn(network);
        when(connectivityManager.getNetworkCapabilities(network)).thenReturn(capabilities);
        when(capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)).thenReturn(true);

        String networkType = NetworkTypeProvider.getNetworkType(context);

        assertEquals("WIFI", networkType);
    }

    @Test
    public void getNetworkType_whenCellular_returnsCellular() {
        Context context = mock(Context.class);
        ConnectivityManager connectivityManager = mock(ConnectivityManager.class);
        Network network = mock(Network.class);
        NetworkCapabilities capabilities = mock(NetworkCapabilities.class);

        when(context.getSystemService(Context.CONNECTIVITY_SERVICE)).thenReturn(connectivityManager);
        when(connectivityManager.getActiveNetwork()).thenReturn(network);
        when(connectivityManager.getNetworkCapabilities(network)).thenReturn(capabilities);
        when(capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)).thenReturn(false);
        when(capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)).thenReturn(true);

        String networkType = NetworkTypeProvider.getNetworkType(context);

        assertEquals("CELLULAR", networkType);
    }
}