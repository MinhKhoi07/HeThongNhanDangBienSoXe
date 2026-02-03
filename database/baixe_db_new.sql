-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Máy chủ: 127.0.0.1
-- Thời gian đã tạo: Feb 03, 2026
-- Phiên bản máy phục vụ: 10.4.32-MariaDB
-- Phiên bản PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

-- --------------------------------------------------------
-- Cơ sở dữ liệu: `baixe_db`
-- --------------------------------------------------------

DROP TABLE IF EXISTS `thanh_toan`;
DROP TABLE IF EXISTS `vi_pham`;
DROP TABLE IF EXISTS `danh_sach_den`;
DROP TABLE IF EXISTS `chi_tiet_xe`;
DROP TABLE IF EXISTS `lichsu`;
DROP TABLE IF EXISTS `bienso`;
DROP TABLE IF EXISTS `users`;

-- --------------------------------------------------------
-- Cấu trúc bảng cho bảng `users`
-- --------------------------------------------------------

CREATE TABLE `users` (
  `id` int(11) UNSIGNED NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `ho_ten` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `vai_tro` enum('admin','operator','viewer') DEFAULT 'operator',
  `trang_thai` int(1) DEFAULT 1,
  `ngay_tao` datetime DEFAULT CURRENT_TIMESTAMP,
  `ngay_cap_nhat` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------
-- Cấu trúc bảng cho bảng `bienso`
-- --------------------------------------------------------

CREATE TABLE `bienso` (
  `id` int(11) UNSIGNED NOT NULL,
  `so_bien` varchar(20) NOT NULL,
  `chu_xe` varchar(100) NOT NULL,
  `sdt` varchar(15) DEFAULT NULL,
  `email_chu_xe` varchar(100) DEFAULT NULL,
  `ngay_dang_ky` date DEFAULT CURRENT_DATE,
  `trang_thai` int(1) DEFAULT 1 COMMENT '1=Hoạt động, 0=Tạm dừng',
  `tong_lan_vao` int(11) DEFAULT 0,
  `tong_lan_ra` int(11) DEFAULT 0,
  `lan_vao_gan_nhat` datetime DEFAULT NULL,
  `lan_ra_gan_nhat` datetime DEFAULT NULL,
  `ghi_chu` text DEFAULT NULL,
  `ngay_cap_nhat` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------
-- Cấu trúc bảng cho bảng `chi_tiet_xe`
-- --------------------------------------------------------

CREATE TABLE `chi_tiet_xe` (
  `id` int(11) UNSIGNED NOT NULL,
  `so_bien` varchar(20) NOT NULL,
  `loai_xe` enum('4cho','7cho','giaothong','moto','khac') DEFAULT '4cho',
  `hang_xe` varchar(50) DEFAULT NULL,
  `mau_xe` varchar(30) DEFAULT NULL,
  `nam_san_xuat` int(4) DEFAULT NULL,
  `ma_khung` varchar(50) DEFAULT NULL,
  `ma_may` varchar(50) DEFAULT NULL,
  `ngay_cap_nhat` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------
-- Cấu trúc bảng cho bảng `lichsu`
-- --------------------------------------------------------

CREATE TABLE `lichsu` (
  `id` int(11) UNSIGNED NOT NULL,
  `so_bien` varchar(20) NOT NULL,
  `thoi_gian` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `loai_su_kien` varchar(10) DEFAULT 'VAO' COMMENT 'VAO hoac RA',
  `duong_dan_anh` text DEFAULT NULL,
  `duong_dan_anh_goc` text DEFAULT NULL,
  `ghi_chu` text DEFAULT NULL,
  `operator_id` int(11) UNSIGNED DEFAULT NULL COMMENT 'Người thực hiện',
  `ngay_cap_nhat` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------
-- Cấu trúc bảng cho bảng `danh_sach_den`
-- --------------------------------------------------------

CREATE TABLE `danh_sach_den` (
  `id` int(11) UNSIGNED NOT NULL,
  `so_bien` varchar(20) NOT NULL,
  `ly_do` varchar(255) DEFAULT NULL,
  `muc_do_canh_bao` enum('cao','trung','thap') DEFAULT 'trung',
  `ngay_tao` datetime DEFAULT CURRENT_TIMESTAMP,
  `ngay_het_hieu_luc` datetime DEFAULT NULL,
  `trang_thai` int(1) DEFAULT 1,
  `ghi_chu` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------
-- Cấu trúc bảng cho bảng `vi_pham`
-- --------------------------------------------------------

CREATE TABLE `vi_pham` (
  `id` int(11) UNSIGNED NOT NULL,
  `so_bien` varchar(20) NOT NULL,
  `loai_vi_pham` varchar(50) DEFAULT NULL COMMENT 'nợ phí, vượt quá giới hạn, etc',
  `muc_phat` decimal(10,2) DEFAULT 0.00,
  `trang_thai` enum('chua_xu_ly','da_xu_ly','khong_hop_le') DEFAULT 'chua_xu_ly',
  `ngay_phat_hien` datetime DEFAULT CURRENT_TIMESTAMP,
  `ngay_xu_ly` datetime DEFAULT NULL,
  `ghi_chu` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------
-- Cấu trúc bảng cho bảng `thanh_toan`
-- --------------------------------------------------------

CREATE TABLE `thanh_toan` (
  `id` int(11) UNSIGNED NOT NULL,
  `so_bien` varchar(20) NOT NULL,
  `so_tien` decimal(12,2) NOT NULL,
  `loai_thanh_toan` enum('giu_xe','vi_pham','khac') DEFAULT 'giu_xe',
  `phuong_thuc` enum('tien_mat','the_tin_dung','ck_ngan_hang','khac') DEFAULT 'tien_mat',
  `trang_thai` enum('chua_thanh_toan','da_thanh_toan','huy') DEFAULT 'chua_thanh_toan',
  `ngay_tao` datetime DEFAULT CURRENT_TIMESTAMP,
  `ngay_thanh_toan` datetime DEFAULT NULL,
  `ma_giao_dich` varchar(50) DEFAULT NULL,
  `ghi_chu` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------
-- Chỉ mục cho các bảng đã đổ
-- --------------------------------------------------------

-- --------------------------------------------------------
-- Chỉ mục cho bảng `users`
-- --------------------------------------------------------
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD KEY `idx_users_vai_tro` (`vai_tro`);

-- --------------------------------------------------------
-- Chỉ mục cho bảng `bienso`
-- --------------------------------------------------------
ALTER TABLE `bienso`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `so_bien` (`so_bien`),
  ADD KEY `idx_bienso_chu_xe` (`chu_xe`),
  ADD KEY `idx_bienso_sdt` (`sdt`),
  ADD KEY `idx_bienso_trang_thai` (`trang_thai`),
  ADD KEY `idx_bienso_ngay_dang_ky` (`ngay_dang_ky`);

-- --------------------------------------------------------
-- Chỉ mục cho bảng `chi_tiet_xe`
-- --------------------------------------------------------
ALTER TABLE `chi_tiet_xe`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `so_bien` (`so_bien`),
  ADD KEY `idx_chi_tiet_loai_xe` (`loai_xe`);

-- --------------------------------------------------------
-- Chỉ mục cho bảng `lichsu`
-- --------------------------------------------------------
ALTER TABLE `lichsu`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_lichsu_so_bien` (`so_bien`),
  ADD KEY `idx_lichsu_thoi_gian` (`thoi_gian`),
  ADD KEY `idx_lichsu_loai_su_kien` (`loai_su_kien`),
  ADD KEY `idx_lichsu_operator` (`operator_id`);

-- --------------------------------------------------------
-- Chỉ mục cho bảng `danh_sach_den`
-- --------------------------------------------------------
ALTER TABLE `danh_sach_den`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `so_bien` (`so_bien`),
  ADD KEY `idx_danh_sach_den_trang_thai` (`trang_thai`),
  ADD KEY `idx_danh_sach_den_muc_do` (`muc_do_canh_bao`);

-- --------------------------------------------------------
-- Chỉ mục cho bảng `vi_pham`
-- --------------------------------------------------------
ALTER TABLE `vi_pham`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_vi_pham_so_bien` (`so_bien`),
  ADD KEY `idx_vi_pham_trang_thai` (`trang_thai`),
  ADD KEY `idx_vi_pham_ngay_phat_hien` (`ngay_phat_hien`);

-- --------------------------------------------------------
-- Chỉ mục cho bảng `thanh_toan`
-- --------------------------------------------------------
ALTER TABLE `thanh_toan`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_thanh_toan_so_bien` (`so_bien`),
  ADD KEY `idx_thanh_toan_trang_thai` (`trang_thai`),
  ADD KEY `idx_thanh_toan_ngay_tao` (`ngay_tao`),
  ADD KEY `idx_thanh_toan_ma_giao_dich` (`ma_giao_dich`);

-- --------------------------------------------------------
-- Ràng buộc liên kết (Foreign Keys)
-- --------------------------------------------------------

-- Ràng buộc cho bảng `chi_tiet_xe`
ALTER TABLE `chi_tiet_xe`
  ADD CONSTRAINT `fk_chi_tiet_bienso` FOREIGN KEY (`so_bien`) REFERENCES `bienso` (`so_bien`) ON UPDATE CASCADE ON DELETE CASCADE;

-- Ràng buộc cho bảng `lichsu`
ALTER TABLE `lichsu`
  ADD CONSTRAINT `fk_lichsu_bienso` FOREIGN KEY (`so_bien`) REFERENCES `bienso` (`so_bien`) ON UPDATE CASCADE ON DELETE RESTRICT,
  ADD CONSTRAINT `fk_lichsu_operator` FOREIGN KEY (`operator_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE SET NULL;

-- Ràng buộc cho bảng `danh_sach_den`
ALTER TABLE `danh_sach_den`
  ADD CONSTRAINT `fk_danh_sach_den_bienso` FOREIGN KEY (`so_bien`) REFERENCES `bienso` (`so_bien`) ON UPDATE CASCADE ON DELETE CASCADE;

-- Ràng buộc cho bảng `vi_pham`
ALTER TABLE `vi_pham`
  ADD CONSTRAINT `fk_vi_pham_bienso` FOREIGN KEY (`so_bien`) REFERENCES `bienso` (`so_bien`) ON UPDATE CASCADE ON DELETE CASCADE;

-- Ràng buộc cho bảng `thanh_toan`
ALTER TABLE `thanh_toan`
  ADD CONSTRAINT `fk_thanh_toan_bienso` FOREIGN KEY (`so_bien`) REFERENCES `bienso` (`so_bien`) ON UPDATE CASCADE ON DELETE CASCADE;

-- --------------------------------------------------------
-- AUTO_INCREMENT cho các bảng đã đổ
-- --------------------------------------------------------

ALTER TABLE `users`
  MODIFY `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT;

ALTER TABLE `bienso`
  MODIFY `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT;

ALTER TABLE `chi_tiet_xe`
  MODIFY `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT;

ALTER TABLE `lichsu`
  MODIFY `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT;

ALTER TABLE `danh_sach_den`
  MODIFY `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT;

ALTER TABLE `vi_pham`
  MODIFY `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT;

ALTER TABLE `thanh_toan`
  MODIFY `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT;

-- --------------------------------------------------------
-- Dữ liệu mẫu (Optional - Bạn có thể xóa phần này)
-- --------------------------------------------------------

-- Thêm tài khoản admin mặc định
INSERT INTO `users` (`username`, `password`, `ho_ten`, `email`, `vai_tro`, `trang_thai`) VALUES
('admin', 'admin123', 'Admin', 'admin@baixe.local', 'admin', 1),
('operator1', 'op123', 'Nhân viên 1', 'op1@baixe.local', 'operator', 1),
('viewer1', 'view123', 'Xem dữ liệu', 'view1@baixe.local', 'viewer', 1);

COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
