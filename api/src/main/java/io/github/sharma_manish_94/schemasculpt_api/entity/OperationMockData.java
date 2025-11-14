package io.github.sharma_manish_94.schemasculpt_api.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.annotations.UpdateTimestamp;
import org.hibernate.type.SqlTypes;

@Entity
@Table(
    name = "operation_mock_data",
    uniqueConstraints =
        @UniqueConstraint(
            name = "unique_project_operation_mock",
            columnNames = {"project_id", "path", "method", "response_code"}))
@Data
@NoArgsConstructor
@AllArgsConstructor
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
}
