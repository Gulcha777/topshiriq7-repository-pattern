# Xavfsizlik bo'yicha qisqa hisobot

## 1. SQL Injection

| | Zaif variant | Xavfsiz variant |
|---|---|---|
| Kod | `app/security/sqli_demo.py: insecure_find_users` | `secure_find_users`, `UserRepository.find_by_username` |
| Usul | foydalanuvchi matni SQL satriga qo'shiladi | qiymat alohida parametr (`:name`) yoki ORM orqali yuboriladi |
| `' OR '1'='1` | hamma foydalanuvchi qaytadi | bo'sh natija |
| `' UNION SELECT id, password_hash FROM users --` | parol hash'lari o'g'irlanadi | bo'sh natija |
| `x'; DROP TABLE ...; --` | PostgreSQL'da jadval o'chadi | hech narsa o'zgarmaydi |

Zaif joy: so'rov matni `"... WHERE username = '" + name + "'"` ko'rinishida qurilgan, shuning uchun kiritilgan qo'shtirnoq so'rov tuzilishini o'zgartiradi.

Tuzatish: qiymatlar so'rovdan alohida yuboriladi, baza ularni hech qachon SQL kodi sifatida talqin qilmaydi. Qo'shimcha qatlamlar:
- kiritishni tekshirish: login faqat `[A-Za-z0-9_.-]{3,50}` (`AuthService.register`);
- eng kam huquq: ilova `shop_app` roli bilan ulanadi, `DROP`/`ALTER`/`TRUNCATE` huquqi yo'q (`docs/least_privilege.sql`);
- xatolik matnlarida SQL yoki baza tuzilishi foydalanuvchiga ko'rsatilmaydi (domen xatoliklari alohida).

Tekshiruv: `tests/test_sqli.py`, `tests/test_auth_service.py`, `python -m app.demo_sqli`, `python -m app.postgres_demo`.

## 2. Parollarni saqlash

- Parol ochiq holda saqlanmaydi: **Argon2id** hash (`argon2-cffi`), parametrlar: xotira 64 MB, 3 iteratsiya, 4 oqim.
- Har bir hash uchun tasodifiy tuz (salt): bir xil parol turli hash beradi (test bilan tasdiqlangan).
- Parametrlar eskirsa, foydalanuvchi kirganda hash avtomatik yangilanadi (`needs_rehash`).
- Foydalanuvchi topilmaganda ham soxta hash tekshiriladi: javob vaqti bo'yicha login mavjudligini bilib bo'lmaydi.
- Parol siyosati: kamida 8 ta belgi.
- Eng yomon holat: SQL Injection orqali bazadan hash o'g'irlansa ham, ochiq parol chiqmaydi (UNION namoyishida faqat `$argon2id$...` ko'rinadi).

## 3. Tranzaksiyalar va ma'lumot butunligi

- Buyurtma, qoldiq va to'lov bitta tranzaksiyada: istalgan xatolikda to'liq `ROLLBACK` (`tests/test_order_service.py`).
- `SELECT ... FOR UPDATE` bilan qator qulflanadi: parallel buyurtmalarda qoldiq manfiy bo'lmaydi.
- Bazadagi `CHECK` cheklovlari (`stock >= 0`, `balance >= 0`, `quantity > 0`) ikkinchi himoya qatlami.
- Bank o'tkazmasida hisoblar bir xil tartibda qulflanadi (deadlock xavfini kamaytirish).

## 4. Redis (kesh)

- Keshga faqat ommaviy mahsulot ma'lumoti yoziladi; parol, hash va shaxsiy ma'lumot keshlanmaydi.
- Har bir yozuvga TTL beriladi; ma'lumot o'zgarganda (bazaga muvaffaqiyatli commit'dan keyin) kesh bekor qilinadi.
- Ulanish manzili `.env` dan olinadi. Production uchun tavsiya: Redis'ga parol (`requirepass`/ACL), TLS va faqat ichki tarmoqdan kirish.

## 5. Sirlar va konfiguratsiya

- `.env` fayli `.gitignore` da, repozitoriyda faqat namuna `.env.example` bor.
- Connection string yozilganda parol chiqishda yashiriladi.

## 6. Qolgan xavflar va tavsiyalar

- Kirishga urinishlar sonini cheklash (rate limiting) va vaqtinchalik bloklash qo'shilmagan.
- Production'da faqat HTTPS orqali ishlash, audit jurnali va sirlarni maxsus saqlash (vault) tavsiya etiladi.
- Redis ulanishida autentifikatsiya va TLS production'da yoqilishi kerak.
