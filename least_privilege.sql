-- Eng kam huquq tamoyili (least privilege): ilova alohida, cheklangan foydalanuvchi bilan ulanadi.
-- Ilova faqat ma'lumotni o'qiy/yoza oladi; jadvalni o'chirish (DROP), o'zgartirish (ALTER)
-- va tozalash (TRUNCATE) huquqi berilmaydi. Sxema o'zgarishlari alohida "migratsiya" foydalanuvchisi bilan.

CREATE ROLE shop_app LOGIN PASSWORD 'ALMASHTIRING';

GRANT CONNECT ON DATABASE shop_db TO shop_app;
GRANT USAGE ON SCHEMA public TO shop_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO shop_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO shop_app;

-- Kelajakda yaratiladigan jadvallar uchun ham xuddi shunday (jadvallarni yaratuvchi rol nomi bilan):
-- ALTER DEFAULT PRIVILEGES FOR ROLE shop IN SCHEMA public
--     GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO shop_app;
-- ALTER DEFAULT PRIVILEGES FOR ROLE shop IN SCHEMA public
--     GRANT USAGE, SELECT ON SEQUENCES TO shop_app;
