/*
 Navicat Premium Data Transfer

 Source Server         : 127.0.0.1
 Source Server Type    : MySQL
 Source Server Version : 80019
 Source Host           : localhost:3306
 Source Schema         : hn_vedio

 Target Server Type    : MySQL
 Target Server Version : 80019
 File Encoding         : 65001

 Date: 11/03/2020 19:26:27
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for video
-- ----------------------------
DROP TABLE IF EXISTS `video`;
CREATE TABLE `video` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL COMMENT '电影名',
  `name_jane` varchar(100) DEFAULT NULL COMMENT '电影名拼音首字母',
  `score` double DEFAULT NULL COMMENT '评分',
  `content_abstract` text COMMENT '内容简介',
  `alias_name` varchar(255) DEFAULT NULL COMMENT '别名',
  `image_path` varchar(255) DEFAULT NULL COMMENT '电影图片地址',
  `language` varchar(50) DEFAULT NULL COMMENT '语言',
  `upcoming_time` datetime DEFAULT NULL COMMENT '即将上映时间',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP(0) COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='电影基本信息表';

-- ----------------------------
-- Table structure for video_actor
-- ----------------------------
DROP TABLE IF EXISTS `video_actor`;
CREATE TABLE `video_actor` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `video_id` bigint DEFAULT NULL COMMENT '电影基本信息外键id',
  `name` varchar(255) DEFAULT NULL COMMENT '演员名字',
  `name_jane` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '演员名字简称拼音首字母',
  PRIMARY KEY (`id`),
  KEY `foreign_video_actor_id` (`video_id`),
  CONSTRAINT `foreign_video_actor_id` FOREIGN KEY (`video_id`) REFERENCES `video` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='演员基本信息表';

-- ----------------------------
-- Table structure for video_character
-- ----------------------------
DROP TABLE IF EXISTS `video_character`;
CREATE TABLE `video_character` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `video_id` bigint DEFAULT NULL COMMENT '电影基本信息外键id',
  `sorting` int DEFAULT NULL COMMENT '排序',
  `name` varchar(255) DEFAULT NULL COMMENT '演员名',
  `role` varchar(100) DEFAULT NULL COMMENT '角色',
  `image_path` varchar(255) DEFAULT NULL COMMENT '图片存放位置',
  PRIMARY KEY (`id`),
  KEY `video_id` (`video_id`),
  CONSTRAINT `video_character_ibfk_1` FOREIGN KEY (`video_id`) REFERENCES `video` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='影视数据检索库';

-- ----------------------------
-- Table structure for video_director
-- ----------------------------
DROP TABLE IF EXISTS `video_director`;
CREATE TABLE `video_director` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `video_id` bigint DEFAULT NULL COMMENT '电影基本信息外键id',
  `name` varchar(255) DEFAULT NULL COMMENT '导演名字',
  `name_jane` varchar(100) DEFAULT NULL COMMENT '导演名字简称拼音首字母',
  PRIMARY KEY (`id`),
  KEY `video_id` (`video_id`),
  CONSTRAINT `video_director_ibfk_1` FOREIGN KEY (`video_id`) REFERENCES `video` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='导演基本信息表';

-- ----------------------------
-- Table structure for video_extension_region
-- ----------------------------
DROP TABLE IF EXISTS `video_extension_region`;
CREATE TABLE `video_extension_region` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `video_id` bigint NOT NULL COMMENT '电影基本信息外键id',
  `region` varchar(50) DEFAULT NULL COMMENT '地区',
  `year` int DEFAULT NULL COMMENT '年份',
  `release_time` varchar(20) DEFAULT NULL COMMENT '上映时间',
  `running_time` varchar(20) DEFAULT NULL COMMENT '时长',
  `coming_soon` tinyint(1) DEFAULT NULL COMMENT '是否即将上映（拉取即将上映的数据必存）1代表TRUE\r\n0代表FALSE\r\n',
  PRIMARY KEY (`id`),
  KEY `foreign_video_extension_region_id` (`video_id`),
  CONSTRAINT `foreign_video_extension_region_id` FOREIGN KEY (`video_id`) REFERENCES `video` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='地区扩展基本信息表';

-- ----------------------------
-- Table structure for video_review
-- ----------------------------
DROP TABLE IF EXISTS `video_review`;
CREATE TABLE `video_review` (
  `id` int NOT NULL AUTO_INCREMENT,
  `video_id` bigint DEFAULT NULL COMMENT '电影基本信息外键id',
  `sorting` int DEFAULT NULL COMMENT '排序（楼数）',
  `review_time` varchar(20) DEFAULT NULL COMMENT '点评时间(YYYY-MM-dd HH:mm:ss)',
  `score` double DEFAULT NULL COMMENT '评分',
  `content` text COMMENT '评论内容',
  PRIMARY KEY (`id`),
  KEY `video_id` (`video_id`),
  CONSTRAINT `video_review_ibfk_1` FOREIGN KEY (`video_id`) REFERENCES `video` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='电影点评信息表(vedio_review)';

-- ----------------------------
-- Table structure for video_type
-- ----------------------------
DROP TABLE IF EXISTS `video_type`;
CREATE TABLE `video_type` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `video_id` bigint DEFAULT NULL COMMENT '电影基本信息外键id',
  `name` varchar(255) NOT NULL COMMENT '类型名称',
  PRIMARY KEY (`id`),
  KEY `video_id` (`video_id`),
  CONSTRAINT `video_type_ibfk_1` FOREIGN KEY (`video_id`) REFERENCES `video` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='电影点评信息表(vedio_review)\n';

SET FOREIGN_KEY_CHECKS = 1;
