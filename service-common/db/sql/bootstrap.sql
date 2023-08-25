-- -------------------------------------------------------------
-- TablePlus 4.0.0(370)
--
-- https://tableplus.com/
--
-- Database: bugzero
-- Generation Time: 2021-07-06 15:58:56.8490
-- -------------------------------------------------------------


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


DROP TABLE IF EXISTS `bugs`;
CREATE TABLE `bugs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bugId` varchar(255) NOT NULL,
  `bugUrl` varchar(1000) NOT NULL,
  `description` text NOT NULL,
  `priority` varchar(255) NOT NULL,
  `snCiFilter` varchar(1000) NOT NULL,
  `snCiTable` varchar(255) NOT NULL,
  `summary` varchar(500) NOT NULL,
  `status` varchar(255) DEFAULT NULL,
  `knownAffectedReleases` varchar(1000) DEFAULT NULL,
  `knownFixedReleases` varchar(1000) DEFAULT NULL,
  `knownAffectedHardware` varchar(1000) DEFAULT NULL,
  `knownAffectedOs` varchar(1000) DEFAULT NULL,
  `vendorData` json DEFAULT NULL,
  `versions` json DEFAULT NULL,
  `vendorCreatedDate` datetime DEFAULT NULL,
  `vendorLastUpdatedDate` datetime DEFAULT NULL,
  `processed` tinyint(1) DEFAULT '0',
  `createdAt` datetime NOT NULL,
  `updatedAt` datetime NOT NULL,
  `managedProductId` int DEFAULT NULL,
  `vendorId` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `managedProductId` (`managedProductId`),
  KEY `vendorId` (`vendorId`),
  CONSTRAINT `bugs_ibfk_1` FOREIGN KEY (`managedProductId`) REFERENCES `managedProducts` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `bugs_ibfk_2` FOREIGN KEY (`vendorId`) REFERENCES `vendors` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `managedProducts`;
CREATE TABLE `managedProducts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `snProductId` varchar(255) DEFAULT NULL,
  `vendorPriorities` json NOT NULL,
  `vendorStatuses` json NOT NULL,
  `lastExecution` datetime DEFAULT NULL,
  `vendorData` json DEFAULT NULL,
  `isDisabled` tinyint(1) DEFAULT '0',
  `createdAt` datetime NOT NULL,
  `updatedAt` datetime NOT NULL,
  `vendorId` varchar(255) DEFAULT NULL,
  `vendorProductFamilyId` int DEFAULT NULL,
  `vendorProductId` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `vendorId` (`vendorId`),
  KEY `vendorProductFamilyId` (`vendorProductFamilyId`),
  KEY `vendorProductId` (`vendorProductId`),
  CONSTRAINT `managedproducts_ibfk_1` FOREIGN KEY (`vendorId`) REFERENCES `vendors` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `managedproducts_ibfk_2` FOREIGN KEY (`vendorProductFamilyId`) REFERENCES `vendorProductFamilies` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `managedproducts_ibfk_3` FOREIGN KEY (`vendorProductId`) REFERENCES `vendorProducts` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `managedProductVersions`;
CREATE TABLE `managedProductVersions` (
  `createdAt` datetime NOT NULL,
  `updatedAt` datetime NOT NULL,
  `managedProductId` int NOT NULL,
  `vendorProductVersionId` int NOT NULL,
  PRIMARY KEY (`managedProductId`,`vendorProductVersionId`),
  KEY `vendorProductVersionId` (`vendorProductVersionId`),
  CONSTRAINT `managedproductversions_ibfk_1` FOREIGN KEY (`managedProductId`) REFERENCES `managedProducts` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `managedproductversions_ibfk_2` FOREIGN KEY (`vendorProductVersionId`) REFERENCES `vendorProductVersions` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `msftBugs`;
CREATE TABLE `msftBugs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `kbUrl` varchar(1000) NOT NULL,
  `vendorCreatedDate` datetime DEFAULT NULL,
  `vendorLastUpdatedDate` datetime DEFAULT NULL,
  `guid` varchar(255) DEFAULT NULL,
  `kbId` varchar(255) DEFAULT NULL,
  `knownAffectedReleases` json DEFAULT NULL,
  `rssFeedId` varchar(255) DEFAULT NULL,
  `rssFeedName` varchar(255) DEFAULT NULL,
  `apiUrl` varchar(255) DEFAULT NULL,
  `eolProject` varchar(255) DEFAULT NULL,
  `heading` varchar(255) DEFAULT NULL,
  `title` varchar(255) DEFAULT NULL,
  `description` text,
  `processed` tinyint(1) DEFAULT '0',
  `processError` tinyint(1) DEFAULT '0',
  `processErrorMsg` varchar(500) DEFAULT '',
  `snCiFilter` varchar(1000) NOT NULL,
  `snCiTable` varchar(255) NOT NULL,
  `summary` varchar(300) NOT NULL,
  `status` varchar(255) DEFAULT NULL,
  `createdAt` datetime NOT NULL,
  `updatedAt` datetime NOT NULL,
  `managedProductId` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `managedProductId` (`managedProductId`),
  CONSTRAINT `msftbugs_ibfk_1` FOREIGN KEY (`managedProductId`) REFERENCES `managedProducts` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `settings`;
CREATE TABLE `settings` (
  `id` varchar(255) NOT NULL,
  `type` varchar(255) NOT NULL,
  `value` json NOT NULL,
  `createdAt` datetime NOT NULL,
  `updatedAt` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `vendorProductFamilies`;
CREATE TABLE `vendorProductFamilies` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `productFamilyId` varchar(255) NOT NULL,
  `vendorData` json DEFAULT NULL,
  `active` tinyint(1) DEFAULT '1',
  `createdAt` datetime NOT NULL,
  `updatedAt` datetime NOT NULL,
  `vendorId` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `vendorId` (`vendorId`),
  CONSTRAINT `vendorproductfamilies_ibfk_1` FOREIGN KEY (`vendorId`) REFERENCES `vendors` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `vendorProducts`;
CREATE TABLE `vendorProducts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `productUrl` varchar(1000) DEFAULT NULL,
  `productId` varchar(255) NOT NULL,
  `vendorData` json DEFAULT NULL,
  `active` tinyint(1) DEFAULT '1',
  `createdAt` datetime NOT NULL,
  `updatedAt` datetime NOT NULL,
  `vendorProductFamilyId` int DEFAULT NULL,
  `vendorId` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `vendorProductFamilyId` (`vendorProductFamilyId`),
  KEY `vendorId` (`vendorId`),
  CONSTRAINT `vendorproducts_ibfk_1` FOREIGN KEY (`vendorProductFamilyId`) REFERENCES `vendorProductFamilies` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `vendorproducts_ibfk_2` FOREIGN KEY (`vendorId`) REFERENCES `vendors` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `vendorProductVersions`;
CREATE TABLE `vendorProductVersions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `productUrl` varchar(1000) DEFAULT NULL,
  `snCiFilter` varchar(1000) DEFAULT NULL,
  `snCiTable` varchar(255) DEFAULT NULL,
  `productVersionId` varchar(255) NOT NULL,
  `vendorData` json DEFAULT NULL,
  `active` tinyint(1) DEFAULT '1',
  `createdAt` datetime NOT NULL,
  `updatedAt` datetime NOT NULL,
  `vendorProductId` int DEFAULT NULL,
  `vendorId` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `vendorProductId` (`vendorProductId`),
  KEY `vendorId` (`vendorId`),
  CONSTRAINT `vendorproductversions_ibfk_1` FOREIGN KEY (`vendorProductId`) REFERENCES `vendorProducts` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `vendorproductversions_ibfk_2` FOREIGN KEY (`vendorId`) REFERENCES `vendors` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `vendors`;
CREATE TABLE `vendors` (
  `id` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `vendorData` json DEFAULT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '1',
  `createdAt` datetime NOT NULL,
  `updatedAt` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO `vendors` (`id`, `name`, `vendorData`, `active`, `createdAt`, `updatedAt`) VALUES
('cisco', 'cisco', NULL, 1, '2021-06-27 14:31:46', '2021-06-27 14:31:46'),
('hpe', 'hpe', NULL, 1, '2021-06-29 10:20:00', '2021-06-29 10:20:00'),
('msft', 'Microsoft', NULL, 1, '2021-06-29 10:20:00', '2021-06-29 10:20:00'),
('rh', 'Red Hat', NULL, 1, '2021-06-29 10:20:00', '2021-06-29 10:20:00'),
('vmware', 'VWware', NULL, 1, '2021-06-29 10:20:00', '2021-06-29 10:20:00');



/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;