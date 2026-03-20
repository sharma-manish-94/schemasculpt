plugins {
    java
    id("org.springframework.boot") version "4.0.2"
    id("io.spring.dependency-management") version "1.1.7"
    id("com.diffplug.spotless") version "8.4.0"
    checkstyle
    pmd
    jacoco
    id("com.github.spotbugs") version "6.1.7"
    id("org.owasp.dependencycheck") version "12.2.0"
    id("org.springdoc.openapi-gradle-plugin") version "1.9.0"
    id("org.openrewrite.rewrite") version "latest.release"
}


group = "io.github.sharma-manish-94"
version = "0.0.1-SNAPSHOT"
description = "Backend API for the SchemaSculpt OpenAPI editor."


java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(25)
    }
}

// ============================================
// BUILD ENVIRONMENT DETECTION
// ============================================
// Lets you tighten quality gates in CI while staying
// fast in local development. Set CI=true in your
// pipeline (GitHub Actions / Jenkins do this automatically).
val isCI: Boolean = System.getenv("CI")?.toBoolean() ?: false

// ============================================
// VERSION CATALOG
// ============================================
val versions = mapOf(
    "testcontainers" to "1.21.3",
    "jackson" to "3.0.3",
    "jjwt" to "0.13.0",
    "swaggerParser" to "2.1.39",
    "jgrapht" to "1.5.2",
    "commonsText" to "1.13.0",
    "commonsMath3" to "3.6.1",
    "spotbugsCore" to "4.9.3",
    "findsecbugs" to "1.14.0",
    "jacoco" to "0.8.14",
    "checkstyle" to "10.26.1",
    "pmd" to "7.7.0"
)

// ============================================
// CONFIGURATIONS
// ============================================
configurations {
    compileOnly {
        extendsFrom(configurations.annotationProcessor.get())
    }
    // Align jackson-bom across all configurations to prevent
    // NoSuchMethodError when owasp dependency-check pulls in
    // an older jackson version via transitive resolution.
    all {
        resolutionStrategy.eachDependency {
            if (requested.group == "tools.jackson") {
                useVersion(versions["jackson"]!!)
                because("Pin Jackson 3 BOM to prevent transitive version conflicts")
            }
        }
    }
}

// ============================================
// REPOSITORIES
// ============================================
repositories {
    mavenCentral()
    maven {
        name = "mulesoft-releases"
        url = uri("https://repository-master.mulesoft.org/nexus/content/groups/releases-group/")
        content {
            // Only resolve dependencies whose group starts with com.mulesoft or org.mule
            includeGroupByRegex("(com\\.mulesoft|org\\.mule).*")
        }
    }
}

// ============================================
// DEPENDENCIES
// ============================================
dependencies {

    // ----- Spring Boot Starters -----
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.springframework.boot:spring-boot-starter-validation")
    implementation("org.springframework.boot:spring-boot-starter-webflux")
    implementation("org.springframework.boot:spring-boot-starter-websocket")
    implementation("org.springframework.boot:spring-boot-starter-data-redis")
    implementation("org.springframework.boot:spring-boot-starter-security")
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    implementation("org.springframework.boot:spring-boot-starter-oauth2-client")

    // ----- Lombok -----
    compileOnly("org.projectlombok:lombok")
    annotationProcessor("org.projectlombok:lombok")
    testCompileOnly("org.projectlombok:lombok")
    testAnnotationProcessor("org.projectlombok:lombok")

    // ----- Jackson 3 (Spring Boot 4 moved to tools.jackson groupId) -----
    implementation(platform("tools.jackson:jackson-bom:${versions["jackson"]}"))
    implementation("tools.jackson.core:jackson-databind")

    // ----- Database -----
    runtimeOnly("org.postgresql:postgresql")
    implementation("org.flywaydb:flyway-core")
    runtimeOnly("org.flywaydb:flyway-database-postgresql")

    // ----- JWT -----
    implementation("io.jsonwebtoken:jjwt-api:${versions["jjwt"]}")
    runtimeOnly("io.jsonwebtoken:jjwt-impl:${versions["jjwt"]}")
    runtimeOnly("io.jsonwebtoken:jjwt-jackson:${versions["jjwt"]}")

    // ----- OpenAPI / Swagger -----
    implementation("io.swagger.parser.v3:swagger-parser:${versions["swaggerParser"]}")

    // ----- JSON Patch (RFC 6902) -----
    implementation("com.github.java-json-tools:json-patch:1.13")

    // ----- Graph & Analytics -----
    implementation("org.jgrapht:jgrapht-core:${versions["jgrapht"]}")
    implementation("org.apache.commons:commons-text:${versions["commonsText"]}")
    implementation("org.apache.commons:commons-math3:${versions["commonsMath3"]}")

    // ----- OWASP dependency-check transitive pins -----
    // dependency-check-gradle 9.x+ can conflict with older jackson/commons-text
    // pulled in by other plugins. Pinning here keeps the build deterministic.
    constraints {
        add("implementation", "tools.jackson:jackson-bom:${versions["jackson"]}") {
            because("owasp dependency-check transitively pulls older versions")
        }
        add("implementation", "org.apache.commons:commons-text:${versions["commonsText"]}") {
            because("owasp dependency-check requires 1.13.x+")
        }
    }

    // ----- Testing -----
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testImplementation("org.springframework.security:spring-security-test")
    testImplementation(platform("org.testcontainers:testcontainers-bom:${versions["testcontainers"]}"))
    testImplementation("org.testcontainers:testcontainers")
    testImplementation("org.testcontainers:junit-jupiter")
    testImplementation("org.testcontainers:postgresql")

    // ----- Static Analysis Annotations -----
    compileOnly("com.github.spotbugs:spotbugs-annotations:${versions["spotbugsCore"]}")

    // ----- SpotBugs + FindSecBugs -----
    spotbugs("com.github.spotbugs:spotbugs:${versions["spotbugsCore"]}")
    spotbugsPlugins("com.h3xstream.findsecbugs:findsecbugs-plugin:${versions["findsecbugs"]}")
}

// ============================================
// COMPILE OPTIONS
// ============================================
tasks.withType<JavaCompile> {
    options.release = 25
    options.compilerArgs.addAll(
        listOf(
            "-Xlint:unchecked",
            "-Xlint:deprecation",
            "-parameters"           // needed for Spring MVC parameter name discovery
        )
    )
    options.isIncremental = true
}

// ============================================
// SPRING BOOT APPLICATION
// ============================================
springBoot {
    mainClass = "io.github.sharmanish.schemasculpt.SchemaSculptApiApplication"
}

// ============================================
// TEST CONFIGURATION
// ============================================
tasks.test {
    useJUnitPlatform {
        excludeTags("integration")  // unit tests only in the default `test` task
    }
    maxParallelForks = (Runtime.getRuntime().availableProcessors() / 2).coerceAtLeast(1)
    jvmArgs("-Xmx512m", "-XX:+UseG1GC")
    finalizedBy(tasks.jacocoTestReport)
    testLogging {
        events("passed", "skipped", "failed")
    }
}

// ============================================
// INTEGRATION TESTS
// ============================================
val integrationTest by tasks.registering(Test::class) {
    description = "Runs integration tests (tagged 'integration')"
    group = "verification"

    testClassesDirs = sourceSets["test"].output.classesDirs
    classpath = sourceSets["test"].runtimeClasspath

    useJUnitPlatform {
        includeTags("integration")
    }

    // Testcontainers needs a working Docker socket — skip in CI if unavailable
    val dockerAvailable = file("/var/run/docker.sock").exists() || System.getenv("DOCKER_HOST") != null
    onlyIf { dockerAvailable }

    maxParallelForks = 1   // integration tests are typically resource-heavy
    jvmArgs("-Xmx1g")
    shouldRunAfter(tasks.test)
    finalizedBy(tasks.jacocoTestReport)
}

tasks.check {
    dependsOn(integrationTest)
}

// ============================================
// SPOTLESS — CODE FORMATTING
// ============================================
spotless {
    java {
        target("src/**/*.java")
        googleJavaFormat("1.25.2").reflowLongStrings()
        endWithNewline()
        importOrder()
        removeUnusedImports()
        trimTrailingWhitespace()
    }
}
tasks.named("spotlessCheck") {
    enabled = isCI
}

// ============================================
// CHECKSTYLE — CODE STYLE
// ============================================
checkstyle {
    toolVersion = versions["checkstyle"]!!
    configFile = file("config/checkstyle/checkstyle.xml")
    isIgnoreFailures = !isCI  // fail only in CI
    maxWarnings = 0
}

tasks.withType<Checkstyle> {
    reports {
        xml.required = true
        html.required = true
    }
}

// ============================================
// PMD — CODE QUALITY
// ============================================
pmd {
    toolVersion = versions["pmd"]!!
    isConsoleOutput = true
    ruleSetFiles = files("config/pmd/pmd-ruleset.xml")
    ruleSets = listOf()
    isIgnoreFailures = !isCI  // fail only in CI
}

tasks.withType<Pmd> {
    reports {
        xml.required = true
        html.required = true
    }
}

// ============================================
// SPOTBUGS — BUG DETECTION
// ============================================
spotbugs {
    effort = com.github.spotbugs.snom.Effort.MAX
    reportLevel = com.github.spotbugs.snom.Confidence.LOW
    excludeFilter = file("config/spotbugs/spotbugs-exclude.xml")
    showProgress = true
    ignoreFailures = !isCI
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

// ============================================
// JACOCO — CODE COVERAGE
// ============================================
jacoco {
    toolVersion = versions["jacoco"]!!
}

tasks.jacocoTestReport {
    dependsOn(tasks.test, integrationTest)

    reports {
        xml.required = true
        html.required = true
    }

    executionData.setFrom(
        fileTree(layout.buildDirectory.get().asFile) {
            include("jacoco/*.exec")
        })
}

tasks.jacocoTestCoverageVerification {
    dependsOn(tasks.jacocoTestReport)

    violationRules {
        rule {
            limit {
                counter = "LINE"
                value = "COVEREDRATIO"
                // TODO: Raise incrementally — target 0.70 for production readiness.
                // Current relaxed threshold to unblock initial CI pipeline.
                minimum = if (isCI) "0.40".toBigDecimal() else "0.20".toBigDecimal()
            }
        }
        rule {
            limit {
                counter = "BRANCH"
                value = "COVEREDRATIO"
                minimum = if (isCI) "0.30".toBigDecimal() else "0.10".toBigDecimal()
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
// NOTE: The NVD API enforces rate limits. Set NVD_API_KEY in your
// environment / CI secrets to avoid throttling on first run.
dependencyCheck {
    format = org.owasp.dependencycheck.reporting.ReportGenerator.Format.ALL.toString()
    failBuildOnCVSS = if (isCI) 4f else 7f  // stricter in CI
    suppressionFile = "config/owasp/owasp-suppressions.xml"
    analyzers.assemblyEnabled = false

    // Configure NVD API key from environment (never hardcode secrets)
    nvd.apiKey = System.getenv("NVD_API_KEY") ?: ""

    // Skip configurations that do not ship to production
    skipConfigurations = listOf(
        "testCompileClasspath", "testRuntimeClasspath", "spotbugs", "spotbugsPlugins", "checkstyle", "pmd", "rewrite"
    )
}

// ============================================
// SPRINGDOC OPENAPI GENERATION
// ============================================
openApi {
    // Use an env var to support different environments (e.g. port randomization in CI).
    val apiPort = System.getenv("SERVER_PORT") ?: "8080"
    apiDocsUrl.set("http://localhost:$apiPort/v3/api-docs")
    outputDir.set(layout.buildDirectory.dir("openapi"))
    outputFileName.set("openapi.json")
    waitTimeInSeconds.set(60)
}

// ============================================
// DEPENDENCY RESOLUTION STRATEGY
// ============================================
configurations.all {
    resolutionStrategy {
        preferProjectModules()
        cacheDynamicVersionsFor(24, "hours")
        cacheChangingModulesFor(0, "seconds")

        eachDependency {
            // jsr305: spotbugs-annotations wants 3.0.2, old json-schema wants 2.0.1
            if (requested.group == "com.google.code.findbugs" && requested.name == "jsr305") {
                useVersion("3.0.2")
                because("Align jsr305 to highest safe version; 2.0.1 pulled by json-schema-validator")
            }
            // commons-io: swagger-parser 2.1.39 needs 2.20.0, other transitive deps want 2.15.1
            if (requested.group == "commons-io" && requested.name == "commons-io") {
                useVersion("2.20.0")
                because("swagger-parser requires 2.20.0; pin to avoid conflict with older transitive")
            }
            // Guava: swagger-core pulls android variant, Spring ecosystem pulls jre variant
            // Force the jre variant — you're on JDK 25, not Android
            if (requested.group == "com.google.guava" && requested.name == "guava") {
                useVersion("33.4.0-jre")
                because("Force JRE variant; swagger-core pulls android variant which lacks JRE APIs")
            }
            // error_prone_annotations: log4j 2.25.x pulls 2.38.0, guava pulls 2.21.1
            if (requested.group == "com.google.errorprone" && requested.name == "error_prone_annotations") {
                useVersion("2.38.0")
                because("Pin to highest; annotation-only jar, no behavioral difference between versions")
            }
        }
    }
}

// ============================================
// JVM VERSION ENFORCEMENT
// ============================================
tasks.register("enforceJavaVersion") {
    description = "Enforces minimum Java 25 toolchain requirement"
    group = "verification"
    doLast {
        val current = JavaVersion.current()
        val required = JavaVersion.VERSION_25
        check(current >= required) {
            "Java $current is unsupported. Minimum required: $required."
        }
        println("✓ Java version OK: $current")
    }
}

tasks.register("enforceGradleVersion") {
    description = "Enforces minimum Gradle 8.14 requirement"
    group = "verification"
    doLast {
        val current = GradleVersion.current()
        val required = GradleVersion.version("8.14")
        check(current >= required) {
            "Gradle ${current.version} is unsupported. Minimum required: ${required.version}."
        }
        println("✓ Gradle version OK: ${current.version}")
    }
}

tasks.named("compileJava") {
    dependsOn("enforceJavaVersion", "enforceGradleVersion")
}

// ============================================
// CUSTOM AGGREGATION TASKS
// ============================================
tasks.register("qualityCheck") {
    description = "Runs all static analysis tools (Checkstyle, PMD, SpotBugs)"
    group = "verification"
    dependsOn(
        tasks.checkstyleMain, tasks.checkstyleTest, tasks.pmdMain, tasks.pmdTest, tasks.spotbugsMain, tasks.spotbugsTest
    )
}

tasks.register("securityCheck") {
    description = "Runs OWASP dependency-check vulnerability scan"
    group = "verification"
    dependsOn("dependencyCheckAnalyze")
}

tasks.register("formatAll") {
    description = "Auto-formats all Java source files using Spotless"
    group = "formatting"
    dependsOn("spotlessApply")
}

// ============================================
// BUILD SUMMARY - config-cache compatible
// ============================================

abstract class BuildSummaryService
    : BuildService<BuildServiceParameters.None>, AutoCloseable {

    override fun close() {
        println("""
            ╔═══════════════════════════════════════╗
            ║  SchemaSculpt build complete          ║
            ║  Java   : ${JavaVersion.current()}
            ║  Gradle : ${GradleVersion.current().version}
            ╚═══════════════════════════════════════╝
        """.trimIndent())
    }
}

val buildSummary = gradle.sharedServices.registerIfAbsent(
    "buildSummary", BuildSummaryService::class
) {}

tasks.configureEach {
    usesService(buildSummary)
}

// Wire it so Gradle knows this service is "used" and calls close()
tasks.configureEach {
    usesService(buildSummary)
}
