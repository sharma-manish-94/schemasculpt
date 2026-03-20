package io.github.sharmanish.schemasculpt.util;

import java.util.concurrent.Callable;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.function.Supplier;

/**
 * Utility for executing blocking operations on virtual threads.
 *
 * <p>Virtual threads (JEP 444) allow blocking I/O to scale efficiently. Instead of blocking
 * platform threads (expensive), we block virtual threads (cheap). This is ideal for:
 * <ul>
 *   <li>WebClient .block() calls to AI service</li>
 *   <li>Database queries</li>
 *   <li>Any I/O-bound operation</li>
 * </ul>
 *
 * <p>Usage:
 * <pre>{@code
 * // Instead of:
 * Response response = webClient.get().retrieve().bodyToMono(Response.class).block();
 *
 * // Use:
 * Response response = VirtualThreads.executeBlocking(executor,
 *     () -> webClient.get().retrieve().bodyToMono(Response.class).block());
 * }</pre>
 */
public final class VirtualThreads {

  private VirtualThreads() {
    // Utility class
  }

  /**
   * Executes a blocking operation on a virtual thread and waits for the result.
   *
   * @param executor The virtual thread executor
   * @param supplier The blocking operation to execute
   * @param <T> The return type
   * @return The result of the operation
   * @throws RuntimeException if the operation fails
   */
  public static <T> T executeBlocking(ExecutorService executor, Supplier<T> supplier) {
    try {
      return CompletableFuture.supplyAsync(supplier, executor).join();
    } catch (Exception e) {
      if (e.getCause() instanceof RuntimeException re) {
        throw re;
      }
      throw new RuntimeException("Virtual thread execution failed", e);
    }
  }

  /**
   * Executes a blocking operation on a virtual thread asynchronously.
   *
   * @param executor The virtual thread executor
   * @param supplier The blocking operation to execute
   * @param <T> The return type
   * @return CompletableFuture with the result
   */
  public static <T> CompletableFuture<T> executeAsync(
      ExecutorService executor, Supplier<T> supplier) {
    return CompletableFuture.supplyAsync(supplier, executor);
  }

  /**
   * Executes a void blocking operation on a virtual thread.
   *
   * @param executor The virtual thread executor
   * @param runnable The blocking operation to execute
   */
  public static void executeBlockingVoid(ExecutorService executor, Runnable runnable) {
    try {
      CompletableFuture.runAsync(runnable, executor).join();
    } catch (Exception e) {
      if (e.getCause() instanceof RuntimeException re) {
        throw re;
      }
      throw new RuntimeException("Virtual thread execution failed", e);
    }
  }
}
