package io.github.sharmanish.schemasculpt.entity;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

/**
 * Project entity representing a user's OpenAPI specification project.
 *
 * <p>Note: equals/hashCode use ID-based comparison with null-safety for proper JPA identity
 * semantics across entity state transitions.
 */
@Entity
@Table(name = "projects")
@Getter
@Setter
@NoArgsConstructor
@ToString(exclude = {"user", "specifications"}) // Exclude lazy relationships
public class Project {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "user_id", nullable = false)
  private User user;

  @Column(nullable = false)
  private String name;

  @Column(columnDefinition = "TEXT")
  private String description;

  @Column(name = "is_public")
  private Boolean isPublic = false;

  @Column(name = "created_at", updatable = false)
  @CreationTimestamp
  private LocalDateTime createdAt;

  @Column(name = "updated_at")
  @UpdateTimestamp
  private LocalDateTime updatedAt;

  @OneToMany(mappedBy = "project", cascade = CascadeType.ALL, orphanRemoval = true)
  private List<Specification> specifications = new ArrayList<>();

  /**
   * Equals based on ID for JPA identity. Returns false if ID is null (transient entity).
   */
  @Override
  public boolean equals(Object o) {
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;
    Project project = (Project) o;
    return id != null && Objects.equals(id, project.id);
  }

  /**
   * HashCode returns constant to maintain contract when ID is null.
   * Per Vlad Mihalcea's recommendations for JPA entities.
   */
  @Override
  public int hashCode() {
    return getClass().hashCode();
  }
}
