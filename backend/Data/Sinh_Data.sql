-- Xóa bảng nếu đã tồn tại để reset dữ liệu
--DROP TABLE IF EXISTS MedicalRecords;
--DROP TABLE IF EXISTS Patients;
--DROP TABLE IF EXISTS Examiners;
--DROP TABLE IF EXISTS Appointments;
--DROP TABLE IF EXISTS Sessions;

PRAGMA foreign_keys = ON;

-- Tạo bảng Patients
CREATE TABLE IF NOT EXISTS Patients (
    PatientID INTEGER PRIMARY KEY AUTOINCREMENT,
    FullName TEXT NOT NULL,
    DateOfBirth DATE NOT NULL,
    Gender TEXT NOT NULL CHECK(Gender IN ('Nam', 'Nữ', 'Khác')),
    PhoneNumber TEXT,
    Address TEXT,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tạo bảng Examiners
CREATE TABLE IF NOT EXISTS Examiners (
    ExaminerID INTEGER PRIMARY KEY AUTOINCREMENT,
    FullName TEXT NOT NULL,
    Specialty TEXT NOT NULL,
    PhoneNumber TEXT,
    Email TEXT,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tạo bảng MedicalRecords
CREATE TABLE IF NOT EXISTS MedicalRecords (
    RecordID INTEGER PRIMARY KEY AUTOINCREMENT,
    PatientID INTEGER NOT NULL,
    ExaminerID INTEGER NOT NULL,
    ExaminationDate DATE NOT NULL,
    Diagnosis TEXT,
    Notes TEXT,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (PatientID) REFERENCES Patients(PatientID) ON DELETE CASCADE,
    FOREIGN KEY (ExaminerID) REFERENCES Examiners(ExaminerID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Appointments (
    AppointmentID INTEGER PRIMARY KEY AUTOINCREMENT,
    PatientID INTEGER,
    ExaminerID INTEGER,
    AppointmentDate DATE NOT NULL,
    AppointmentTime TEXT NOT NULL,
    Status TEXT DEFAULT 'Pending',  -- Pending, Confirmed, Cancelled
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (PatientID) REFERENCES Patients(PatientID),
    FOREIGN KEY (ExaminerID) REFERENCES Examiners(ExaminerID)
);

CREATE TABLE IF NOT EXISTS Sessions (
    session_key TEXT PRIMARY KEY,
    session_data TEXT
);


-- Tháng 1: 5 ca
INSERT INTO MedicalRecords (PatientID, ExaminerID, ExaminationDate, Diagnosis, Notes) VALUES
(1, 2, '2024-01-03', 'Cảm cúm', 'Sốt nhẹ, đau họng'),
(5, 7, '2024-01-10', 'Viêm họng', 'Ho khan, đau họng'),
(12, 1, '2024-01-15', 'Đau đầu', 'Đau nửa đầu, chóng mặt'),
(20, 4, '2024-01-22', 'Đau bụng', 'Đau vùng thượng vị'),
(8, 3, '2024-01-28', 'Viêm phổi', 'Ho kéo dài, khó thở');

-- Tháng 2: 8 ca
INSERT INTO MedicalRecords (PatientID, ExaminerID, ExaminationDate, Diagnosis, Notes) VALUES
(2, 5, '2024-02-02', 'Sốt xuất huyết', 'Sốt cao, đau cơ'),
(7, 9, '2024-02-06', 'Viêm phế quản', 'Ho, khó thở'),
(15, 12, '2024-02-09', 'Đau lưng', 'Đau vùng thắt lưng'),
(23, 8, '2024-02-12', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(30, 6, '2024-02-15', 'Tiểu đường', 'Khát nước, tiểu nhiều'),
(18, 10, '2024-02-18', 'Viêm dạ dày', 'Đau bụng, buồn nôn'),
(25, 11, '2024-02-22', 'Viêm gan', 'Mệt mỏi, vàng da'),
(4, 13, '2024-02-26', 'Viêm khớp', 'Đau khớp gối');

-- Tháng 3: 12 ca
INSERT INTO MedicalRecords (PatientID, ExaminerID, ExaminationDate, Diagnosis, Notes) VALUES
(3, 14, '2024-03-01', 'Viêm phổi', 'Ho, sốt'),
(9, 2, '2024-03-04', 'Đau bụng', 'Đau vùng hạ sườn phải'),
(16, 7, '2024-03-07', 'Viêm họng', 'Đau họng, sốt nhẹ'),
(21, 5, '2024-03-10', 'Đau đầu', 'Đau nửa đầu'),
(27, 1, '2024-03-13', 'Viêm phế quản', 'Ho, khó thở'),
(33, 3, '2024-03-16', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(40, 8, '2024-03-19', 'Tiểu đường', 'Khát nước, tiểu nhiều'),
(11, 6, '2024-03-21', 'Viêm dạ dày', 'Đau bụng, buồn nôn'),
(19, 4, '2024-03-23', 'Viêm gan', 'Mệt mỏi, vàng da'),
(24, 15, '2024-03-25', 'Viêm khớp', 'Đau khớp gối'),
(6, 17, '2024-03-27', 'Viêm phổi', 'Ho, sốt'),
(13, 20, '2024-03-29', 'Đau bụng', 'Đau vùng hạ sườn phải');

-- Tháng 4: 15 ca
INSERT INTO MedicalRecords (PatientID, ExaminerID, ExaminationDate, Diagnosis, Notes) VALUES
(10, 16, '2024-04-02', 'Viêm họng', 'Đau họng, sốt nhẹ'),
(14, 18, '2024-04-04', 'Đau đầu', 'Đau nửa đầu'),
(22, 19, '2024-04-06', 'Viêm phế quản', 'Ho, khó thở'),
(28, 12, '2024-04-08', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(35, 11, '2024-04-10', 'Tiểu đường', 'Khát nước, tiểu nhiều'),
(41, 9, '2024-04-12', 'Viêm dạ dày', 'Đau bụng, buồn nôn'),
(17, 8, '2024-04-14', 'Viêm gan', 'Mệt mỏi, vàng da'),
(26, 7, '2024-04-16', 'Viêm khớp', 'Đau khớp gối'),
(32, 6, '2024-04-18', 'Viêm phổi', 'Ho, sốt'),
(38, 5, '2024-04-20', 'Đau bụng', 'Đau vùng hạ sườn phải'),
(44, 4, '2024-04-22', 'Viêm họng', 'Đau họng, sốt nhẹ'),
(20, 3, '2024-04-24', 'Đau đầu', 'Đau nửa đầu'),
(36, 2, '2024-04-26', 'Viêm phế quản', 'Ho, khó thở'),
(42, 1, '2024-04-28', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(48, 13, '2024-04-30', 'Tiểu đường', 'Khát nước, tiểu nhiều');

-- Tháng 5: 20 ca
INSERT INTO MedicalRecords (PatientID, ExaminerID, ExaminationDate, Diagnosis, Notes) VALUES
(5, 2, '2024-05-01', 'Viêm dạ dày', 'Đau bụng, buồn nôn'),
(11, 3, '2024-05-02', 'Viêm gan', 'Mệt mỏi, vàng da'),
(18, 4, '2024-05-03', 'Viêm khớp', 'Đau khớp gối'),
(24, 5, '2024-05-04', 'Viêm phổi', 'Ho, sốt'),
(30, 6, '2024-05-05', 'Đau bụng', 'Đau vùng hạ sườn phải'),
(36, 7, '2024-05-06', 'Viêm họng', 'Đau họng, sốt nhẹ'),
(42, 8, '2024-05-07', 'Đau đầu', 'Đau nửa đầu'),
(48, 9, '2024-05-08', 'Viêm phế quản', 'Ho, khó thở'),
(4, 10, '2024-05-09', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(10, 11, '2024-05-10', 'Tiểu đường', 'Khát nước, tiểu nhiều'),
(16, 12, '2024-05-11', 'Viêm dạ dày', 'Đau bụng, buồn nôn'),
(22, 13, '2024-05-12', 'Viêm gan', 'Mệt mỏi, vàng da'),
(28, 14, '2024-05-13', 'Viêm khớp', 'Đau khớp gối'),
(34, 15, '2024-05-14', 'Viêm phổi', 'Ho, sốt'),
(40, 16, '2024-05-15', 'Đau bụng', 'Đau vùng hạ sườn phải'),
(46, 17, '2024-05-16', 'Viêm họng', 'Đau họng, sốt nhẹ'),
(3, 18, '2024-05-17', 'Đau đầu', 'Đau nửa đầu'),
(9, 19, '2024-05-18', 'Viêm phế quản', 'Ho, khó thở'),
(15, 20, '2024-05-19', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(21, 1, '2024-05-20', 'Tiểu đường', 'Khát nước, tiểu nhiều');

-- Tháng 6: 25 ca
INSERT INTO MedicalRecords (PatientID, ExaminerID, ExaminationDate, Diagnosis, Notes) VALUES
(6, 2, '2024-06-01', 'Viêm dạ dày', 'Đau bụng, buồn nôn'),
(12, 3, '2024-06-02', 'Viêm gan', 'Mệt mỏi, vàng da'),
(18, 4, '2024-06-03', 'Viêm khớp', 'Đau khớp gối'),
(24, 5, '2024-06-04', 'Viêm phổi', 'Ho, sốt'),
(30, 6, '2024-06-05', 'Đau bụng', 'Đau vùng hạ sườn phải'),
(36, 7, '2024-06-06', 'Viêm họng', 'Đau họng, sốt nhẹ'),
(42, 8, '2024-06-07', 'Đau đầu', 'Đau nửa đầu'),
(48, 9, '2024-06-08', 'Viêm phế quản', 'Ho, khó thở'),
(2, 10, '2024-06-09', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(8, 11, '2024-06-10', 'Tiểu đường', 'Khát nước, tiểu nhiều'),
(14, 12, '2024-06-11', 'Viêm dạ dày', 'Đau bụng, buồn nôn'),
(20, 13, '2024-06-12', 'Viêm gan', 'Mệt mỏi, vàng da'),
(26, 14, '2024-06-13', 'Viêm khớp', 'Đau khớp gối'),
(32, 15, '2024-06-14', 'Viêm phổi', 'Ho, sốt'),
(38, 16, '2024-06-15', 'Đau bụng', 'Đau vùng hạ sườn phải'),
(44, 17, '2024-06-16', 'Viêm họng', 'Đau họng, sốt nhẹ'),
(1, 18, '2024-06-17', 'Đau đầu', 'Đau nửa đầu'),
(7, 19, '2024-06-18', 'Viêm phế quản', 'Ho, khó thở'),
(13, 20, '2024-06-19', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(19, 1, '2024-06-20', 'Tiểu đường', 'Khát nước, tiểu nhiều'),
(25, 2, '2024-06-21', 'Viêm dạ dày', 'Đau bụng, buồn nôn'),
(31, 3, '2024-06-22', 'Viêm gan', 'Mệt mỏi, vàng da'),
(37, 4, '2024-06-23', 'Viêm khớp', 'Đau khớp gối'),
(43, 5, '2024-06-24', 'Viêm phổi', 'Ho, sốt'),
(49, 6, '2024-06-25', 'Đau bụng', 'Đau vùng hạ sườn phải');

-- Tháng 7: 30 ca
INSERT INTO MedicalRecords (PatientID, ExaminerID, ExaminationDate, Diagnosis, Notes) VALUES
(3, 7, '2024-07-01', 'Viêm họng', 'Đau họng, sốt nhẹ'),
(9, 8, '2024-07-02', 'Đau đầu', 'Đau nửa đầu'),
(15, 9, '2024-07-03', 'Viêm phế quản', 'Ho, khó thở'),
(21, 10, '2024-07-04', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(27, 11, '2024-07-05', 'Tiểu đường', 'Khát nước, tiểu nhiều'),
(33, 12, '2024-07-06', 'Viêm dạ dày', 'Đau bụng, buồn nôn'),
(39, 13, '2024-07-07', 'Viêm gan', 'Mệt mỏi, vàng da'),
(45, 14, '2024-07-08', 'Viêm khớp', 'Đau khớp gối'),
(5, 15, '2024-07-09', 'Viêm phổi', 'Ho, sốt'),
(11, 16, '2024-07-10', 'Đau bụng', 'Đau vùng hạ sườn phải'),
(17, 17, '2024-07-11', 'Viêm họng', 'Đau họng, sốt nhẹ'),
(23, 18, '2024-07-12', 'Đau đầu', 'Đau nửa đầu'),
(29, 19, '2024-07-13', 'Viêm phế quản', 'Ho, khó thở'),
(35, 20, '2024-07-14', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(41, 1, '2024-07-15', 'Tiểu đường', 'Khát nước, tiểu nhiều'),
(47, 2, '2024-07-16', 'Viêm dạ dày', 'Đau bụng, buồn nôn'),
(6, 3, '2024-07-17', 'Viêm gan', 'Mệt mỏi, vàng da'),
(12, 4, '2024-07-18', 'Viêm khớp', 'Đau khớp gối'),
(18, 5, '2024-07-19', 'Viêm phổi', 'Ho, sốt'),
(24, 6, '2024-07-20', 'Đau bụng', 'Đau vùng hạ sườn phải'),
(30, 7, '2024-07-21', 'Viêm họng', 'Đau họng, sốt nhẹ'),
(36, 8, '2024-07-22', 'Đau đầu', 'Đau nửa đầu'),
(42, 9, '2024-07-23', 'Viêm phế quản', 'Ho, khó thở'),
(48, 10, '2024-07-24', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(4, 11, '2024-07-25', 'Tiểu đường', 'Khát nước, tiểu nhiều'),
(10, 12, '2024-07-26', 'Viêm dạ dày', 'Đau bụng, buồn nôn'),
(16, 13, '2024-07-27', 'Viêm gan', 'Mệt mỏi, vàng da'),
(22, 14, '2024-07-28', 'Viêm khớp', 'Đau khớp gối'),
(28, 15, '2024-07-29', 'Viêm phổi', 'Ho, sốt'),
(34, 16, '2024-07-30', 'Đau bụng', 'Đau vùng hạ sườn phải');

-- Tháng 8: 28 ca
INSERT INTO MedicalRecords (PatientID, ExaminerID, ExaminationDate, Diagnosis, Notes) VALUES
(8, 17, '2024-08-01', 'Viêm họng', 'Đau họng, sốt nhẹ'),
(14, 18, '2024-08-02', 'Đau đầu', 'Đau nửa đầu'),
(20, 19, '2024-08-03', 'Viêm phế quản', 'Ho, khó thở'),
(26, 20, '2024-08-04', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(32, 1, '2024-08-05', 'Tiểu đường', 'Khát nước, tiểu nhiều'),
(38, 2, '2024-08-06', 'Viêm dạ dày', 'Đau bụng, buồn nôn'),
(44, 3, '2024-08-07', 'Viêm gan', 'Mệt mỏi, vàng da'),
(50, 4, '2024-08-08', 'Viêm khớp', 'Đau khớp gối'),
(7, 5, '2024-08-09', 'Viêm phổi', 'Ho, sốt'),
(13, 6, '2024-08-10', 'Đau bụng', 'Đau vùng hạ sườn phải'),
(19, 7, '2024-08-11', 'Viêm họng', 'Đau họng, sốt nhẹ'),
(25, 8, '2024-08-12', 'Đau đầu', 'Đau nửa đầu'),
(31, 9, '2024-08-13', 'Viêm phế quản', 'Ho, khó thở'),
(37, 10, '2024-08-14', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(43, 11, '2024-08-15', 'Tiểu đường', 'Khát nước, tiểu nhiều'),
(49, 12, '2024-08-16', 'Viêm dạ dày', 'Đau bụng, buồn nôn'),
(5, 13, '2024-08-17', 'Viêm gan', 'Mệt mỏi, vàng da'),
(11, 14, '2024-08-18', 'Viêm khớp', 'Đau khớp gối'),
(17, 15, '2024-08-19', 'Viêm phổi', 'Ho, sốt'),
(23, 16, '2024-08-20', 'Đau bụng', 'Đau vùng hạ sườn phải'),
(29, 17, '2024-08-21', 'Viêm họng', 'Đau họng, sốt nhẹ'),
(35, 18, '2024-08-22', 'Đau đầu', 'Đau nửa đầu'),
(41, 19, '2024-08-23', 'Viêm phế quản', 'Ho, khó thở'),
(47, 20, '2024-08-24', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(6, 1, '2024-08-25', 'Tiểu đường', 'Khát nước, tiểu nhiều'),
(12, 2, '2024-08-26', 'Viêm dạ dày', 'Đau bụng, buồn nôn'),
(18, 3, '2024-08-27', 'Viêm gan', 'Mệt mỏi, vàng da'),
(24, 4, '2024-08-28', 'Viêm khớp', 'Đau khớp gối');

-- Tháng 9: 22 ca
INSERT INTO MedicalRecords (PatientID, ExaminerID, ExaminationDate, Diagnosis, Notes) VALUES
(9, 5, '2024-09-01', 'Viêm phổi', 'Ho, sốt'),
(15, 6, '2024-09-02', 'Đau bụng', 'Đau vùng hạ sườn phải'),
(21, 7, '2024-09-03', 'Viêm họng', 'Đau họng, sốt nhẹ'),
(27, 8, '2024-09-04', 'Đau đầu', 'Đau nửa đầu'),
(33, 9, '2024-09-05', 'Viêm phế quản', 'Ho, khó thở'),
(39, 10, '2024-09-06', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(45, 11, '2024-09-07', 'Tiểu đường', 'Khát nước, tiểu nhiều'),
(1, 12, '2024-09-08', 'Viêm dạ dày', 'Đau bụng, buồn nôn'),
(7, 13, '2024-09-09', 'Viêm gan', 'Mệt mỏi, vàng da'),
(13, 14, '2024-09-10', 'Viêm khớp', 'Đau khớp gối'),
(19, 15, '2024-09-11', 'Viêm phổi', 'Ho, sốt'),
(25, 16, '2024-09-12', 'Đau bụng', 'Đau vùng hạ sườn phải'),
(31, 17, '2024-09-13', 'Viêm họng', 'Đau họng, sốt nhẹ'),
(37, 18, '2024-09-14', 'Đau đầu', 'Đau nửa đầu'),
(43, 19, '2024-09-15', 'Viêm phế quản', 'Ho, khó thở'),
(49, 20, '2024-09-16', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(5, 1, '2024-09-17', 'Tiểu đường', 'Khát nước, tiểu nhiều'),
(11, 2, '2024-09-18', 'Viêm dạ dày', 'Đau bụng, buồn nôn'),
(17, 3, '2024-09-19', 'Viêm gan', 'Mệt mỏi, vàng da'),
(23, 4, '2024-09-20', 'Viêm khớp', 'Đau khớp gối'),
(29, 5, '2024-09-21', 'Viêm phổi', 'Ho, sốt'),
(35, 6, '2024-09-22', 'Đau bụng', 'Đau vùng hạ sườn phải');

-- Tháng 10: 18 ca
INSERT INTO MedicalRecords (PatientID, ExaminerID, ExaminationDate, Diagnosis, Notes) VALUES
(10, 7, '2024-10-01', 'Viêm họng', 'Đau họng, sốt nhẹ'),
(16, 8, '2024-10-02', 'Đau đầu', 'Đau nửa đầu'),
(22, 9, '2024-10-03', 'Viêm phế quản', 'Ho, khó thở'),
(28, 10, '2024-10-04', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(34, 11, '2024-10-05', 'Tiểu đường', 'Khát nước, tiểu nhiều'),
(40, 12, '2024-10-06', 'Viêm dạ dày', 'Đau bụng, buồn nôn'),
(46, 13, '2024-10-07', 'Viêm gan', 'Mệt mỏi, vàng da'),
(2, 14, '2024-10-08', 'Viêm khớp', 'Đau khớp gối'),
(8, 15, '2024-10-09', 'Viêm phổi', 'Ho, sốt'),
(14, 16, '2024-10-10', 'Đau bụng', 'Đau vùng hạ sườn phải'),
(20, 17, '2024-10-11', 'Viêm họng', 'Đau họng, sốt nhẹ'),
(26, 18, '2024-10-12', 'Đau đầu', 'Đau nửa đầu'),
(32, 19, '2024-10-13', 'Viêm phế quản', 'Ho, khó thở'),
(38, 20, '2024-10-14', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(44, 1, '2024-10-15', 'Tiểu đường', 'Khát nước, tiểu nhiều'),
(3, 2, '2024-10-16', 'Viêm dạ dày', 'Đau bụng, buồn nôn'),
(9, 3, '2024-10-17', 'Viêm gan', 'Mệt mỏi, vàng da'),
(15, 4, '2024-10-18', 'Viêm khớp', 'Đau khớp gối');

-- Tháng 11: 10 ca
INSERT INTO MedicalRecords (PatientID, ExaminerID, ExaminationDate, Diagnosis, Notes) VALUES
(21, 5, '2024-11-01', 'Viêm phổi', 'Ho, sốt'),
(27, 6, '2024-11-03', 'Đau bụng', 'Đau vùng hạ sườn phải'),
(33, 7, '2024-11-05', 'Viêm họng', 'Đau họng, sốt nhẹ'),
(39, 8, '2024-11-07', 'Đau đầu', 'Đau nửa đầu'),
(45, 9, '2024-11-09', 'Viêm phế quản', 'Ho, khó thở'),
(1, 10, '2024-11-11', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(7, 11, '2024-11-13', 'Tiểu đường', 'Khát nước, tiểu nhiều'),
(13, 12, '2024-11-15', 'Viêm dạ dày', 'Đau bụng, buồn nôn'),
(19, 13, '2024-11-17', 'Viêm gan', 'Mệt mỏi, vàng da'),
(25, 14, '2024-11-19', 'Viêm khớp', 'Đau khớp gối');

-- Tháng 12: 7 ca
INSERT INTO MedicalRecords (PatientID, ExaminerID, ExaminationDate, Diagnosis, Notes) VALUES
(31, 15, '2024-12-01', 'Viêm phổi', 'Ho, sốt'),
(37, 16, '2024-12-05', 'Đau bụng', 'Đau vùng hạ sườn phải'),
(43, 17, '2024-12-09', 'Viêm họng', 'Đau họng, sốt nhẹ'),
(49, 18, '2024-12-13', 'Đau đầu', 'Đau nửa đầu'),
(5, 19, '2024-12-17', 'Viêm phế quản', 'Ho, khó thở'),
(11, 20, '2024-12-21', 'Viêm xoang', 'Đau đầu, nghẹt mũi'),
(17, 1, '2024-12-25', 'Tiểu đường', 'Khát nước, tiểu nhiều');