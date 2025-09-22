-- MariaDB dump 10.19  Distrib 10.11.6-MariaDB, for debian-linux-gnu (aarch64)
--
-- Host: localhost    Database: box_db2
-- ------------------------------------------------------
-- Server version	10.11.6-MariaDB-0+deb12u1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `boxes`
--

LOCK TABLES `boxes` WRITE;
/*!40000 ALTER TABLE `boxes` DISABLE KEYS */;
INSERT INTO `boxes` VALUES
(1,'Basement','Interesting stuff this is really crazy long and unreasonable for a test that I don\'t like','2025-08-05','2025-08-05'),
(2,'Attic','','2025-08-05','2025-08-05'),
(3,'Storage room','','2025-08-17','2025-08-17'),
(5,'Unspecified','','2025-08-17','2025-08-17'),
(6,'Unspecified','','2025-08-17','2025-08-17');
/*!40000 ALTER TABLE `boxes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `categories` (
  `cat_num` int(11) NOT NULL AUTO_INCREMENT,
  `cat_name` varchar(36) NOT NULL,
  PRIMARY KEY (`cat_num`)
) ENGINE=InnoDB AUTO_INCREMENT=163 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES
(1,'Uncategorized'),
(154,'Household'),
(155,'Wall decor'),
(156,'Decorating'),
(159,'Office'),
(160,'Kitchen');
/*!40000 ALTER TABLE `categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `items`
--

DROP TABLE IF EXISTS `items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `items`
--

LOCK TABLES `items` WRITE;
/*!40000 ALTER TABLE `items` DISABLE KEYS */;
INSERT INTO `items` VALUES
(23542517,'Other Cat ',1,'white_cat1754676171.361323.jpg','2025-08-05','Decorating','This cat is not our cat, though it is a white Persian\r\n				'),
(23542518,'Kitty has a kitty-catty name that is long',1,'sleepy_cat1754586100.435703.jpg','2025-08-05','Decorating','It\'s hard to describe a cat this fluffy\r\n				\r\n				\r\n				\r\n				\r\n				'),
(23542522,'Odd cat',1,'cat1754402419.8150618.jpg','2025-08-05','Decorating','Upside down in a basket\r\n				\r\n				\r\n				'),
(23542534,'Cat \'o Cat',1,'cat_in_basket1754586020.012839.jpg','2025-08-05','Decorating',''),
(23542536,'Bed cat',1,'doll_bed_cat1754586156.0029042.jpg','2025-08-05','Decorating','This is Meringue'),
(23542538,'Meringue and shoes',1,'shoe_cat1754593839.013192.jpg','2025-08-07','Decorating','One of these things is not like the other.'),
(23542539,'Sleepy cat',1,'IMG_34911754678187.944106.jpeg','2025-08-07','Decorating','Cat asleep in a basket upside down'),
(23542545,'Grouchy Cat',1,'IMG_47191754801655.8378577.jpeg','2025-08-10','Decorating','This cat is grouchy. It is 11:00 at night and she tried to lick a cracker. That made her angry because it was salty.'),
(23542546,'Cat w/ ears',1,'IMG_05391754801746.7012002.jpeg','2025-08-10','Decorating',''),
(23542547,'Loaf Cat by box',1,'IMG_42021754801751.2102.jpeg','2025-08-10','Decorating',''),
(23542548,'Box cat',1,'IMG_29521754801792.6730905.jpeg','2025-08-10','Decorating',''),
(23542549,'Kitty Who Saw a Bug',1,'IMG_41991754801851.4096892.jpeg','2025-08-10','Decorating','This kitty has seen a bug (probably a moth)'),
(23542550,'Floof ',1,'IMG_27241754801865.4031425.jpeg','2025-08-10','Decorating',''),
(23542551,'Long cat',1,'IMG_26131754801919.0087068.jpeg','2025-08-10','Decorating',''),
(23542552,'Silly cat',1,'IMG_25741754801953.527697.jpeg','2025-08-10','Decorating',''),
(23542553,'Big Loaf Cat',1,'IMG_41971754802000.1013217.jpeg','2025-08-10','Decorating','This cat is looking up'),
(23542554,'Baby goof',1,'IMG_23081754802011.5942495.jpeg','2025-08-10','Decorating',''),
(23542555,'Small cat 3',1,'IMG_22141754802055.3617797.jpeg','2025-08-10','Decorating',''),
(23542556,'Cat in a car',1,'IMG_34101754802385.2807262.jpeg','2025-08-10','Decorating','This cat in that car'),
(23542557,'Not Meringue',1,'white_cat1754676171.361323.jpg','2025-08-05','Decorating','This cat is not our cat, though it is a white Persian\r\n				'),
(23542560,'Meringue',1,'doll_bed_cat1754586156.0029042.jpg','2025-08-05','Decorating','This is Meringue'),
(23542561,'Meringue and shoes',1,'shoe_cat1754593839.013192.jpg','2025-08-07','Decorating','One of these things is not like the other.'),
(23542562,'Merry Cat',1,'IMG_31971754855747.2535975.jpeg','2025-08-10','Household',''),
(23542563,'Box cat 2',1,'IMG_29521754801792.6730905.jpeg','2025-08-10','Decorating','Cat in a box '),
(23542564,'Long cat',1,'IMG_26131754801919.0087068.jpeg','2025-08-10','Decorating',''),
(23542565,'Other Loaf Cat',1,'IMG_41971754802000.1013217.jpeg','2025-08-10','Decorating','This cat is looking up'),
(23542566,'Small cat',1,'IMG_22141754802055.3617797.jpeg','2025-08-10','Decorating',''),
(23542567,'Cat on car part ii ',1,'IMG_31171754855649.2286828.jpeg','2025-08-05','Decorating','				'),
(23542568,'Meringue and shoes 2',1,'shoe_cat1754593839.013192.jpg','2025-08-07','Decorating','One of these things is not like the other.'),
(23542569,'I can fit',1,'IMG_27221754855589.803494.jpeg','2025-08-10','Household','At least my head'),
(23542570,'Friendly cat',1,'IMG_31491754855512.109483.jpeg','2025-08-10','Decorating','When it’s cold'),
(23542571,'Window cat',1,'IMG_27151754855429.2310407.jpeg','2025-08-10','Decorating',''),
(23542572,'Meringue the great',2,'IMG_32191754855374.6257684.jpeg','2025-08-05','Decorating','This is Meringue'),
(23542573,'Blue cat',1,'grump1754929683.474008.jpg','2025-08-11','Decorating',''),
(23542574,'Poster cat',1,'loaf1754929705.2171688.jpg','2025-08-11','Decorating',''),
(23542575,'KITTEN',1,'kitten1754929840.9603348.jpeg','2025-08-11','Decorating',''),
(23542576,'Computer cat',1,'IMG_32361754930033.939078.jpeg','2025-08-11','Decorating',''),
(23542578,'Skeptical cat',1,'IMG_31101754930196.7702649.jpeg','2025-08-11','Decorating',''),
(23542579,'Mat cat',1,'IMG_27671754930134.3660243.jpeg','2025-08-16','Decorating','Cat who sat on a mat'),
(23542604,'test',1,'none.jpg','2025-08-17','Uncategorized',''),
(23542605,'test3',3,'none.jpg','2025-08-17','Uncategorized',''),
(23542606,'Orphan test',NULL,'none.jpg','2025-08-17','Uncategorized',''),
(23542607,'test',3,'none.jpg','2025-08-17','Uncategorized','');
/*!40000 ALTER TABLE `items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `locations`
--

DROP TABLE IF EXISTS `locations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `locations` (
  `loc_name` varchar(255) NOT NULL,
  `loc_num` int(11) NOT NULL AUTO_INCREMENT,
  UNIQUE KEY `loc_num` (`loc_num`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `locations`
--

LOCK TABLES `locations` WRITE;
/*!40000 ALTER TABLE `locations` DISABLE KEYS */;
INSERT INTO `locations` VALUES
('Unspecified',0),
('Storage room',1),
('Garage',2),
('Sun room',3),
('Basement',6),
('Attic',9);
/*!40000 ALTER TABLE `locations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `settings`
--

DROP TABLE IF EXISTS `settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `settings` (
  `set_num` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `value` varchar(255) NOT NULL,
  UNIQUE KEY `set_num_2` (`set_num`),
  KEY `set_num` (`set_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `settings`
--

LOCK TABLES `settings` WRITE;
/*!40000 ALTER TABLE `settings` DISABLE KEYS */;
INSERT INTO `settings` VALUES
(1,'backup_filename','static/backup/box_db2-1755460850.564475.sql'),
(2,'last_backup','2025-08-17'),
(3,'archive_filename','static/backup/imps_imagearchive.2025-08-17.zip'),
(4,'last_archive','2025-08-17');
/*!40000 ALTER TABLE `settings` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-08-17 21:05:06
