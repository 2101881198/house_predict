package com.example.housepredict.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "houses_crawltask")
public class CrawlTask extends BaseEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "task_name", nullable = false, length = 100)
    private String taskName;

    @Column(name = "target_city", nullable = false, length = 50)
    private String targetCity;

    @Column(name = "target_district", length = 50)
    private String targetDistrict = "";

    @Column(name = "page_count")
    private Integer pageCount = 1;
    private String status = "pending";
    @Column(name = "success_count")
    private Integer successCount = 0;
    @Column(name = "fail_count")
    private Integer failCount = 0;
    @Column(name = "started_at")
    private LocalDateTime startedAt;
    @Column(name = "finished_at")
    private LocalDateTime finishedAt;

    @Column(columnDefinition = "TEXT")
    private String message = "";

    public Long getId() { return id; }
    public String getTaskName() { return taskName; }
    public void setTaskName(String taskName) { this.taskName = taskName; }
    public String getTargetCity() { return targetCity; }
    public void setTargetCity(String targetCity) { this.targetCity = targetCity; }
    public String getTargetDistrict() { return targetDistrict; }
    public void setTargetDistrict(String targetDistrict) { this.targetDistrict = targetDistrict; }
    public Integer getPageCount() { return pageCount; }
    public void setPageCount(Integer pageCount) { this.pageCount = pageCount; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public Integer getSuccessCount() { return successCount; }
    public void setSuccessCount(Integer successCount) { this.successCount = successCount; }
    public Integer getFailCount() { return failCount; }
    public void setFailCount(Integer failCount) { this.failCount = failCount; }
    public LocalDateTime getStartedAt() { return startedAt; }
    public void setStartedAt(LocalDateTime startedAt) { this.startedAt = startedAt; }
    public LocalDateTime getFinishedAt() { return finishedAt; }
    public void setFinishedAt(LocalDateTime finishedAt) { this.finishedAt = finishedAt; }
    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
}
