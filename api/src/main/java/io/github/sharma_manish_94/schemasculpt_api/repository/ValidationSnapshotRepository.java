package io.github.sharma_manish_94.schemasculpt_api.repository;

import io.github.sharma_manish_94.schemasculpt_api.entity.ValidationSnapshot;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ValidationSnapshotRepository extends JpaRepository<ValidationSnapshot, Long> {

    List<ValidationSnapshot> findBySpecificationIdOrderByCreatedAtDesc(Long specificationId);

    List<ValidationSnapshot> findTop10BySpecificationIdOrderByCreatedAtDesc(Long specificationId);
}
