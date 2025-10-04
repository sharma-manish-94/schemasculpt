package io.github.sharma_manish_94.schemasculpt_api.repository;

import io.github.sharma_manish_94.schemasculpt_api.entity.Specification;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface SpecificationRepository extends JpaRepository<Specification, Long> {

    List<Specification> findByProjectIdOrderByCreatedAtDesc(Long projectId);

    Optional<Specification> findByProjectIdAndVersion(Long projectId, String version);

    Optional<Specification> findByProjectIdAndIsCurrentTrue(Long projectId);

    long countByProjectId(Long projectId);

    boolean existsByProjectIdAndVersion(Long projectId, String version);

    @Modifying
    @Query("UPDATE Specification s SET s.isCurrent = false WHERE s.project.id = :projectId")
    void markAllAsNotCurrent(@Param("projectId") Long projectId);
}
