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
import jakarta.persistence.UniqueConstraint;
import java.time.LocalDateTime;
import java.util.Objects;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.annotations.UpdateTimestamp;
import org.hibernate.type.SqlTypes;

/** Entity storing cached test cases for API operations. */
@Entity
@Table(
    name = "operation_test_cases",
    uniqueConstraints =
        @UniqueConstraint(
            name = "unique_project_operation_tests",
            columnNames = {"project_id", "path", "method"}))
@Getter
@Setter
@NoArgsConstructor
@ToString(exclude = {"project", "specification", "createdBy"})
public class OperationTestCases {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "project_id", nullable = false)
  private Project project;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "specification_id")
  private Specification specification;

  @Column(nullable = false, length = 500)
  private String path;

  @Column(nullable = false, length = 10)
  private String method;

  @Column(columnDefinition = "TEXT")
  private String operationSummary;

  @JdbcTypeCode(SqlTypes.JSON)
  @Column(nullable = false, columnDefinition = "jsonb")
  private String testCases;

  @Column(name = "include_ai_tests")
  private Boolean includeAiTests = true;

  @Column(name = "total_tests", nullable = false)
  private Integer totalTests = 0;

  @Column(name = "spec_hash", nullable = false, length = 64)
  private String specHash;

  @Column(name = "created_at", updatable = false)
  @CreationTimestamp
  private LocalDateTime createdAt;

  @Column(name = "updated_at")
  @UpdateTimestamp
  private LocalDateTime updatedAt;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "created_by")
  private User createdBy;

  @Override
  public boolean equals(Object o) {
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;
    OperationTestCases that = (OperationTestCases) o;
    return id != null && Objects.equals(id, that.id);
  }

  @Override
  public int hashCode() {
    return getClass().hashCode();
  }
}
