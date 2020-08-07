-- 豆瓣电视剧相关数据，list_series 存储的是列表页信息


-- ----------------------------
-- Table structure for list_series
-- ----------------------------
DROP TABLE IF EXISTS `list_series`;
CREATE TABLE `list_series` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tag` varchar(10) COMMENT '豆瓣电视剧页面中的 tag，包括 热门,美剧,英剧,韩剧,日剧,国产剧,港剧,日本动画,综艺,纪录片',
  `title` varchar(150) COMMENT '标题',
  `series_id` varchar(20) NOT NULL COMMENT '豆瓣电视剧页面保存的各条目 ID',
  `rate` decimal(3, 1) DEFAULT NULL COMMENT '评分',
  `url` varchar(500) NOT NULL COMMENT '电视剧详情页链接',
  `cover_link`  varchar(500) COMMENT '海报链接',
  `crawled` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已经爬取',
  PRIMARY KEY (`id`),
  UNIQUE KEY `sid` (`series_id`) COMMENT '电视剧实际 ID 作为唯一约束'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='电视剧列表信息表';



-- ----------------------------
-- Table structure for series_info
-- ----------------------------
DROP TABLE IF EXISTS `series_info`;
CREATE TABLE `series_info` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `series_id` varchar(20) NOT NULL COMMENT '豆瓣影视剧条目 ID',
  `name` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '豆瓣影视名称',
  `alias` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视别名',
  `rate` decimal(2, 1) DEFAULT 0 COMMENT '豆瓣影视评分',
  `rate_collection` INT UNSIGNED DEFAULT 0 COMMENT '豆瓣影视评论人数',
  `main_tag` varchar(10) DEFAULT NULL COMMENT '豆瓣影视主要类型标签 eg:电影、电视剧、综艺、动漫、纪录片以及短片',
  `category` varchar(200) DEFAULT NULL COMMENT '豆瓣影视类型，例如 恐怖、动作等',
  `product_country` varchar(100) DEFAULT NULL COMMENT '豆瓣影视制片国家',
  `language` varchar(100) DEFAULT NULL COMMENT '豆瓣影视语言',
  `release_year` YEAR DEFAULT NULL COMMENT '豆瓣影视成片年份',
  `release_date` varchar(100) DEFAULT NULL COMMENT '豆瓣影视上映日期，不同的国家可能日期不同',
  `play_duration` varchar(100) DEFAULT NULL COMMENT '豆瓣影视播放时长，可能不同回家版本存在不同时长',
  `imdb_id` varchar(20) DEFAULT NULL COMMENT 'IMDB 数据中的 ID',
  `tags` varchar(100) DEFAULT NULL COMMENT '豆瓣影视中豆瓣成员常用标签 实际可能为豆瓣处理得到的结果',
  `directors` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视条目中导演，使用 / 分隔',
  `screenwriter` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视条目中编剧，使用 / 分隔',
  `actors` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视条目中演员，使用 / 分隔',
  `plot` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视条目剧情简介',
  `cover` varchar(150) DEFAULT NULL COMMENT '豆瓣影视条目中封面海报链接',
  PRIMARY KEY (`id`),
  UNIQUE KEY `sid` (`series_id`) COMMENT '豆瓣影视实际 ID 作为唯一约束'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='影视列表信息表';


-- ----------------------------
-- Table structure for series_episode
-- ----------------------------
DROP TABLE IF EXISTS `series_episode`;
CREATE TABLE `series_episode` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `series_id` varchar(20) NOT NULL COMMENT '豆瓣影视剧条目 ID',
  `episode` TINYINT(3) UNSIGNED NOT NULL COMMENT '多季剧集的集数',
  `title` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '豆瓣影视剧集标题',
  `origin_title` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '豆瓣影视剧集原始标题，主要是一类国外剧集的标题',
  `date` varchar(100) DEFAULT NULL COMMENT '豆瓣剧集上映日期',
  `plot` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '豆瓣影视条目多季剧集剧情简介',
  PRIMARY KEY (`id`),
  UNIQUE KEY `seid` (`series_id`, `episode`) COMMENT '豆瓣影视实际 ID 和剧集集数作为唯一约束'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='影视多季各集信息表';