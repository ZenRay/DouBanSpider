-- 豆瓣电视剧相关数据，list_series 存储的是列表页信息


-- ----------------------------
-- Table structure for list_series
-- ----------------------------
DROP TABLE IF EXISTS `list_series`;
CREATE TABLE `list_series` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tag` varchar(10) NOT NULL COMMENT '豆瓣电视剧页面中的 tag，包括 热门,美剧,英剧,韩剧,日剧,国产剧,港剧,日本动画,综艺,纪录片',
  `title` varchar(150) NOT NULL COMMENT '标题',
  `list_id` varchar(20) NOT NULL COMMENT '豆瓣电视剧页面保存的各条目 ID',
  `rate` decimal(3, 1) DEFAULT NULL COMMENT '评分',
  `url` varchar(500) NOT NULL COMMENT '电视剧详情页链接',
  `cover_link`  varchar(500) NOT NULL COMMENT '海报链接',
  PRIMARY KEY (`id`),
  UNIQUE KEY `sid` (`list_id`) COMMENT '电视剧实际 ID 作为唯一键'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='电视剧列表信息表';