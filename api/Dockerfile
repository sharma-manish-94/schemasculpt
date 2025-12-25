# Multi-stage build for SchemaSculpt API
# Stage 1: Build the application
FROM gradle:8.14-jdk21-alpine AS builder

WORKDIR /app

# Copy Gradle configuration files
COPY build.gradle.kts settings.gradle.kts ./
COPY gradlew ./
COPY gradle ./gradle

# Create Docker-friendly gradle.properties (without Windows JAVA_HOME)
RUN echo "org.gradle.caching=true" > gradle.properties && \
    echo "org.gradle.parallel=true" >> gradle.properties && \
    echo "org.gradle.jvmargs=-Xmx2g -XX:+HeapDumpOnOutOfMemoryError -Dfile.encoding=UTF-8" >> gradle.properties && \
    echo "org.gradle.configuration-cache=true" >> gradle.properties && \
    echo "kotlin.incremental=true" >> gradle.properties && \
    echo "org.gradle.dependency.verification=lenient" >> gradle.properties && \
    echo "org.gradle.console=plain" >> gradle.properties && \
    echo "org.gradle.warning.mode=all" >> gradle.properties

# Download dependencies (cached layer)
RUN gradle dependencies --no-daemon || true

# Copy source code
COPY src ./src

# Build the application (skip tests for faster builds)
RUN gradle bootJar --no-daemon -x test

# Stage 2: Runtime image
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# Create non-root user for security
RUN addgroup -S spring && adduser -S spring -G spring

# Copy the built JAR from builder stage
COPY --from=builder /app/build/libs/*.jar app.jar

# Change ownership to non-root user
RUN chown -R spring:spring /app

USER spring

# Expose API port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health || exit 1

# Run the application
ENTRYPOINT ["java", "-jar", "app.jar"]
