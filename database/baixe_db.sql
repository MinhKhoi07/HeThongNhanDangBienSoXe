-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Máy chủ: 127.0.0.1
-- Thời gian đã tạo: Th1 29, 2026 lúc 06:36 PM
-- Phiên bản máy phục vụ: 10.4.32-MariaDB
-- Phiên bản PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Cơ sở dữ liệu: `baixe_db`
--

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `bienso`
--

CREATE TABLE `bienso` (
  `id` int(11) UNSIGNED NOT NULL,
  `so_bien` varchar(20) NOT NULL,
  `chu_xe` varchar(100) NOT NULL,
  `sdt` varchar(15) DEFAULT NULL,
  `ngay_dang_ky` date DEFAULT current_timestamp(),
  `trang_thai` int(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `lichsu`
--

CREATE TABLE `lichsu` (
  `id` int(11) UNSIGNED NOT NULL,
  `so_bien` varchar(20) NOT NULL,
  `thoi_gian` datetime NOT NULL DEFAULT current_timestamp(),
  `loai_su_kien` varchar(10) DEFAULT 'VAO',
  `duong_dan_anh` text DEFAULT NULL,
  `ghi_chu` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Chỉ mục cho các bảng đã đổ
--

--
-- Chỉ mục cho bảng `bienso`
--
ALTER TABLE `bienso`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `so_bien` (`so_bien`);

--
-- Chỉ mục cho bảng `lichsu`
--
ALTER TABLE `lichsu`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_lichsu_so_bien` (`so_bien`);

--
-- Ràng buộc liên kết giữa lichsu và bienso
--
ALTER TABLE `lichsu`
  ADD CONSTRAINT `fk_lichsu_bienso`
  FOREIGN KEY (`so_bien`) REFERENCES `bienso` (`so_bien`)
  ON UPDATE CASCADE
  ON DELETE RESTRICT;

--
-- AUTO_INCREMENT cho các bảng đã đổ
--

--
-- AUTO_INCREMENT cho bảng `bienso`
--
ALTER TABLE `bienso`
  MODIFY `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT cho bảng `lichsu`
--
ALTER TABLE `lichsu`
  MODIFY `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
