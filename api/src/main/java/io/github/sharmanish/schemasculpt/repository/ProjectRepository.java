package io.github.sharmanish.schemasculpt.repository;

import io.github.sharmanish.schemasculpt.entity.Project;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ProjectRepository extends JpaRepository<Project, Long> {

  List<Project> findByUserIdOrderByCreatedAtDesc(Long userId);

  Optional<Project> findByUserIdAndName(Long userId, String name);

  List<Project> findByIsPublicTrue();

  boolean existsByUserIdAndName(Long userId, String name);
}
