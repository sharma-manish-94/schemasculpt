package io.github.sharma_manish_94.schemasculpt_api.repository;

import io.github.sharma_manish_94.schemasculpt_api.entity.Project;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ProjectRepository extends JpaRepository<Project, Long> {

    List<Project> findByUserIdOrderByCreatedAtDesc(Long userId);

    Optional<Project> findByUserIdAndName(Long userId, String name);

    List<Project> findByIsPublicTrue();

    boolean existsByUserIdAndName(Long userId, String name);
}
