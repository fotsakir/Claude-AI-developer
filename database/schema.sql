-- MySQL dump 10.13  Distrib 8.0.44, for Linux (x86_64)
--
-- Host: localhost    Database: claude_knowledge
-- ------------------------------------------------------
-- Server version	8.0.44-0ubuntu0.24.04.2

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `conversation_messages`
--

DROP TABLE IF EXISTS `conversation_messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `conversation_messages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ticket_id` int NOT NULL,
  `session_id` int DEFAULT NULL,
  `role` enum('user','assistant','system','tool_use','tool_result') NOT NULL,
  `content` text,
  `tool_name` varchar(100) DEFAULT NULL,
  `tool_input` json DEFAULT NULL,
  `tokens_used` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_ticket` (`ticket_id`),
  CONSTRAINT `conversation_messages_ibfk_1` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=665 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `daemon_status`
--

DROP TABLE IF EXISTS `daemon_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `daemon_status` (
  `id` int NOT NULL DEFAULT '1',
  `status` enum('running','stopped','error') DEFAULT 'stopped',
  `current_ticket_id` int DEFAULT NULL,
  `current_session_id` int DEFAULT NULL,
  `last_heartbeat` timestamp NULL DEFAULT NULL,
  `started_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `developers`
--

DROP TABLE IF EXISTS `developers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `developers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `role` enum('admin','developer','viewer') DEFAULT 'developer',
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `last_login` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `execution_logs`
--

DROP TABLE IF EXISTS `execution_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `execution_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `session_id` int NOT NULL,
  `log_type` enum('info','output','error','warning','user') DEFAULT 'output',
  `message` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_session` (`session_id`),
  CONSTRAINT `execution_logs_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `execution_sessions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=649 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `execution_sessions`
--

DROP TABLE IF EXISTS `execution_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `execution_sessions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ticket_id` int DEFAULT NULL,
  `status` enum('running','completed','failed','stuck','stopped','skipped') DEFAULT 'running',
  `tokens_used` int DEFAULT '0',
  `started_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `ended_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ticket_id` (`ticket_id`),
  CONSTRAINT `execution_sessions_ibfk_1` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=43 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `projects`
--

DROP TABLE IF EXISTS `projects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `projects` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `code` varchar(10) NOT NULL,
  `description` text,
  `project_type` enum('web','app','hybrid','api','other') DEFAULT 'web',
  `tech_stack` varchar(255) DEFAULT NULL,
  `web_path` varchar(500) DEFAULT NULL,
  `preview_url` varchar(500) DEFAULT NULL,
  `app_path` varchar(500) DEFAULT NULL,
  `context` text,
  `status` enum('active','archived','paused') DEFAULT 'active',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `db_name` varchar(100) DEFAULT NULL,
  `db_user` varchar(100) DEFAULT NULL,
  `db_password` varchar(255) DEFAULT NULL,
  `db_host` varchar(255) DEFAULT 'localhost',
  `total_tokens` int DEFAULT '0',
  `total_duration_seconds` int DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `idx_status` (`status`),
  KEY `idx_code` (`code`),
  KEY `idx_db_name` (`db_name`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tickets`
--

DROP TABLE IF EXISTS `tickets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tickets` (
  `id` int NOT NULL AUTO_INCREMENT,
  `project_id` int NOT NULL,
  `ticket_number` varchar(20) NOT NULL,
  `title` varchar(500) NOT NULL,
  `description` text,
  `context` text,
  `priority` enum('low','medium','high','critical') DEFAULT 'medium',
  `status` enum('new','open','pending','in_progress','awaiting_input','done','failed','stuck','skipped') DEFAULT 'open',
  `result_summary` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `closed_at` timestamp NULL DEFAULT NULL,
  `closed_by` varchar(50) DEFAULT NULL,
  `close_reason` enum('completed','manual','timeout','skipped','failed','approved','auto_approved_7days') DEFAULT NULL,
  `review_deadline` datetime DEFAULT NULL,
  `total_tokens` int DEFAULT '0',
  `total_duration_seconds` int DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ticket_number` (`ticket_number`),
  KEY `idx_project_status` (`project_id`,`status`),
  KEY `idx_status` (`status`),
  CONSTRAINT `tickets_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_messages`
--

DROP TABLE IF EXISTS `user_messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_messages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ticket_id` int DEFAULT NULL,
  `user_id` int DEFAULT NULL,
  `content` text NOT NULL,
  `message_type` enum('command','message','input') DEFAULT 'message',
  `processed` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_ticket` (`ticket_id`),
  KEY `idx_processed` (`processed`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `usage_stats`
--

DROP TABLE IF EXISTS `usage_stats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usage_stats` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ticket_id` int NOT NULL,
  `project_id` int NOT NULL,
  `session_id` int DEFAULT NULL,
  `input_tokens` int DEFAULT '0',
  `output_tokens` int DEFAULT '0',
  `total_tokens` int DEFAULT '0',
  `cache_read_tokens` int DEFAULT '0',
  `cache_creation_tokens` int DEFAULT '0',
  `duration_seconds` int DEFAULT '0',
  `api_calls` int DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_usage_project` (`project_id`),
  KEY `idx_usage_ticket` (`ticket_id`),
  KEY `idx_usage_created` (`created_at`),
  KEY `idx_usage_project_created` (`project_id`,`created_at`),
  CONSTRAINT `usage_stats_ibfk_1` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`) ON DELETE CASCADE,
  CONSTRAINT `usage_stats_ibfk_2` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `usage_stats_ibfk_3` FOREIGN KEY (`session_id`) REFERENCES `execution_sessions` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Default data for daemon_status
--

INSERT INTO `daemon_status` (`id`, `status`, `current_ticket_id`, `current_session_id`, `last_heartbeat`, `started_at`)
VALUES (1, 'stopped', NULL, NULL, NULL, NULL);

--
-- Default admin user (password: admin123)
--

INSERT INTO `developers` (`username`, `password_hash`, `role`, `is_active`)
VALUES ('admin', '$2b$12$szAIZl2ejy.Y5Bj98prT3eZ2/ruBWlHqpwPtBhHj3pPC1Rk3PZsKO', 'admin', 1);

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-08
-- Updated: Added usage_stats table, fixed awaiting_input status, removed simplevehi_vehicles
