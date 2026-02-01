package io.github.sharmanish.schemasculpt.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.time.LocalDateTime;
import java.util.Objects;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;
import org.hibernate.annotations.CreationTimestamp;

/** Entity tracking test data generation history for analytics. */
@Entity
@Table(name = "test_data_generation_history")
@Getter
@Setter
@NoArgsConstructor
@ToString(exclude = {"project", "createdBy"})
public class TestDataGenerationHistory {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "project_id", nullable = false)
  private Project project;

  @Column(name = "data_type", nullable = false, length = 20)
  private String dataType; // 'test_cases' or 'mock_data'

  @Column(nullable = false, length = 500)
  private String path;

  @Column(nullable = false, length = 10)
  private String method;

  @Column(nullable = false)
  private Boolean success;

  @Column(name = "error_message", columnDefinition = "TEXT")
  private String errorMessage;

  @Column(name = "generation_time_ms")
  private Integer generationTimeMs;

  @Column(name = "cache_hit")
  private Boolean cacheHit = false;

  @Column(name = "created_at", updatable = false)
  @CreationTimestamp
  private LocalDateTime createdAt;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "created_by")
  private User createdBy;

  @Override
  public boolean equals(Object o) {
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;
    TestDataGenerationHistory that = (TestDataGenerationHistory) o;
    return id != null && Objects.equals(id, that.id);
  }

  @Override
  public int hashCode() {
    return getClass().hashCode();
  }
}
