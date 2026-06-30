package com.example.housepredict.service.impl;

import com.example.housepredict.entity.City;
import com.example.housepredict.entity.CrawlTask;
import com.example.housepredict.entity.District;
import com.example.housepredict.entity.House;
import com.example.housepredict.mapper.CityMapper;
import com.example.housepredict.mapper.CrawlTaskMapper;
import com.example.housepredict.mapper.DistrictMapper;
import com.example.housepredict.mapper.HouseMapper;
import com.example.housepredict.service.DemoDataService;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class DemoDataServiceImpl implements DemoDataService {
    private final CityMapper cityMapper;
    private final DistrictMapper districtMapper;
    private final HouseMapper houseMapper;
    private final CrawlTaskMapper crawlTaskMapper;

    public DemoDataServiceImpl(CityMapper cityMapper, DistrictMapper districtMapper, HouseMapper houseMapper, CrawlTaskMapper crawlTaskMapper) {
        this.cityMapper = cityMapper;
        this.districtMapper = districtMapper;
        this.houseMapper = houseMapper;
        this.crawlTaskMapper = crawlTaskMapper;
    }

    @Override
    @Transactional
    public int seedDemoData() {
        int created = 0;
        for (Map<String, String> row : rows()) {
            if (houseMapper.selectBySourceUrl(row.get("sourceUrl")) != null) {
                continue;
            }
            City city = findOrCreateCity(row.get("city"));
            District district = findOrCreateDistrict(city, row.get("district"));
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
            houseMapper.insert(house);
            created++;
        }
        return created;
    }

    @Override
    @Transactional
    public CrawlTask runDemoCrawler(String city, String district, int pages) {
        CrawlTask task = new CrawlTask();
        task.setTaskName("示例采集-" + city);
        task.setTargetCity(city);
        task.setTargetDistrict(district == null ? "" : district);
        task.setPageCount(Math.max(pages, 1));
        task.setStatus("running");
        task.setStartedAt(LocalDateTime.now());
        crawlTaskMapper.insert(task);
        int created = seedDemoData();
        task.setStatus("success");
        task.setSuccessCount(rows().size());
        task.setFailCount(0);
        task.setFinishedAt(LocalDateTime.now());
        task.setMessage("Processed bundled demo houses; imported " + created + " new houses.");
        crawlTaskMapper.updateById(task);
        return task;
    }

    private City findOrCreateCity(String name) {
        City city = cityMapper.selectByName(name);
        if (city != null) {
            return city;
        }
        City created = new City();
        created.setName(name);
        created.setProvince("山东省");
        cityMapper.insert(created);
        return created;
    }

    private District findOrCreateDistrict(City city, String name) {
        District district = districtMapper.selectByCityIdAndName(city.getId(), name);
        if (district != null) {
            district.setCity(city);
            return district;
        }
        District created = new District();
        created.setCity(city);
        created.setName(name);
        districtMapper.insert(created);
        return created;
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
