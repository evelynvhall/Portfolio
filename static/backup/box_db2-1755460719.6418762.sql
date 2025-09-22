-- MariaDB dump 10.19  Distrib 10.11.6-MariaDB, for debian-linux-gnu (aarch64)
--

--
-- Table structure for table `boxes`
--

DROP TABLE IF EXISTS `boxes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `boxes` (
  `box_num` int(11) DEFAULT NULL,
  `box_loc` varchar(30) DEFAULT NULL,
  `box_name` varchar(255) NOT NULL,
  `box_date` date NOT NULL,
  `box_last_changed` date NOT NULL,
  UNIQUE KEY `box_num_2` (`box_num`),
  KEY `box_num` (`box_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `boxes`
--

LOCK TABLES `boxes` WRITE;

INSERT INTO `boxes` VALUES
(1,'Sample location','Sample name','2025-08-05','2025-08-05'),

UNLOCK TABLES;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;

CREATE TABLE `categories` (
  `cat_num` int(11) NOT NULL AUTO_INCREMENT,
  `cat_name` varchar(36) NOT NULL,
  PRIMARY KEY (`cat_num`)
) ENGINE=InnoDB AUTO_INCREMENT=163 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;

INSERT INTO `categories` VALUES
(1,'Uncategorized'),
(2,'Sample cat'),

UNLOCK TABLES;

--
-- Table structure for table `items`
--

DROP TABLE IF EXISTS `items`;
CREATE TABLE `items` (
  `item_num` int(11) NOT NULL AUTO_INCREMENT,
  `item_name` varchar(256) NOT NULL,
  `box_num` int(11) DEFAULT NULL,
  `item_pic` varchar(255) DEFAULT 'none.jpg',
  `item_date` date NOT NULL,
  `item_cat` varchar(64) NOT NULL DEFAULT 'uncategorized',
  `item_desc` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`item_num`),
  KEY `item_num` (`item_num`),
  FULLTEXT KEY `item_desc` (`item_desc`)
) ENGINE=InnoDB AUTO_INCREMENT=23542608 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `items`
--

LOCK TABLES `items` WRITE;
INSERT INTO `items` VALUES
(1,'Sample item',1,'sample_image.jpg','2025-08-05','Sample cat','Sample item description'),
UNLOCK TABLES;

--
-- Table structure for table `locations`
--

DROP TABLE IF EXISTS `locations`;

CREATE TABLE `locations` (
  `loc_name` varchar(255) NOT NULL,
  `loc_num` int(11) NOT NULL AUTO_INCREMENT,
  UNIQUE KEY `loc_num` (`loc_num`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `locations`
--

LOCK TABLES `locations` WRITE;
INSERT INTO `locations` VALUES
('Unspecified',0),
('Sample loc',1),
UNLOCK TABLES;

--
-- Table structure for table `settings`
--

DROP TABLE IF EXISTS `settings`;
CREATE TABLE `settings` (
  `set_num` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `value` varchar(255) NOT NULL,
  UNIQUE KEY `set_num_2` (`set_num`),
  KEY `set_num` (`set_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `settings`
--

LOCK TABLES `settings` WRITE;
INSERT INTO `settings` VALUES
(1,'backup_filename','static/backup/setup.sql'),
(2,'last_backup','2025-09-25'),
(3,'archive_filename','static/backup/imps_imagearchive.zip'),
(4,'last_archive','2025-09-25');
UNLOCK TABLES;
