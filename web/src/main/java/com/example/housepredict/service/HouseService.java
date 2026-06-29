package com.example.housepredict.service;

import com.example.housepredict.dto.HouseQuery;
import com.example.housepredict.entity.House;
import com.example.housepredict.repository.HouseRepository;
import jakarta.persistence.criteria.JoinType;
import java.util.Map;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;

@Service
public class HouseService {
    private static final Map<String, String> SORT_FIELDS = Map.of(
            "total_price", "totalPrice",
            "unit_price", "unitPrice",
            "area", "area",
            "crawl_time", "crawlTime"
    );

    private final HouseRepository houseRepository;

    public HouseService(HouseRepository houseRepository) {
        this.houseRepository = houseRepository;
    }

    public Page<House> findHouses(HouseQuery query, int maxPageSize) {
        Sort sort = resolveSort(query.sort());
        Pageable pageable = PageRequest.of(query.safePage() - 1, query.safePageSize(maxPageSize), sort.and(Sort.by(Sort.Direction.DESC, "id")));
        return houseRepository.findAll(specification(query), pageable);
    }

    public Specification<House> specification(HouseQuery query) {
        return (root, criteriaQuery, cb) -> {
            if (criteriaQuery.getResultType() != Long.class && criteriaQuery.getResultType() != long.class) {
                root.fetch("city", JoinType.LEFT);
                root.fetch("district", JoinType.LEFT);
            }
            criteriaQuery.distinct(true);
            var predicate = cb.conjunction();
            if (hasText(query.city())) {
                if (query.city().chars().allMatch(Character::isDigit)) {
                    predicate = cb.and(predicate, cb.equal(root.get("city").get("id"), Long.parseLong(query.city())));
                } else {
                    predicate = cb.and(predicate, cb.equal(root.get("city").get("name"), query.city()));
                }
            }
            if (hasText(query.district())) {
                if (query.district().chars().allMatch(Character::isDigit)) {
                    predicate = cb.and(predicate, cb.equal(root.get("district").get("id"), Long.parseLong(query.district())));
                } else {
                    predicate = cb.and(predicate, cb.equal(root.get("district").get("name"), query.district()));
                }
            }
            if (hasText(query.roomType())) {
                predicate = cb.and(predicate, cb.equal(root.get("roomType"), query.roomType()));
            }
            if (hasText(query.decoration())) {
                predicate = cb.and(predicate, cb.equal(root.get("decoration"), query.decoration()));
            }
            if (query.minPrice() != null) {
                predicate = cb.and(predicate, cb.greaterThanOrEqualTo(root.get("totalPrice"), query.minPrice()));
            }
            if (query.maxPrice() != null) {
                predicate = cb.and(predicate, cb.lessThanOrEqualTo(root.get("totalPrice"), query.maxPrice()));
            }
            if (query.minArea() != null) {
                predicate = cb.and(predicate, cb.greaterThanOrEqualTo(root.get("area"), query.minArea()));
            }
            if (query.maxArea() != null) {
                predicate = cb.and(predicate, cb.lessThanOrEqualTo(root.get("area"), query.maxArea()));
            }
            return predicate;
        };
    }

    private Sort resolveSort(String rawSort) {
        String sort = hasText(rawSort) ? rawSort : "-crawl_time";
        boolean descending = sort.startsWith("-");
        String key = descending ? sort.substring(1) : sort;
        String property = SORT_FIELDS.getOrDefault(key, "crawlTime");
        return Sort.by(descending ? Sort.Direction.DESC : Sort.Direction.ASC, property);
    }

    private boolean hasText(String value) {
        return value != null && !value.isBlank();
    }
}
