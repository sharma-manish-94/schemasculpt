import org.springframework.boot.gradle.tasks.bundling.BootJar

plugins {
    java
    id("org.springframework.boot") version "4.0.0"
    id("io.spring.dependency-management") version "1.1.7"
    id("com.diffplug.spotless") version "7.0.3"
    checkstyle
    pmd
    jacoco
    id("com.github.spotbugs") version "6.1.4"
    id("org.owasp.dependencycheck") version "12.1.1"
    id("org.springdoc.openapi-gradle-plugin") version "1.9.0"
}

group = "io.github.sharma-manish-94"
version = "0.0.1-SNAPSHOT"
description = "Backend API for the SchemaSculpt OpenAPI editor."

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(21)
    }
}

configurations {
    compileOnly {
        extendsFrom(configurations.annotationProcessor.get())
    }
}

repositories {
    mavenCentral()
    maven {
        url = uri("https://repository-master.mulesoft.org/nexus/content/groups/releases-group/")
    }
}

// Dependency versions management
extra["testcontainersVersion"] = "1.21.3"
extra["jacksonVersion"] = "3.0.3"

dependencies {
    // Spring Boot Starters
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.springframework.boot:spring-boot-starter-webmvc")
    implementation("org.springframework.boot:spring-boot-starter-validation")
    implementation("org.springframework.boot:spring-boot-starter-webflux")
    implementation("org.springframework.boot:spring-boot-starter-websocket")
    implementation("org.springframework.boot:spring-boot-starter-data-redis")
    implementation("org.springframework.boot:spring-boot-starter-security")
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    implementation("org.springframework.boot:spring-boot-starter-oauth2-client")

    // Lombok
    compileOnly("org.projectlombok:lombok")
    annotationProcessor("org.projectlombok:lombok")

    // Jackson
    implementation(platform("tools.jackson:jackson-bom:${property("jacksonVersion")}"))
    implementation("tools.jackson.core:jackson-databind")

    // Database
    runtimeOnly("org.postgresql:postgresql")
    implementation("org.flywaydb:flyway-core")
    runtimeOnly("org.flywaydb:flyway-database-postgresql")

    // JWT Support
    implementation("io.jsonwebtoken:jjwt-api:0.13.0")
    runtimeOnly("io.jsonwebtoken:jjwt-impl:0.13.0")
    runtimeOnly("io.jsonwebtoken:jjwt-jackson:0.13.0")

    // OpenAPI & JSON Tools
    implementation("io.swagger.parser.v3:swagger-parser:2.1.36")
    implementation("com.github.java-json-tools:json-patch:1.13")

    // Graph & Analytics
    implementation("org.jgrapht:jgrapht-core:1.5.2")
    implementation("org.apache.commons:commons-text:1.10.0")
    implementation("org.apache.commons:commons-math3:3.6.1")

    // Testing
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testImplementation("org.springframework.boot:spring-boot-starter-webmvc-test")
    testImplementation("org.springframework.security:spring-security-test")
    testImplementation(platform("org.testcontainers:testcontainers-bom:${property("testcontainersVersion")}"))
    testImplementation("org.testcontainers:testcontainers")
    testImplementation("org.testcontainers:junit-jupiter")

    // SpotBugs annotations for static analysis
    compileOnly("com.github.spotbugs:spotbugs-annotations:4.8.6")
}

// ============================================
// JAVA COMPILATION
// ============================================
tasks.withType<JavaCompile> {
    options.release = 21
    options.compilerArgs.add("-Xlint:unchecked")
}

// ============================================
// SPRING BOOT CONFIGURATION
// ============================================
springBoot {
    mainClass = "io.github.sharmanish.schemasculpt.SchemaSculptApiApplication"
}

// ============================================
// TESTING CONFIGURATION
// ============================================
tasks.test {
    useJUnitPlatform()
    finalizedBy(tasks.jacocoTestReport) // Generate coverage report after tests
}

// Integration tests task (equivalent to Maven Failsafe)
val integrationTest by tasks.registering(Test::class) {
    description = "Runs integration tests"
    group = "verification"

    useJUnitPlatform {
        includeTags("integration")
    }

    shouldRunAfter(tasks.test)
    finalizedBy(tasks.jacocoTestReport)
}

tasks.check {
    dependsOn(integrationTest)
}

// ============================================
// SPOTLESS - CODE FORMATTING
// ============================================
spotless {
    java {
        target("src/**/*.java")
        googleJavaFormat("1.25.2").aosp().reflowLongStrings()
        endWithNewline()
        importOrder()
    }
}

// ============================================
// CHECKSTYLE - CODE QUALITY
// ============================================
checkstyle {
    toolVersion = "10.26.1"
    configFile = file("checkstyle.xml")
    isIgnoreFailures = false
    maxWarnings = 0
}

tasks.withType<Checkstyle> {
    // Skip checkstyle (matches Maven config: <skip>true</skip>)
    enabled = false
    reports {
        xml.required = true
        html.required = true
    }
}

// ============================================
// PMD - CODE QUALITY ANALYSIS
// ============================================
pmd {
    toolVersion = "7.7.0"
    isConsoleOutput = true
    ruleSetFiles = files("pmd-ruleset.xml")
    ruleSets = listOf() // Clear default rulesets since we're using custom
    isIgnoreFailures = false
}

tasks.withType<Pmd> {
    reports {
        xml.required = true
        html.required = true
    }
}

// ============================================
// SPOTBUGS - BUG DETECTION
// ============================================
spotbugs {
    effort = com.github.spotbugs.snom.Effort.MAX
    reportLevel = com.github.spotbugs.snom.Confidence.LOW
    excludeFilter = file("spotbugs-exclude.xml")
    showProgress = true
}

tasks.withType<com.github.spotbugs.snom.SpotBugsTask> {
    reports.create("html") {
        required = true
        setStylesheet("fancy-hist.xsl")
    }
    reports.create("xml") {
        required = true
    }
}

dependencies {
    // Add FindSecBugs plugin for security vulnerability detection
    spotbugs("com.github.spotbugs:spotbugs:4.8.6")
    spotbugsPlugins("com.h3xstream.findsecbugs:findsecbugs-plugin:1.14.0")
}

// ============================================
// JACOCO - CODE COVERAGE
// ============================================
jacoco {
    toolVersion = "0.8.14"
}

tasks.jacocoTestReport {
    dependsOn(tasks.test, integrationTest)

    reports {
        xml.required = true
        html.required = true
    }

    // Aggregate coverage from both unit and integration tests
    executionData.setFrom(
        fileTree(layout.buildDirectory.get().asFile) {
            include("jacoco/*.exec")
        }
    )
}

tasks.jacocoTestCoverageVerification {
    dependsOn(tasks.jacocoTestReport)

    violationRules {
        rule {
            limit {
                counter = "LINE"
                value = "COVEREDRATIO"
                minimum = "0.50".toBigDecimal()
            }
        }
    }
}

tasks.check {
    dependsOn(tasks.jacocoTestCoverageVerification)
}

// ============================================
// OWASP DEPENDENCY CHECK
// ============================================
dependencyCheck {
    format = org.owasp.dependencycheck.reporting.ReportGenerator.Format.ALL.toString()
    failBuildOnCVSS = 7f
    skipConfigurations = listOf("compileClasspath", "runtimeClasspath")
    suppressionFile = "owasp-suppressions.xml" // Optional: create if needed
    analyzers.assemblyEnabled = false
}

// ============================================
// GRADLE BUILD SCANS (OPTIONAL BUT USEFUL)
// ============================================
// Uncomment to enable build scans for performance insights
// plugins.apply("com.gradle.enterprise")
// gradleEnterprise {
//     buildScan {
//         termsOfServiceUrl = "https://gradle.com/terms-of-service"
//         termsOfServiceAgree = "yes"
//     }
// }

// ============================================
// CUSTOM TASKS
// ============================================

// Task to format all code (equivalent to format-java.sh)
tasks.register("formatAll") {
    description = "Format all Java code using Spotless"
    group = "formatting"
    dependsOn("spotlessApply")
}

// Task to run all quality checks
tasks.register("qualityCheck") {
    description = "Run all code quality checks (Checkstyle, PMD, SpotBugs)"
    group = "verification"
    dependsOn(
        tasks.checkstyleMain,
        tasks.checkstyleTest,
        tasks.pmdMain,
        tasks.pmdTest,
        tasks.spotbugsMain,
        tasks.spotbugsTest
    )
}

// ============================================
// DEPENDENCY VERIFICATION & ENFORCEMENT
// (Equivalent to Maven Enforcer Plugin)
// ============================================

// Dependency resolution strategy
configurations.all {
    resolutionStrategy {
        // Use preferProjectModules() to prefer project modules over external deps
        preferProjectModules()

        // Cache dynamic versions for 24 hours
        cacheDynamicVersionsFor(24, "hours")

        // Don't cache changing modules
        cacheChangingModulesFor(0, "seconds")
    }
}

// Check for Java version at build time (equivalent to requireJavaVersion)
tasks.register("enforceJavaVersion") {
    description = "Enforce minimum Java version requirement"
    group = "verification"

    doLast {
        val javaVersion = JavaVersion.current()
        val requiredVersion = JavaVersion.VERSION_21

        if (javaVersion < requiredVersion) {
            throw GradleException(
                "Java version $javaVersion is not supported. " +
                "Minimum required version is $requiredVersion. " +
                "Current version: $javaVersion"
            )
        }
        println("✓ Java version check passed: $javaVersion")
    }
}

// Check for Gradle version (equivalent to requireMavenVersion)
tasks.register("enforceGradleVersion") {
    description = "Enforce minimum Gradle version requirement"
    group = "verification"

    doLast {
        val currentVersion = GradleVersion.current()
        val requiredVersion = GradleVersion.version("8.5")

        if (currentVersion < requiredVersion) {
            throw GradleException(
                "Gradle version ${currentVersion.version} is not supported. " +
                "Minimum required version is ${requiredVersion.version}. " +
                "Please update your Gradle wrapper."
            )
        }
        println("✓ Gradle version check passed: ${currentVersion.version}")
    }
}

// Run enforcer checks before build
tasks.named("compileJava") {
    dependsOn("enforceJavaVersion", "enforceGradleVersion")
}

// ============================================
// SPRINGDOC OPENAPI GENERATION
// ============================================
openApi {
    apiDocsUrl.set("http://localhost:8080/v3/api-docs")
    outputDir.set(layout.buildDirectory.dir("openapi"))
    outputFileName.set("openapi.json")
    waitTimeInSeconds.set(60)
}
