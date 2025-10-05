package io.github.sharma_manish_94.schemasculpt_api.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "test_data_generation_history")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class TestDataGenerationHistory {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "project_id", nullable = false)
    private Project project;

    @Column(name = "data_type", nullable = false, length = 20)
    private String dataType; // 'test_cases' or 'mock_data'

    @Column(nullable = false, length = 500)
    private String path;

    @Column(nullable = false, length = 10)
    private String method;

    @Column(nullable = false)
    private Boolean success;

    @Column(name = "error_message", columnDefinition = "TEXT")
    private String errorMessage;

    @Column(name = "generation_time_ms")
    private Integer generationTimeMs;

    @Column(name = "cache_hit")
    private Boolean cacheHit = false;

    @Column(name = "created_at", updatable = false)
    @CreationTimestamp
    private LocalDateTime createdAt;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "created_by")
    private User createdBy;
}
