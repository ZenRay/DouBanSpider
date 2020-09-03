-- 豆瓣电视剧相关数据，list_series 存储的是列表页信息



-- ----------------------------
-- Table structure for series_temp
-- 外源信息临时存储表，存储信息包括三个主要信息，影视条目信息、标题以及主要的类型标签
-- ----------------------------
DROP TABLE IF EXISTS `series_temp`;
CREATE TABLE `series_temp` (
  `series_id` varchar(20) NOT NULL COMMENT '豆瓣影视剧条目 ID',
  `title` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '豆瓣影视标题',
  `main_tag` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视主要类型标签 eg:电影、电视剧、综艺、动漫、纪录片以及短片',
  `crawled` boolean DEFAULT 0 COMMENT '该条目信息是否已经爬取，默认为 0 未爬取，1 为已爬取',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次爬取数据',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新爬取时间，没有更新的情况和首次爬取时间一致',
  PRIMARY KEY (`series_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='外源信息临时存储表';


-- ----------------------------
-- Table structure for list_series
-- 作为基本信息存储
-- ----------------------------
DROP TABLE IF EXISTS `list_series`;
CREATE TABLE `list_series` (
  `series_id` varchar(20) NOT NULL COMMENT '豆瓣影视剧条目 ID',
  `tag` varchar(10) COMMENT '豆瓣电视剧页面中的 tag，包括 热门,美剧,英剧,韩剧,日剧,国产剧,港剧,日本动画,综艺,纪录片',
  `name` varchar(150) COMMENT '标题',
  `rate` decimal(3, 1) DEFAULT NULL COMMENT '评分',
  `cover`  varchar(500) COMMENT '海报链接',
  `crawled` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已经爬取',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次爬取数据',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新爬取时间，没有更新的情况和首次爬取时间一致',
  PRIMARY KEY (`series_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='电视剧列表信息表';



-- ----------------------------
-- Table structure for series_info
-- ----------------------------
DROP TABLE IF EXISTS `series_info`;
CREATE TABLE `series_info` (
  -- `id` bigint NOT NULL AUTO_INCREMENT,
  `series_id` varchar(20) NOT NULL COMMENT '豆瓣影视剧条目 ID',
  `name` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '豆瓣影视名称',
  `alias` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视别名',
  `rate` decimal(2, 1) DEFAULT 0 COMMENT '豆瓣影视评分',
  `rate_collection` INT UNSIGNED DEFAULT 0 COMMENT '豆瓣影视评论人数',
  `main_tag` varchar(10) DEFAULT NULL COMMENT '豆瓣影视主要类型标签 eg:电影、电视剧、综艺、动漫、纪录片以及短片',
  `genres` varchar(200) DEFAULT NULL COMMENT '豆瓣影视类型，例如 恐怖、动作等',
  `product_country` varchar(100) DEFAULT NULL COMMENT '豆瓣影视制片国家',
  `language` varchar(100) DEFAULT NULL COMMENT '豆瓣影视语言',
  `release_year` YEAR DEFAULT NULL COMMENT '豆瓣影视成片年份',
  `release_date` varchar(100) DEFAULT NULL COMMENT '豆瓣影视上映日期，不同的国家可能日期不同',
  `play_duration` varchar(100) DEFAULT NULL COMMENT '豆瓣影视播放时长，可能不同回家版本存在不同时长',
  `imdb_id` varchar(20) DEFAULT NULL COMMENT 'IMDB 数据中的 ID',
  `tags` varchar(100) DEFAULT NULL COMMENT '豆瓣影视中豆瓣成员常用标签 实际可能为豆瓣处理得到的结果',
  `directors` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视条目中导演，使用 / 分隔',
  `screenwriters` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视条目中编剧，使用 / 分隔',
  `actors` varchar(400) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视条目中演员，使用 / 分隔',
  `plot` varchar(3000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视条目剧情简介',
  `cover` varchar(150) DEFAULT NULL COMMENT '豆瓣影视条目中封面海报链接',
  `cover_content` BLOB DEFAULT NULL COMMENT '豆瓣影视海报链接请求后的 content，避免后续无法请求的情况'
  `official_site` varchar(200) DEFAULT NULL COMMENT '影视条目上的官方网站',
  `recommendation_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '影视条目上的官方网站',
  `recommendation_item` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '提取豆瓣对当前内容推荐对相似条目',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次爬取数据',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新爬取时间，没有更新的情况和首次爬取时间一致',
  PRIMARY KEY (`series_id`)
  -- UNIQUE KEY `sid` (`series_id`) COMMENT '豆瓣影视实际 ID 作为唯一约束'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='影视列表信息表';


-- ----------------------------
-- Table structure for episode_info
-- ----------------------------
DROP TABLE IF EXISTS `episode_info`;
CREATE TABLE `episode_info` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `sid` varchar(20) NOT NULL COMMENT '豆瓣影视剧条目 ID',
  `episode` TINYINT(3) UNSIGNED NOT NULL COMMENT '多季剧集的集数',
  `title` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视剧集标题',
  `origin_title` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视剧集原始标题，主要是一类国外剧集的标题',
  `date` varchar(200) DEFAULT NULL COMMENT '豆瓣剧集上映日期',
  `plot` varchar(3000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视条目多季剧集剧情简介',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次爬取数据',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新爬取时间，没有更新的情况和首次爬取时间一致',
  PRIMARY KEY (`id`),
  -- 与 sereis_info 中 ID 一致，使用外键方式
  FOREIGN KEY (`sid`)
    REFERENCES series_info(`series_id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
  -- UNIQUE KEY `seid` (`series_id`, `episode`) COMMENT '豆瓣影视实际 ID 和剧集集数作为唯一约束'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='影视多季各集信息表';



-- ----------------------------
-- Table structure for worker
-- 存储影视演职人员信息
-- ----------------------------
DROP TABLE IF EXISTS `worker`;
CREATE TABLE `worker` (
  `wid` varchar(20) NOT NULL COMMENT '豆瓣影视演职人员 ID',
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '豆瓣影视演职人员姓名',
  `alias` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视演职人员姓名(非中文)', 
  `sid` varchar(20) NOT NULL COMMENT '豆瓣影视剧条目 ID',
  `duty` varchar(100) COMMENT '演职人员岗位',
  `action` varchar(5) DEFAULT NULL COMMENT '演员或其他配音演员，参与到影片中到方式',
  `role` varchar(100) DEFAULT NULL COMMENT '演员或其他配音演员，在影片中的角色',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次爬取数据',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新爬取时间，没有更新的情况和首次爬取时间一致',
  PRIMARY KEY (`wid`),
  FOREIGN KEY (`sid`)
    REFERENCES series_info(`series_id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='影视演职人员信息';


-- ----------------------------
-- Table structure for picture
-- 存储影视海报和壁纸信息
-- ----------------------------
DROP TABLE IF EXISTS `picture`;
CREATE TABLE `picture` (
  `pid` varchar(30) NOT NULL COMMENT '豆瓣影视海报和壁纸 ID',
  `url` varchar(150) NOT NULL COMMENT '豆瓣影视海报和壁纸的链接',
  `content` BLOB NOT NULL COMMENT '豆瓣影视海报和壁纸的链接请求后的 content，避免后续无法请求的情况',
  `description` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视海报和壁纸的描述信息', 
  `specification` varchar(30) DEFAULT NULL COMMENT '豆瓣影视剧海报和壁纸的规格',
  `type` varchar(10) DEFAULT NULL COMMENT '图片类型分类: 海报、壁纸和剧照',
  `sid` varchar(20) NOT NULL COMMENT '豆瓣影视剧条目 ID',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次爬取数据',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新爬取时间，没有更新的情况和首次爬取时间一致',
  PRIMARY KEY (`pid`),
  FOREIGN KEY (`sid`)
    REFERENCES series_info(`series_id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='影视海报和壁纸信息';



-- ----------------------------
-- Table structure for award
-- 存储影视获奖信息
-- ----------------------------
DROP TABLE IF EXISTS `award`;
CREATE TABLE `award` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `sid` varchar(20) NOT NULL COMMENT '豆瓣影视剧 ID'
  `host` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '颁奖主办方',
  `year` YEAR NOT NULL COMMENT '获奖年份',
  `name` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '获奖类型名称',
  `person` varchar(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '获奖人姓名',
  `status` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '最终获奖状态, 1 为获奖，0 表示只有提名'
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次爬取数据',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新爬取时间，没有更新的情况和首次爬取时间一致',
  PRIMARY KEY (`pid`),
  FOREIGN KEY (`sid`)
    REFERENCES series_info(`series_id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='影视获奖信息';





-- ----------------------------
-- Table structure for person
-- 存储影视人员的具体信息，和 worker 的差异在于，该表主要针对的是演职人员的 profile 信息
-- ----------------------------
DROP TABLE IF EXISTS `person`;
CREATE TABLE `person` (
  `id` varchar(20) NOT NULL COMMENT '豆瓣影视演职人员的 ID',
  `name` varchar(25) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '豆瓣影视演职人员姓名',
  `gender` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '演职人员性别, 1 为男性，0 为女性, 2 为未标注，默认为 2'
  `constellation` varchar(5) DEFAULT NULL COMMENT '影视演职人员星座',
  `birthdate` varchar(30) COMMENT '影视演职人员出生日期',
  `birthplace` varchar(60) DEFAULT NULL COMMENT '影视演职人员出生地',
  `profession` varchar(40) DEFAULT NULL COMMENT '演职人员的职业名称，可能使用 / 分隔',
  `alias` varchar(160) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视演职人员姓名(非中文)',  
  `alias_cn` varchar(240) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视演职人员姓名(中文)',  
  `family` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视演职人员家庭成员',   
  `imdb_link` varchar(30) DEFAULT NULL COMMENT 'IMDB 数据中的链接',
  `official_web` varchar(150) DEFAULT NULL COMMENT '影视推广的官方网站',
  `introduction` varcahr(300) DEFAULT NULL COMMENT '人物信息简介',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次爬取数据',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新爬取时间，没有更新的情况和首次爬取时间一致',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='影视海报和壁纸信息';
