rootProject.name = "schemasculpt-api"

// Enable Gradle build cache for faster builds
buildCache {
    local {
        isEnabled = true
        directory = File(rootDir, ".gradle/build-cache")
        // removeUnusedEntriesAfterDays deprecated in Gradle 8.12+
    }
}

// Configure plugin repositories
pluginManagement {
    repositories {
        gradlePluginPortal()
        mavenCentral()
    }
}

// Configuration cache disabled - enable when Gradle daemon runs on Java 21
// enableFeaturePreview("STABLE_CONFIGURATION_CACHE")
