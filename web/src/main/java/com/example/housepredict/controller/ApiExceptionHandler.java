package com.example.housepredict.controller;

import com.example.housepredict.dto.ApiResponse;
import jakarta.persistence.EntityNotFoundException;
import java.util.NoSuchElementException;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiExceptionHandler {
    @ExceptionHandler({NoSuchElementException.class, EntityNotFoundException.class})
    public ResponseEntity<ApiResponse<Object>> notFound() {
        return ResponseEntity.status(404).body(ApiResponse.error(404, "Not found"));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Object>> badRequest(MethodArgumentNotValidException ex) {
        return ResponseEntity.badRequest().body(ApiResponse.error(400, ex.getMessage()));
    }
}
