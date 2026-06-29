package com.example.housepredict.service;

import com.example.housepredict.entity.City;
import com.example.housepredict.entity.CrawlTask;
import com.example.housepredict.entity.District;
import com.example.housepredict.entity.House;
import com.example.housepredict.repository.CityRepository;
import com.example.housepredict.repository.CrawlTaskRepository;
import com.example.housepredict.repository.DistrictRepository;
import com.example.housepredict.repository.HouseRepository;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class DemoDataService {
    private final CityRepository cityRepository;
    private final DistrictRepository districtRepository;
    private final HouseRepository houseRepository;
    private final CrawlTaskRepository crawlTaskRepository;

    public DemoDataService(CityRepository cityRepository, DistrictRepository districtRepository, HouseRepository houseRepository, CrawlTaskRepository crawlTaskRepository) {
        this.cityRepository = cityRepository;
        this.districtRepository = districtRepository;
        this.houseRepository = houseRepository;
        this.crawlTaskRepository = crawlTaskRepository;
    }

    @Transactional
    public int seedDemoData() {
        int created = 0;
        for (Map<String, String> row : rows()) {
            if (houseRepository.findBySourceUrl(row.get("sourceUrl")).isPresent()) {
                continue;
            }
            City city = cityRepository.findByName(row.get("city")).orElseGet(() -> {
                City newCity = new City();
                newCity.setName(row.get("city"));
                newCity.setProvince("山东省");
                return cityRepository.save(newCity);
            });
            District district = districtRepository.findByCityAndName(city, row.get("district")).orElseGet(() -> {
                District newDistrict = new District();
                newDistrict.setCity(city);
                newDistrict.setName(row.get("district"));
                return districtRepository.save(newDistrict);
            });
            House house = new House();
            house.setCity(city);
            house.setDistrict(district);
            house.setTitle(row.get("title"));
            house.setCommunity(row.get("community"));
            house.setTotalPrice(new BigDecimal(row.get("totalPrice")));
            house.setArea(new BigDecimal(row.get("area")));
            house.setUnitPrice(house.getTotalPrice().multiply(BigDecimal.valueOf(10000)).divide(house.getArea(), 2, java.math.RoundingMode.HALF_UP));
            house.setRoomType(row.get("roomType"));
            house.setFloor(row.get("floor"));
            house.setDirection(row.get("direction"));
            house.setDecoration(row.get("decoration"));
            house.setBuildYear(Integer.valueOf(row.get("buildYear")));
            house.setAddress(row.get("address"));
            house.setLongitude(new BigDecimal(row.get("longitude")));
            house.setLatitude(new BigDecimal(row.get("latitude")));
            house.setSurrounding(row.get("surrounding"));
            house.setSourceUrl(row.get("sourceUrl"));
            house.setCrawlTime(LocalDateTime.now().minusDays(created));
            houseRepository.save(house);
            created++;
        }
        return created;
    }

    @Transactional
    public CrawlTask runDemoCrawler(String city, String district, int pages) {
        CrawlTask task = new CrawlTask();
        task.setTaskName("示例采集-" + city);
        task.setTargetCity(city);
        task.setTargetDistrict(district == null ? "" : district);
        task.setPageCount(Math.max(pages, 1));
        task.setStatus("running");
        task.setStartedAt(LocalDateTime.now());
        crawlTaskRepository.save(task);
        int created = seedDemoData();
        task.setStatus("success");
        task.setSuccessCount(rows().size());
        task.setFailCount(0);
        task.setFinishedAt(LocalDateTime.now());
        task.setMessage("Processed bundled demo houses; imported " + created + " new houses.");
        return crawlTaskRepository.save(task);
    }

    private List<Map<String, String>> rows() {
        return List.of(
                row("济南", "历下区", "历下区精装三室", "泉城花园", "215", "96", "三室一厅", "中楼层", "南", "精装", "2015", "济南市历下区", "117.120128", "36.652069", "近地铁，近学校", "demo://jinan-lixia-1"),
                row("济南", "市中区", "市中区改善两室", "鲁能小区", "168", "82", "两室一厅", "高楼层", "南北", "简装", "2010", "济南市市中区", "116.997472", "36.651121", "生活便利", "demo://jinan-shizhong-1"),
                row("青岛", "市南区", "市南区海景房", "海岸名都", "390", "118", "三室两厅", "中楼层", "南", "精装", "2018", "青岛市市南区", "120.384428", "36.105215", "近海，商圈成熟", "demo://qingdao-shinan-1"),
                row("烟台", "芝罘区", "芝罘区刚需两室", "幸福里", "105", "76", "两室一厅", "低楼层", "东南", "简装", "2008", "烟台市芝罘区", "121.383188", "37.539297", "近市场", "demo://yantai-zhifu-1")
        );
    }

    private Map<String, String> row(
            String city,
            String district,
            String title,
            String community,
            String totalPrice,
            String area,
            String roomType,
            String floor,
            String direction,
            String decoration,
            String buildYear,
            String address,
            String longitude,
            String latitude,
            String surrounding,
            String sourceUrl) {
        return Map.ofEntries(
                Map.entry("city", city),
                Map.entry("district", district),
                Map.entry("title", title),
                Map.entry("community", community),
                Map.entry("totalPrice", totalPrice),
                Map.entry("area", area),
                Map.entry("roomType", roomType),
                Map.entry("floor", floor),
                Map.entry("direction", direction),
                Map.entry("decoration", decoration),
                Map.entry("buildYear", buildYear),
                Map.entry("address", address),
                Map.entry("longitude", longitude),
                Map.entry("latitude", latitude),
                Map.entry("surrounding", surrounding),
                Map.entry("sourceUrl", sourceUrl)
        );
    }
}
