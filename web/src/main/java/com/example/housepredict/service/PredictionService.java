package com.example.housepredict.service;

import com.example.housepredict.dto.PredictRequest;
import com.example.housepredict.dto.PredictResponse;

public interface PredictionService {
    PredictResponse predict(PredictRequest request);
}
