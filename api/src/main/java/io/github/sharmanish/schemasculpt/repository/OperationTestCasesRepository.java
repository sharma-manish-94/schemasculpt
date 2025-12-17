package io.github.sharmanish.schemasculpt.repository;

import io.github.sharmanish.schemasculpt.entity.OperationTestCases;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface OperationTestCasesRepository extends JpaRepository<OperationTestCases, Long> {

  Optional<OperationTestCases> findByProject_IdAndPathAndMethod(
      Long projectId, String path, String method);

  List<OperationTestCases> findByProject_IdOrderByCreatedAtDesc(Long projectId);

  List<OperationTestCases> findBySpecification_IdOrderByCreatedAtDesc(Long specificationId);

  boolean existsByProject_IdAndPathAndMethodAndSpecHash(
      Long projectId, String path, String method, String specHash);

  void deleteByProject_Id(Long projectId);

  void deleteBySpecification_Id(Long specificationId);
}
