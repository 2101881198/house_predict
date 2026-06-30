package com.example.housepredict.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@TableName("houses_predictresult")
public class PredictResult extends BaseEntity {
    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("house_id")
    private Long houseId;

    @TableField(exist = false)
    private House house;

    @TableField("input_features")
    private String inputFeatures;

    @TableField("predicted_price")
    private BigDecimal predictedPrice;

    @TableField("predicted_unit_price")
    private BigDecimal predictedUnitPrice;

    @TableField("model_name")
    private String modelName;

    @TableField("predict_time")
    private LocalDateTime predictTime = LocalDateTime.now();

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getHouseId() { return houseId; }
    public void setHouseId(Long houseId) { this.houseId = houseId; }
    public House getHouse() { return house; }
    public void setHouse(House house) {
        this.house = house;
        this.houseId = house == null ? null : house.getId();
    }
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
