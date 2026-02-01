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

/** Entity storing cached mock data for API operations. */
@Entity
@Table(
    name = "operation_mock_data",
    uniqueConstraints =
        @UniqueConstraint(
            name = "unique_project_operation_mock",
            columnNames = {"project_id", "path", "method", "response_code"}))
@Getter
@Setter
@NoArgsConstructor
@ToString(exclude = {"project", "specification", "createdBy"})
public class OperationMockData {

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

  @Column(name = "response_code", length = 10)
  private String responseCode = "200";

  @JdbcTypeCode(SqlTypes.JSON)
  @Column(nullable = false, columnDefinition = "jsonb")
  private String mockVariations;

  @Column(name = "variation_count", nullable = false)
  private Integer variationCount = 3;

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
    OperationMockData that = (OperationMockData) o;
    return id != null && Objects.equals(id, that.id);
  }

  @Override
  public int hashCode() {
    return getClass().hashCode();
  }
}
