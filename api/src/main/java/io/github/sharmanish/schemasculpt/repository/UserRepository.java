package io.github.sharmanish.schemasculpt.repository;

import io.github.sharmanish.schemasculpt.entity.User;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {

  Optional<User> findByGithubId(String githubId);

  Optional<User> findByUsername(String username);

  boolean existsByGithubId(String githubId);
}
