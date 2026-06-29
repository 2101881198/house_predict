package com.example.housepredict.repository;

import com.example.housepredict.entity.PredictResult;
import java.util.List;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PredictResultRepository extends JpaRepository<PredictResult, Long> {
    List<PredictResult> findByOrderByPredictTimeDesc(Pageable pageable);
}
