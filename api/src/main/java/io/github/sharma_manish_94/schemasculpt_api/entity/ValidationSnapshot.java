package io.github.sharma_manish_94.schemasculpt_api.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity
@Table(name = "validation_snapshots")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ValidationSnapshot {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "specification_id", nullable = false)
  private Specification specification;

  @Column(columnDefinition = "jsonb")
  @JdbcTypeCode(SqlTypes.JSON)
  private String errors;

  @Column(columnDefinition = "jsonb")
  @JdbcTypeCode(SqlTypes.JSON)
  private String suggestions;

  @Column(name = "created_at", updatable = false)
  @CreationTimestamp
  private LocalDateTime createdAt;
}
