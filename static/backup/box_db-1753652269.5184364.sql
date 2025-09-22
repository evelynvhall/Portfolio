-- MariaDB dump 10.19  Distrib 10.11.6-MariaDB, for debian-linux-gnu (aarch64)
--
-- Host: localhost    Database: box_db
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
  `box_cat` varchar(30) DEFAULT NULL,
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
(1,'Decorating','','2025-07-24','2025-07-24'),
(2,'Wall Decor','','2025-07-24','2025-07-24'),
(3,'Uncategorized','','2025-07-25','2025-07-25');
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
  PRIMARY KEY (`cat_num`),
  KEY `cat_num` (`cat_num`)
) ENGINE=InnoDB AUTO_INCREMENT=161 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES
(0,'Uncategorized'),
(154,'Household'),
(155,'Office'),
(156,'Decorating'),
(159,'Wall Decor'),
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
) ENGINE=InnoDB AUTO_INCREMENT=23542514 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `items`
--

LOCK TABLES `items` WRITE;
/*!40000 ALTER TABLE `items` DISABLE KEYS */;
INSERT INTO `items` VALUES
(23542495,'Snail',1,'IMG_22601753393961.3702104.jpeg','2025-07-24','Decorating','Brown/Metal/Textured/Heavy'),
(23542496,'Owl',1,'IMG_22611753394194.336892.jpeg','2025-07-24','Decorating','Resin/Charcoal Gray/Tall/Smith & Hawken'),
(23542500,'8x10 Empty Clip Frame',2,'IMG_46681753395665.9701016.jpeg','2025-07-24','Wall Decor','Landscape or Portrait Frame'),
(23542501,'8x10 Tree Sketch in Black Frame',2,'image1753395949.0935495.jpg','2025-07-24','Wall Decor','Michelle Dujardin/Portrait Frame/Botanical Art'),
(23542502,'11x14 Set of Two Botanical Prints in Clip Frames',2,'IMG_46691753396298.3462243.jpeg','2025-07-24','Wall Decor','Blue/Eucalyptus/Prints from Digital File/Landscape or Portrait Frame/Botanical Art'),
(23542503,'8x10 Set of Five Owl Prints in Wood Frames',2,'IMG_46701753397201.030576.jpeg','2025-07-24','Wall Decor','With Mat/Hand Colored/West Elm/Wall or Tabletop/Landscape or Portrait Frame'),
(23542504,'8x10 Set of Five Tree Sketches in Clip Frames',2,'IMG_46711753398546.7061813.jpeg','2025-07-24','Wall Decor','Michelle Dujardin/Live Oak/California Pepper/Eucalyptus/Landscape or Portrait Frame/Botanical Art'),
(23542505,'8x10 Set of Three Victorian Bathroom Prints in Clip Frames',2,'image1753399086.805977.jpg','2025-07-25','Wall Decor','Landscape or Portrait Frame/Photographic Art'),
(23542506,'Lacquer Tray with Handles',3,'image1753476102.1781511.jpg','2025-07-25','Decorating','White with Silver/Bird Silhouette/Botanical/Lacquer/Square'),
(23542507,'Large Decorative Bowl',3,'IMG_46721753477082.2774763.jpeg','2025-07-25','Decorating','Multicolor/Yellow/Teal/Green/Red/White/Floral/Botanical/Pier One/Coordinating Pitcher'),
(23542509,'4.5 Quart Mixing Bowl with Lid ',3,'image1753477795.458188.jpg','2025-07-25','Kitchen','Pyrex/Clear'),
(23542510,'Set of Two Fluted Serving Bowls',3,'image1753478006.6755762.jpg','2025-07-25','Kitchen','Pier One/Nesting/White'),
(23542511,'Large Glass Plate with Beaded Edge',3,'IMG_46741753478575.6694102.jpeg','2025-07-25','Kitchen','Clear'),
(23542512,'Large Decorative Glass Bowl',3,'IMG_46751753478716.8615396.jpeg','2025-07-25','Decorating','Clear/Spiral'),
(23542513,'Bread Basket with Warming Stone',3,'image1753479191.8827608.jpg','2025-07-25','Kitchen','Rectangular/Cotton Cloth Liner/\"Collin Bread Basket\" from Pier One');
/*!40000 ALTER TABLE `items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `locations`
--

DROP TABLE IF EXISTS `locations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `locations` (
  `location` varchar(255) NOT NULL,
  `loc_num` int(255) NOT NULL,
  UNIQUE KEY `loc_num` (`loc_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
('Sun Room',3);
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
(1,'backup_filename','static/backup/box_db-1753457015.6325097.sql'),
(2,'last_backup','2025-07-25'),
(3,'archive_filename','static/backup/imps_imagearchive.2025-07-25.zip'),
(4,'last_archive','2025-07-25');
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

-- Dump completed on 2025-07-27 22:37:49
