# Maven to Gradle Migration Guide

This document explains the migration from Maven to Gradle for the SchemaSculpt API.

## What Changed

### Build Files Created

1. **`build.gradle.kts`** - Main build configuration (replaces `pom.xml`)
2. **`settings.gradle.kts`** - Project settings and build cache configuration
3. **`gradle.properties`** - Gradle build properties and JVM settings
4. **`gradlew` & `gradlew.bat`** - Gradle wrapper scripts
5. **`gradle/wrapper/`** - Gradle wrapper JAR and properties

### Configuration Highlights

#### Java Version
- **Changed from Java 25 to Java 21** (LTS)
- Java 21 is more stable and has better tooling support
- Gradle 8.14's Kotlin DSL has compatibility issues with Java 25

#### Gradle Version
- **Gradle 8.14** (required for Spring Boot 4.0.0)
- Configured with build cache for faster builds
- Parallel execution enabled

#### Build Tools Migrated

All Maven plugins have been migrated to their Gradle equivalents:

| Maven Plugin | Gradle Plugin | Status |
|-------------|---------------|--------|
| maven-compiler-plugin | Built-in Java plugin | ✅ |
| spring-boot-maven-plugin | org.springframework.boot | ✅ |
| spotless-maven-plugin | com.diffplug.spotless | ✅ |
| maven-checkstyle-plugin | checkstyle (disabled) | ⚠️ |
| spotbugs-maven-plugin | com.github.spotbugs | ✅ |
| maven-pmd-plugin | pmd | ✅ |
| dependency-check-maven | org.owasp.dependencycheck | ✅ |
| jacoco-maven-plugin | jacoco | ✅ |
| maven-enforcer-plugin | Custom tasks | ✅ |
| maven-surefire-plugin | Built-in test task | ✅ |
| maven-failsafe-plugin | Custom integrationTest task | ✅ |

⚠️ **Checkstyle is currently disabled** (matching Maven's `<skip>true</skip>` configuration)

## Using Gradle

### Basic Commands

Replace Maven commands with Gradle equivalents:

| Maven Command | Gradle Command | Description |
|--------------|----------------|-------------|
| `mvn clean` | `./gradlew clean` | Clean build artifacts |
| `mvn compile` | `./gradlew compileJava` | Compile Java code |
| `mvn test` | `./gradlew test` | Run unit tests |
| `mvn verify` | `./gradlew integrationTest` | Run integration tests |
| `mvn package` | `./gradlew bootJar` | Create executable JAR |
| `mvn install` | `./gradlew publishToMavenLocal` | Install to local Maven repo |

### Custom Tasks

New Gradle-specific tasks:

```bash
# Format all Java code
./gradlew formatAll

# Run all quality checks (Checkstyle, PMD, SpotBugs)
./gradlew qualityCheck

# Run with Java 21 (if needed)
JAVA_HOME="/c/Program Files/Java/jdk-21" ./gradlew build
```

### IDE Integration

#### IntelliJ IDEA
1. Open the `api` folder
2. IntelliJ will auto-detect the Gradle project
3. Click "Load Gradle Project" when prompted
4. Or: File → Open → Select `build.gradle.kts`

#### VS Code
1. Install "Gradle for Java" extension
2. Open the `api` folder
3. Use Command Palette → "Gradle: Reload"

## Key Differences from Maven

### 1. Build Cache
Gradle has a build cache enabled by default for faster incremental builds:
- Located in `.gradle/build-cache/`
- Caches task outputs between builds
- Much faster than Maven for repeated builds

### 2. Parallel Execution
Gradle runs tasks in parallel when possible:
- Configured in `gradle.properties`
- Can significantly speed up multi-module projects

### 3. Configuration Cache
Currently disabled due to Java 25 compatibility, but can be enabled later for even faster builds

### 4. Kotlin DSL
Using Kotlin DSL (`.kts` files) instead of Groovy:
- Type-safe build configuration
- Better IDE support with autocomplete
- More readable and maintainable

## Troubleshooting

### Issue: Gradle uses wrong Java version

**Solution:** Set JAVA_HOME explicitly:
```bash
export JAVA_HOME="/c/Program Files/Java/jdk-21"
./gradlew build
```

### Issue: Build cache issues

**Solution:** Clean the Gradle cache:
```bash
./gradlew clean --no-build-cache
rm -rf .gradle/build-cache
```

### Issue: Dependency resolution failures

**Solution:** Clear dependency cache:
```bash
./gradlew build --refresh-dependencies
```

### Issue: Gradle daemon issues

**Solution:** Stop all daemons:
```bash
./gradlew --stop
```

## Migration Checklist

- [x] Created `build.gradle.kts` with all dependencies
- [x] Migrated all Maven plugins to Gradle equivalents
- [x] Configured Gradle wrapper (8.14)
- [x] Updated `.gitignore` for Gradle artifacts
- [x] Updated CI/CD workflows to use Gradle
- [x] Tested compilation with Java 21
- [x] Created this migration guide
- [ ] Run full test suite with Gradle
- [ ] Fix any PMD/SpotBugs violations (if needed)
- [ ] Update team documentation
- [ ] Train team on Gradle usage

## Learning Resources

### Official Documentation
- [Gradle User Guide](https://docs.gradle.org/current/userguide/userguide.html)
- [Migrating from Maven](https://docs.gradle.org/current/userguide/migrating_from_maven.html)
- [Kotlin DSL Primer](https://docs.gradle.org/current/userguide/kotlin_dsl.html)

### Spring Boot with Gradle
- [Spring Boot Gradle Plugin](https://docs.spring.io/spring-boot/gradle-plugin/index.html)

### Best Practices
- Use `./gradlew` (wrapper) instead of system `gradle`
- Commit `gradle/wrapper/gradle-wrapper.jar` to version control
- Keep build scripts modular and well-commented
- Use build scans for performance insights: `./gradlew build --scan`

## Performance Comparison

Expected performance improvements over Maven:

| Operation | Maven | Gradle | Improvement |
|-----------|-------|--------|-------------|
| Clean build | ~2-3 min | ~1.5-2 min | ~30-40% |
| Incremental build | ~30-45s | ~10-15s | ~60-70% |
| No-op build | ~10s | ~2-3s | ~70-80% |

*Note: Actual times depend on hardware and project size*

## Next Steps

1. **Test thoroughly**: Run the full test suite and verify all tests pass
2. **Fix quality checks**: Address PMD and SpotBugs violations if you want to enable them
3. **Update documentation**: Ensure all team docs reference Gradle instead of Maven
4. **CI/CD verification**: Verify the updated GitHub Actions workflow works correctly
5. **Team training**: Share this guide with the team and conduct a knowledge transfer session

## Questions or Issues?

- Check the [Gradle Forums](https://discuss.gradle.org/)
- Review the [Gradle User Manual](https://docs.gradle.org/)
- Ask the team or create an issue in the repository

---

**Migration completed on**: December 25, 2024
**Gradle version**: 8.14
**Java version**: 21 (LTS)
