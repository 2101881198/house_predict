package com.example.housepredict.repository;

import com.example.housepredict.entity.CrawlTask;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CrawlTaskRepository extends JpaRepository<CrawlTask, Long> {
    List<CrawlTask> findTop100ByOrderByCreatedAtDesc();
}
