package io.github.sharma_manish_94.schemasculpt_api.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "specifications")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Specification {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "project_id", nullable = false)
    private Project project;

    @Column(nullable = false, length = 50)
    private String version;

    @Column(name = "spec_content", columnDefinition = "TEXT", nullable = false)
    private String specContent;

    @Column(name = "spec_format", length = 10)
    private String specFormat = "json";

    @Column(name = "commit_message", columnDefinition = "TEXT")
    private String commitMessage;

    @Column(name = "is_current")
    private Boolean isCurrent = true;

    @Column(name = "created_at", updatable = false)
    @CreationTimestamp
    private LocalDateTime createdAt;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "created_by")
    private User createdBy;
}
