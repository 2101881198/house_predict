package com.example.housepredict.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "houses_predictresult")
public class PredictResult extends BaseEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "house_id")
    private House house;

    @Column(name = "input_features", columnDefinition = "TEXT", nullable = false)
    private String inputFeatures;

    @Column(name = "predicted_price", nullable = false, precision = 10, scale = 2)
    private BigDecimal predictedPrice;

    @Column(name = "predicted_unit_price", nullable = false, precision = 10, scale = 2)
    private BigDecimal predictedUnitPrice;

    @Column(name = "model_name", nullable = false, length = 100)
    private String modelName;

    @Column(name = "predict_time")
    private LocalDateTime predictTime = LocalDateTime.now();

    public Long getId() { return id; }
    public String getInputFeatures() { return inputFeatures; }
    public void setInputFeatures(String inputFeatures) { this.inputFeatures = inputFeatures; }
    public BigDecimal getPredictedPrice() { return predictedPrice; }
    public void setPredictedPrice(BigDecimal predictedPrice) { this.predictedPrice = predictedPrice; }
    public BigDecimal getPredictedUnitPrice() { return predictedUnitPrice; }
    public void setPredictedUnitPrice(BigDecimal predictedUnitPrice) { this.predictedUnitPrice = predictedUnitPrice; }
    public String getModelName() { return modelName; }
    public void setModelName(String modelName) { this.modelName = modelName; }
    public LocalDateTime getPredictTime() { return predictTime; }
    public void setPredictTime(LocalDateTime predictTime) { this.predictTime = predictTime; }
}
