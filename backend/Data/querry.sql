-- 1. Tổng số bệnh nhân
SELECT COUNT(*) AS total_patients FROM Patients;

-- 2. Tổng số bác sĩ
SELECT COUNT(*) AS total_examiners FROM Examiners;

-- 3. Tổng số hồ sơ khám bệnh
SELECT COUNT(*) AS total_medical_records FROM MedicalRecords;

-- 4. Danh sách tất cả bệnh nhân
SELECT * FROM Patients;

-- 5. Danh sách tất cả bác sĩ
SELECT * FROM Examiners;

-- 6. Danh sách tất cả hồ sơ khám bệnh
SELECT * FROM MedicalRecords;

-- 7. Tổng số bệnh nhân theo giới tính
SELECT Gender, COUNT(*) AS total FROM Patients GROUP BY Gender;

-- 8. Danh sách bệnh nhân sinh sau năm 1990
SELECT * FROM Patients WHERE DateOfBirth > '1990-01-01';

-- 9. Danh sách bác sĩ chuyên khoa "Nội khoa"
SELECT * FROM Examiners WHERE Specialty = 'Nội khoa';

-- 10. Danh sách bệnh nhân có địa chỉ ở Hà Nội
SELECT * FROM Patients WHERE Address LIKE '%Hà Nội%';

-- 11. Danh sách bệnh nhân có số điện thoại bắt đầu bằng '090'
SELECT * FROM Patients WHERE PhoneNumber LIKE '090%';

-- 12. Danh sách bác sĩ có email chứa 'hospital.vn'
SELECT * FROM Examiners WHERE Email LIKE '%hospital.vn%';

-- 13. Danh sách bệnh nhân nữ
SELECT * FROM Patients WHERE Gender = 'Nữ';

-- 14. Danh sách bệnh nhân nam
SELECT * FROM Patients WHERE Gender = 'Nam';

-- 15. Danh sách bệnh nhân có năm sinh từ 1980 đến 1990
SELECT * FROM Patients WHERE DateOfBirth BETWEEN '1980-01-01' AND '1990-12-31';

-- 16. Danh sách bác sĩ có số điện thoại kết thúc bằng '1234'
SELECT * FROM Examiners WHERE PhoneNumber LIKE '%1234';

-- 17. Danh sách hồ sơ khám bệnh trong năm 2024
SELECT * FROM MedicalRecords WHERE ExaminationDate BETWEEN '2024-01-01' AND '2024-12-31';

-- 18. Danh sách bệnh nhân từng được khám bởi bác sĩ có ExaminerID = 1
SELECT DISTINCT PatientID FROM MedicalRecords WHERE ExaminerID = 1;

-- 19. Danh sách bác sĩ từng khám cho bệnh nhân có PatientID = 1
SELECT DISTINCT ExaminerID FROM MedicalRecords WHERE PatientID = 1;

-- 20. Tổng số lần khám của từng bệnh nhân
SELECT PatientID, COUNT(*) AS total_visits FROM MedicalRecords GROUP BY PatientID;

-- 21. Tổng số lần khám của từng bác sĩ
SELECT ExaminerID, COUNT(*) AS total_exams FROM MedicalRecords GROUP BY ExaminerID;

-- 22. Danh sách bệnh nhân chưa có số điện thoại
SELECT * FROM Patients WHERE PhoneNumber IS NULL OR PhoneNumber = '';

-- 23. Danh sách bác sĩ chưa có email
SELECT * FROM Examiners WHERE Email IS NULL OR Email = '';

-- 24. Danh sách bệnh nhân có địa chỉ ở Đà Nẵng
SELECT * FROM Patients WHERE Address LIKE '%Đà Nẵng%';

-- 25. Danh sách bệnh nhân có địa chỉ ở TP.HCM
SELECT * FROM Patients WHERE Address LIKE '%TP.HCM%';

-- 26. Danh sách bệnh nhân có địa chỉ ở Huế
SELECT * FROM Patients WHERE Address LIKE '%Huế%';

-- 27. Danh sách bệnh nhân có địa chỉ ở Hà Nội hoặc TP.HCM
SELECT * FROM Patients WHERE Address LIKE '%Hà Nội%' OR Address LIKE '%TP.HCM%';

-- 28. Danh sách bác sĩ có chuyên khoa là 'Nhi khoa' hoặc 'Sản khoa'
SELECT * FROM Examiners WHERE Specialty IN ('Nhi khoa', 'Sản khoa');

-- 29. Danh sách bệnh nhân có họ là 'Nguyễn'
SELECT * FROM Patients WHERE FullName LIKE 'Nguyễn%';

-- 30. Danh sách bác sĩ có họ là 'Trần'
SELECT * FROM Examiners WHERE FullName LIKE 'Trần%';

-- 31. Danh sách bệnh nhân có ngày sinh nhật trong tháng 3
SELECT * FROM Patients WHERE strftime('%m', DateOfBirth) = '03';

-- 32. Danh sách bác sĩ có số điện thoại bắt đầu bằng '09'
SELECT * FROM Examiners WHERE PhoneNumber LIKE '09%';

-- 33. Danh sách bệnh nhân có tên chứa 'Lan'
SELECT * FROM Patients WHERE FullName LIKE '%Lan%';

-- 34. Danh sách bác sĩ có tên chứa 'Linh'
SELECT * FROM Examiners WHERE FullName LIKE '%Linh%';

-- 35. Danh sách bệnh nhân có năm sinh là 1990
SELECT * FROM Patients WHERE strftime('%Y', DateOfBirth) = '1990';

-- 36. Danh sách hồ sơ khám bệnh có chẩn đoán là 'Cao huyết áp'
SELECT * FROM MedicalRecords WHERE Diagnosis = 'Cao huyết áp';

-- 37. Danh sách hồ sơ khám bệnh có ghi chú chứa 'tái khám'
SELECT * FROM MedicalRecords WHERE Notes LIKE '%tái khám%';

-- 38. Danh sách bệnh nhân từng được khám bệnh nhiều hơn 2 lần
SELECT PatientID FROM MedicalRecords GROUP BY PatientID HAVING COUNT(*) > 2;

-- 39. Danh sách bác sĩ từng khám cho nhiều hơn 3 bệnh nhân khác nhau
SELECT ExaminerID FROM MedicalRecords GROUP BY ExaminerID HAVING COUNT(DISTINCT PatientID) > 3;

-- 40. Danh sách bệnh nhân chưa từng được khám bệnh
SELECT * FROM Patients WHERE PatientID NOT IN (SELECT PatientID FROM MedicalRecords);

-- 41. Danh sách bác sĩ chưa từng khám cho bệnh nhân nào
SELECT * FROM Examiners WHERE ExaminerID NOT IN (SELECT ExaminerID FROM MedicalRecords);

-- 42. Danh sách bệnh nhân và số lần khám của họ
SELECT p.FullName, COUNT(m.RecordID) AS total_visits
FROM Patients p
LEFT JOIN MedicalRecords m ON p.PatientID = m.PatientID
GROUP BY p.PatientID;

-- 43. Danh sách bác sĩ và số lần khám của họ
SELECT e.FullName, COUNT(m.RecordID) AS total_exams
FROM Examiners e
LEFT JOIN MedicalRecords m ON e.ExaminerID = m.ExaminerID
GROUP BY e.ExaminerID;

-- 44. Danh sách bệnh nhân cùng với tên bác sĩ đã khám cho họ
SELECT p.FullName AS PatientName, e.FullName AS ExaminerName
FROM MedicalRecords m
JOIN Patients p ON m.PatientID = p.PatientID
JOIN Examiners e ON m.ExaminerID = e.ExaminerID;

-- 45. Danh sách bệnh nhân, ngày khám gần nhất
SELECT p.FullName, MAX(m.ExaminationDate) AS LastExamDate
FROM Patients p
JOIN MedicalRecords m ON p.PatientID = m.PatientID
GROUP BY p.PatientID;

-- 46. Danh sách bác sĩ, ngày khám gần nhất
SELECT e.FullName, MAX(m.ExaminationDate) AS LastExamDate
FROM Examiners e
JOIN MedicalRecords m ON e.ExaminerID = m.ExaminerID
GROUP BY e.ExaminerID;

-- 47. Danh sách bệnh nhân có chẩn đoán là 'Tiểu đường type 2'
SELECT DISTINCT p.FullName
FROM Patients p
JOIN MedicalRecords m ON p.PatientID = m.PatientID
WHERE m.Diagnosis = 'Tiểu đường type 2';

-- 48. Danh sách bác sĩ từng khám bệnh nhân có chẩn đoán 'Cao huyết áp'
SELECT DISTINCT e.FullName
FROM Examiners e
JOIN MedicalRecords m ON e.ExaminerID = m.ExaminerID
WHERE m.Diagnosis = 'Cao huyết áp';

-- 49. Danh sách bệnh nhân có nhiều hơn 1 chẩn đoán khác nhau
SELECT PatientID
FROM MedicalRecords
GROUP BY PatientID
HAVING COUNT(DISTINCT Diagnosis) > 1;

-- 50. Danh sách bác sĩ có nhiều hơn 2 chuyên khoa (giả sử có thể trùng tên)
SELECT Specialty, COUNT(*) AS num_doctors
FROM Examiners
GROUP BY Specialty
HAVING COUNT(*) > 2;

-- 51. Danh sách bệnh nhân có địa chỉ chứa 'Nguyễn'
SELECT * FROM Patients WHERE Address LIKE '%Nguyễn%';

-- 52. Danh sách bác sĩ có tên chứa 'Văn'
SELECT * FROM Examiners WHERE FullName LIKE '%Văn%';

-- 53. Danh sách bệnh nhân có số điện thoại là duy nhất
SELECT PhoneNumber, COUNT(*) FROM Patients GROUP BY PhoneNumber HAVING COUNT(*) = 1;

-- 54. Danh sách bác sĩ có email là duy nhất
SELECT Email, COUNT(*) FROM Examiners GROUP BY Email HAVING COUNT(*) = 1;

-- 55. Danh sách bệnh nhân có số lần khám nhiều nhất
SELECT PatientID, COUNT(*) AS total
FROM MedicalRecords
GROUP BY PatientID
ORDER BY total DESC
LIMIT 1;

-- 56. Danh sách bác sĩ có số lần khám nhiều nhất
SELECT ExaminerID, COUNT(*) AS total
FROM MedicalRecords
GROUP BY ExaminerID
ORDER BY total DESC
LIMIT 1;

-- 57. Danh sách bệnh nhân có số lần khám ít nhất (nhưng đã từng khám)
SELECT PatientID, COUNT(*) AS total
FROM MedicalRecords
GROUP BY PatientID
ORDER BY total ASC
LIMIT 1;

-- 58. Danh sách bác sĩ có số lần khám ít nhất (nhưng đã từng khám)
SELECT ExaminerID, COUNT(*) AS total
FROM MedicalRecords
GROUP BY ExaminerID
ORDER BY total ASC
LIMIT 1;

-- 59. Danh sách bệnh nhân có chẩn đoán là 'Viêm họng'
SELECT DISTINCT p.FullName
FROM Patients p
JOIN MedicalRecords m ON p.PatientID = m.PatientID
WHERE m.Diagnosis = 'Viêm họng';

-- 60. Danh sách bác sĩ từng khám cho bệnh nhân tên 'Nguyễn Văn An'
SELECT DISTINCT e.FullName
FROM Examiners e
JOIN MedicalRecords m ON e.ExaminerID = m.ExaminerID
JOIN Patients p ON m.PatientID = p.PatientID
WHERE p.FullName = 'Nguyễn Văn An';

-- 61. Danh sách bệnh nhân có ghi chú khám bệnh chứa 'MRI'
SELECT DISTINCT p.FullName
FROM Patients p
JOIN MedicalRecords m ON p.PatientID = m.PatientID
WHERE m.Notes LIKE '%MRI%';

-- 62. Danh sách bác sĩ có chuyên khoa bắt đầu bằng chữ 'N'
SELECT * FROM Examiners WHERE Specialty LIKE 'N%';

-- 63. Danh sách bệnh nhân có địa chỉ chứa 'Lê'
SELECT * FROM Patients WHERE Address LIKE '%Lê%';

-- 64. Danh sách bác sĩ có số điện thoại chứa '6789'
SELECT * FROM Examiners WHERE PhoneNumber LIKE '%6789%';

-- 65. Danh sách bệnh nhân có ngày sinh là ngày 15
SELECT * FROM Patients WHERE strftime('%d', DateOfBirth) = '15';

-- 66. Danh sách bác sĩ có email bắt đầu bằng 'cong'
SELECT * FROM Examiners WHERE Email LIKE 'cong%';

-- 67. Danh sách bệnh nhân có số điện thoại là NULL
SELECT * FROM Patients WHERE PhoneNumber IS NULL;

-- 68. Danh sách bác sĩ có email là NULL
SELECT * FROM Examiners WHERE Email IS NULL;

-- 69. Danh sách bệnh nhân có địa chỉ là NULL
SELECT * FROM Patients WHERE Address IS NULL;

-- 70. Danh sách bác sĩ có số điện thoại là NULL
SELECT * FROM Examiners WHERE PhoneNumber IS NULL;

-- 71. Danh sách bệnh nhân có số lần khám trong năm 2024
SELECT PatientID, COUNT(*) AS total_2024
FROM MedicalRecords
WHERE ExaminationDate BETWEEN '2024-01-01' AND '2024-12-31'
GROUP BY PatientID;

-- 72. Danh sách bác sĩ có số lần khám trong năm 2024
SELECT ExaminerID, COUNT(*) AS total_2024
FROM MedicalRecords
WHERE ExaminationDate BETWEEN '2024-01-01' AND '2024-12-31'
GROUP BY ExaminerID;

-- 73. Danh sách bệnh nhân có chẩn đoán là 'Sâu răng'
SELECT DISTINCT p.FullName
FROM Patients p
JOIN MedicalRecords m ON p.PatientID = m.PatientID
WHERE m.Diagnosis = 'Sâu răng';

-- 74. Danh sách bác sĩ từng khám cho bệnh nhân có chẩn đoán 'Suy thận mạn'
SELECT DISTINCT e.FullName
FROM Examiners e
JOIN MedicalRecords m ON e.ExaminerID = m.ExaminerID
WHERE m.Diagnosis = 'Suy thận mạn';

-- 75. Danh sách bệnh nhân có nhiều hơn 1 lần khám trong cùng 1 tháng
SELECT PatientID, strftime('%Y-%m', ExaminationDate) AS Month, COUNT(*) AS total
FROM MedicalRecords
GROUP BY PatientID, Month
HAVING total > 1;

-- 76. Danh sách bác sĩ có nhiều hơn 1 lần khám trong cùng 1 ngày
SELECT ExaminerID, ExaminationDate, COUNT(*) AS total
FROM MedicalRecords
GROUP BY ExaminerID, ExaminationDate
HAVING total > 1;

-- 77. Danh sách bệnh nhân có chẩn đoán là 'Cảm cúm'
SELECT DISTINCT p.FullName
FROM Patients p
JOIN MedicalRecords m ON p.PatientID = m.PatientID
WHERE m.Diagnosis = 'Cảm cúm';

-- 78. Danh sách bác sĩ từng khám cho bệnh nhân có chẩn đoán 'Viêm phế quản'
SELECT DISTINCT e.FullName
FROM Examiners e
JOIN MedicalRecords m ON e.ExaminerID = m.ExaminerID
WHERE m.Diagnosis = 'Viêm phế quản';

-- 79. Danh sách bệnh nhân có chẩn đoán là 'Đau đầu mạn tính'
SELECT DISTINCT p.FullName
FROM Patients p
JOIN MedicalRecords m ON p.PatientID = m.PatientID
WHERE m.Diagnosis = 'Đau đầu mạn tính';

-- 80. Danh sách bác sĩ từng khám cho bệnh nhân có chẩn đoán 'Viêm da dị ứng'
SELECT DISTINCT e.FullName
FROM Examiners e
JOIN MedicalRecords m ON e.ExaminerID = m.ExaminerID
WHERE m.Diagnosis = 'Viêm da dị ứng';

-- 81. Danh sách bệnh nhân có chẩn đoán là 'Gãy xương cẳng tay'
SELECT DISTINCT p.FullName
FROM Patients p
JOIN MedicalRecords m ON p.PatientID = m.PatientID
WHERE m.Diagnosis = 'Gãy xương cẳng tay';

-- 82. Danh sách bác sĩ từng khám cho bệnh nhân có chẩn đoán 'Thiếu máu'
SELECT DISTINCT e.FullName
FROM Examiners e
JOIN MedicalRecords m ON e.ExaminerID = m.ExaminerID
WHERE m.Diagnosis = 'Thiếu máu';

-- 83. Danh sách bệnh nhân có chẩn đoán là 'U nang buồng trứng'
SELECT DISTINCT p.FullName
FROM Patients p
JOIN MedicalRecords m ON p.PatientID = m.PatientID
WHERE m.Diagnosis = 'U nang buồng trứng';

-- 84. Danh sách bác sĩ từng khám cho bệnh nhân có chẩn đoán 'U lành tuyến giáp'
SELECT DISTINCT e.FullName
FROM Examiners e
JOIN MedicalRecords m ON e.ExaminerID = m.ExaminerID
WHERE m.Diagnosis = 'U lành tuyến giáp';

-- 85. Danh sách bệnh nhân có chẩn đoán là 'Rối loạn lo âu'
SELECT DISTINCT p.FullName
FROM Patients p
JOIN MedicalRecords m ON p.PatientID = m.PatientID
WHERE m.Diagnosis = 'Rối loạn lo âu';

-- 86. Danh sách bác sĩ từng khám cho bệnh nhân có chẩn đoán 'Cận thị'
SELECT DISTINCT e.FullName
FROM Examiners e
JOIN MedicalRecords m ON e.ExaminerID = m.ExaminerID
WHERE m.Diagnosis = 'Cận thị';

-- 87. Danh sách bệnh nhân có chẩn đoán là 'Viêm loét dạ dày'
SELECT DISTINCT p.FullName
FROM Patients p
JOIN MedicalRecords m ON p.PatientID = m.PatientID
WHERE m.Diagnosis = 'Viêm loét dạ dày';

-- 88. Danh sách bác sĩ từng khám cho bệnh nhân có chẩn đoán 'Đau khớp gối'
SELECT DISTINCT e.FullName
FROM Examiners e
JOIN MedicalRecords m ON e.ExaminerID = m.ExaminerID
WHERE m.Diagnosis = 'Đau khớp gối';

-- 89. Danh sách bệnh nhân có chẩn đoán là 'Thai kỳ 12 tuần'
SELECT DISTINCT p.FullName
FROM Patients p
JOIN MedicalRecords m ON p.PatientID = m.PatientID
WHERE m.Diagnosis = 'Thai kỳ 12 tuần';

-- 90. Danh sách bác sĩ từng khám cho bệnh nhân có chẩn đoán 'Thai kỳ 24 tuần'
SELECT DISTINCT e.FullName
FROM Examiners e
JOIN MedicalRecords m ON e.ExaminerID = m.ExaminerID
WHERE m.Diagnosis = 'Thai kỳ 24 tuần';

-- 91. Danh sách bệnh nhân có chẩn đoán là 'Suy thận mạn'
SELECT DISTINCT p.FullName
FROM Patients p
JOIN MedicalRecords m ON p.PatientID = m.PatientID
WHERE m.Diagnosis = 'Suy thận mạn';

-- 92. Danh sách bác sĩ từng khám cho bệnh nhân có chẩn đoán 'Tiểu đường type 1'
SELECT DISTINCT e.FullName
FROM Examiners e
JOIN MedicalRecords m ON e.ExaminerID = m.ExaminerID
WHERE m.Diagnosis = 'Tiểu đường type 1';

-- 93. Danh sách bệnh nhân có chẩn đoán là 'Gãy xương vai'
SELECT DISTINCT p.FullName
FROM Patients p
JOIN MedicalRecords m ON p.PatientID = m.PatientID
WHERE m.Diagnosis = 'Gãy xương vai';

-- 94. Danh sách bác sĩ từng khám cho bệnh nhân có chẩn đoán 'Viêm họng'
SELECT DISTINCT e.FullName
FROM Examiners e
JOIN MedicalRecords m ON e.ExaminerID = m.ExaminerID
WHERE m.Diagnosis = 'Viêm họng';

-- 95. Danh sách bệnh nhân có chẩn đoán là 'U lành tuyến giáp'
SELECT DISTINCT p.FullName
FROM Patients p
JOIN MedicalRecords m ON p.PatientID = m.PatientID
WHERE m.Diagnosis = 'U lành tuyến giáp';

-- 96. Danh sách bác sĩ từng khám cho bệnh nhân có chẩn đoán 'Cảm cúm'
SELECT DISTINCT e.FullName
FROM Examiners e
JOIN MedicalRecords m ON e.ExaminerID = m.ExaminerID
WHERE m.Diagnosis = 'Cảm cúm';

-- 97. Danh sách bệnh nhân có chẩn đoán là 'Viêm phế quản'
SELECT DISTINCT p.FullName
FROM Patients p
JOIN MedicalRecords m ON p.PatientID = m.PatientID
WHERE m.Diagnosis = 'Viêm phế quản';

-- 98. Danh sách bác sĩ từng khám cho bệnh nhân có chẩn đoán 'Gãy xương cẳng tay'
SELECT DISTINCT e.FullName
FROM Examiners e
JOIN MedicalRecords m ON e.ExaminerID = m.ExaminerID
WHERE m.Diagnosis = 'Gãy xương cẳng tay';

-- 99. Danh sách bệnh nhân có chẩn đoán là 'Thiếu máu'
SELECT DISTINCT p.FullName
FROM Patients p
JOIN MedicalRecords m ON p.PatientID = m.PatientID
WHERE m.Diagnosis = 'Thiếu máu';

-- 100. Danh sách bác sĩ từng khám cho bệnh nhân có chẩn đoán 'Thiếu máu'
SELECT DISTINCT e.FullName
FROM Examiners e
JOIN MedicalRecords m ON e.ExaminerID = m.ExaminerID
WHERE m.Diagnosis = 'Thiếu máu';