plugins {
    alias(libs.plugins.android.library)
}

android {
    namespace = "com.example.metricsdk"
    compileSdk {
        version = release(36)
    }

    defaultConfig {
        minSdk = 21

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        consumerProguardFiles("consumer-rules.pro")
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
}

dependencies {
    implementation("com.squareup.okhttp3:okhttp:5.3.2")
    implementation(libs.core)

    testImplementation(libs.junit)
    testImplementation(libs.junit)
    testImplementation("org.robolectric:robolectric:4.15.1")
    testImplementation("org.mockito:mockito-core:5.18.0")
    testImplementation("com.squareup.okhttp3:mockwebserver3:5.3.2")

    androidTestImplementation(libs.ext.junit)
    androidTestImplementation(libs.espresso.core)
}