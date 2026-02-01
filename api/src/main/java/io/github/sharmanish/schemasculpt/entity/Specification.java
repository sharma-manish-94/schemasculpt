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

/** Specification entity representing a versioned OpenAPI specification. */
@Entity
@Table(name = "specifications")
@Getter
@Setter
@NoArgsConstructor
@ToString(exclude = {"project", "createdBy"})
public class Specification {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "project_id", nullable = false)
  private Project project;

  @Column(nullable = false, length = 50)
  private String version;

  @Column(name = "spec_content", columnDefinition = "TEXT", nullable = false)
  private String specContent;

  @Column(name = "spec_format", length = 10)
  private String specFormat = "json";

  @Column(name = "commit_message", columnDefinition = "TEXT")
  private String commitMessage;

  @Column(name = "is_current")
  private Boolean isCurrent = true;

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
    Specification that = (Specification) o;
    return id != null && Objects.equals(id, that.id);
  }

  @Override
  public int hashCode() {
    return getClass().hashCode();
  }
}
