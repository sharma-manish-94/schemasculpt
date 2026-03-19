package io.github.sharmanish.schemasculpt.controller;

import io.github.sharmanish.schemasculpt.exception.ValidationException;
import io.github.sharmanish.schemasculpt.util.LogSanitizer;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.InvalidPathException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * Controller for browsing local filesystem directories.
 *
 * <p>This endpoint is intentionally scoped to directory listing only (no file reads) to support the
 * local repository picker UI. It is safe for local development use.
 */
@RestController
@RequestMapping("/api/v1/filesystem")
@Slf4j
public class FilesystemController {

  private static final int MAX_ENTRIES = 500;

  @GetMapping("/browse")
  public ResponseEntity<Map<String, Object>> browse(@RequestParam(defaultValue = "") String path) {

    Path browsePath;

    if (path.isBlank()) {
      browsePath = Path.of(System.getProperty("user.home"));
    } else {
      try {
        browsePath = Path.of(path).normalize();
      } catch (InvalidPathException _) {
        throw new ValidationException("Invalid path: " + LogSanitizer.sanitize(path));
      }

      // Prevent path traversal
      String normalized = browsePath.toString();
      if (normalized.contains("..")) {
        throw new ValidationException("Path traversal not allowed.");
      }
    }

    File dir = browsePath.toFile();
    if (!dir.exists() || !dir.isDirectory()) {
      throw new ValidationException("Path does not exist or is not a directory.");
    }

    log.debug("Browsing filesystem path: {}", LogSanitizer.sanitize(browsePath.toString()));

    List<Map<String, String>> entries = new ArrayList<>();
    File[] children = dir.listFiles(File::isDirectory);

    if (children != null) {
      List<File> sorted = new ArrayList<>(List.of(children));
      sorted.sort(Comparator.comparing(f -> f.getName().toLowerCase()));

      for (File child : sorted) {
        if (entries.size() >= MAX_ENTRIES) break;
        // Skip hidden dirs except on root
        if (child.getName().startsWith(".")) continue;
        boolean readable = Files.isReadable(child.toPath());
        entries.add(
            Map.of(
                "name", child.getName(),
                "path", child.getAbsolutePath(),
                "readable", String.valueOf(readable)));
      }
    }

    // Compute parent path
    Path parent = browsePath.getParent();
    String parentPath = parent != null ? parent.toString() : "";

    return ResponseEntity.ok(
        Map.of(
            "currentPath", browsePath.toString(),
            "parentPath", parentPath,
            "entries", entries));
  }
}
