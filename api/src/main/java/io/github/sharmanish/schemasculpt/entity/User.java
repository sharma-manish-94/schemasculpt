package io.github.sharmanish.schemasculpt.entity;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
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
 * User entity representing authenticated users.
 *
 * <p>Note: equals/hashCode are based on the business key (githubId) to ensure proper JPA identity
 * semantics across entity state transitions.
 */
@Entity
@Table(name = "users")
@Getter
@Setter
@NoArgsConstructor
@ToString(exclude = "projects") // Exclude lazy collections from toString
public class User {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @Column(name = "github_id", unique = true, nullable = false)
  private String githubId;

  @Column(nullable = false)
  private String username;

  private String email;

  @Column(name = "avatar_url")
  private String avatarUrl;

  @Column(name = "created_at", updatable = false)
  @CreationTimestamp
  private LocalDateTime createdAt;

  @Column(name = "updated_at")
  @UpdateTimestamp
  private LocalDateTime updatedAt;

  @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, orphanRemoval = true)
  private List<Project> projects = new ArrayList<>();

  public User(Long id) {
    this.id = id;
  }

  /**
   * Equals based on business key (githubId) for proper JPA identity.
   * Per Hibernate best practices: use business key, not generated ID.
   */
  @Override
  public boolean equals(Object o) {
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;
    User user = (User) o;
    return githubId != null && Objects.equals(githubId, user.githubId);
  }

  /**
   * HashCode based on business key for consistency with equals.
   * Returns constant when githubId is null to maintain contract.
   */
  @Override
  public int hashCode() {
    return githubId != null ? Objects.hash(githubId) : getClass().hashCode();
  }
}
