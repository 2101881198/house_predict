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
                Map.of("city", "济南", "district", "历下区", "title", "历下区精装三室", "community", "泉城花园", "totalPrice", "215", "area", "96", "roomType", "三室一厅", "floor", "中楼层", "direction", "南", "decoration", "精装", "buildYear", "2015", "address", "济南市历下区", "longitude", "117.120128", "latitude", "36.652069", "surrounding", "近地铁，近学校", "sourceUrl", "demo://jinan-lixia-1"),
                Map.of("city", "济南", "district", "市中区", "title", "市中区改善两室", "community", "鲁能小区", "totalPrice", "168", "area", "82", "roomType", "两室一厅", "floor", "高楼层", "direction", "南北", "decoration", "简装", "buildYear", "2010", "address", "济南市市中区", "longitude", "116.997472", "latitude", "36.651121", "surrounding", "生活便利", "sourceUrl", "demo://jinan-shizhong-1"),
                Map.of("city", "青岛", "district", "市南区", "title", "市南区海景房", "community", "海岸名都", "totalPrice", "390", "area", "118", "roomType", "三室两厅", "floor", "中楼层", "direction", "南", "decoration", "精装", "buildYear", "2018", "address", "青岛市市南区", "longitude", "120.384428", "latitude", "36.105215", "surrounding", "近海，商圈成熟", "sourceUrl", "demo://qingdao-shinan-1"),
                Map.of("city", "烟台", "district", "芝罘区", "title", "芝罘区刚需两室", "community", "幸福里", "totalPrice", "105", "area", "76", "roomType", "两室一厅", "floor", "低楼层", "direction", "东南", "decoration", "简装", "buildYear", "2008", "address", "烟台市芝罘区", "longitude", "121.383188", "latitude", "37.539297", "surrounding", "近市场", "sourceUrl", "demo://yantai-zhifu-1")
        );
    }
}
