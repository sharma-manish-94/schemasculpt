package io.github.sharma_manish_94.schemasculpt_api.repository;

import io.github.sharma_manish_94.schemasculpt_api.entity.OperationMockData;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface OperationMockDataRepository extends JpaRepository<OperationMockData, Long> {

  Optional<OperationMockData> findByProject_IdAndPathAndMethodAndResponseCode(
      Long projectId, String path, String method, String responseCode);

  List<OperationMockData> findByProject_IdOrderByCreatedAtDesc(Long projectId);

  List<OperationMockData> findBySpecification_IdOrderByCreatedAtDesc(Long specificationId);

  boolean existsByProject_IdAndPathAndMethodAndResponseCodeAndSpecHash(
      Long projectId, String path, String method, String responseCode, String specHash);

  void deleteByProject_Id(Long projectId);

  void deleteBySpecification_Id(Long specificationId);
}
