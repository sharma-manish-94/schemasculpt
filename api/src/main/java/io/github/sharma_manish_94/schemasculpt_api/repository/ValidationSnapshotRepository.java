package io.github.sharma_manish_94.schemasculpt_api.repository;

import io.github.sharma_manish_94.schemasculpt_api.entity.ValidationSnapshot;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ValidationSnapshotRepository extends JpaRepository<ValidationSnapshot, Long> {

  List<ValidationSnapshot> findBySpecificationIdOrderByCreatedAtDesc(Long specificationId);

  List<ValidationSnapshot> findTop10BySpecificationIdOrderByCreatedAtDesc(Long specificationId);
}
