package io.github.sharmanish.schemasculpt.config;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Configuration for Java 21 virtual threads.
 *
 * <p>Virtual threads are lightweight threads that dramatically reduce the cost of blocking
 * operations. They're ideal for I/O-bound tasks like HTTP calls to external services.
 *
 * <p>Reference: JEP 444 (Virtual Threads), JCIP Ch. 11 (Performance and Scalability)
 */
@Configuration
public class VirtualThreadConfig {

  /**
   * Creates an ExecutorService that creates a new virtual thread for each task. Virtual threads are
   * cheap to create and block, making them ideal for AI service calls.
   *
   * @return ExecutorService using virtual threads
   */
  @Bean(name = "virtualThreadExecutor")
  public ExecutorService virtualThreadExecutor() {
    return Executors.newVirtualThreadPerTaskExecutor();
  }
}
