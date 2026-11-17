# Topshiriq №7: Repository pattern, tranzaksiyalar va xavfsizlik

Python + SQLAlchemy 2.0 da generik Repository pattern, servis qatlamida tranzaksiya (rollback), Redis kesh, SQL Injection himoyasi va Argon2 bilan parol hash'lash.

## Nimalar bajarilgan

| Vazifa | Mazmuni | Qayerda |
|---|---|---|
| 1 | Generik `IRepository` (create, get_by_id, get_all, update, delete) va uning ORM implementatsiyasi | `app/repository/` |
| 2 | Servis qatlamida tranzaksiya: buyurtma yaratishda xatolik bo'lsa to'liq rollback, test bilan isbotlangan | `app/unit_of_work.py`, `app/services/order_service.py`, `tests/test_order_service.py` |
| 3 | Redis kesh, SQL Injection'ga zaif va xavfsiz kod, Argon2 parol hash'i | `app/cache.py`, `app/security/`, `app/services/auth_service.py` |
| Hisobot | Xavfsizlik bo'yicha qisqa hisobot | `docs/security_report.md` |

## Arxitektura

![Arxitektura](docs/architecture.png)

Servis qatlami faqat `IRepository` interfeysiga tayanadi. Tranzaksiyani `UnitOfWork` boshqaradi: repositorylar faqat `flush()` qiladi, `commit()` ni servis chaqiradi. Blok xatolik bilan tugasa, `UnitOfWork` avtomatik `ROLLBACK` qiladi.

## Loyiha tuzilmasi

```
app/
  repository/base.py            IRepository (interfeys)
  repository/sqlalchemy_repo.py ORM implementatsiyasi
  repository/memory_repo.py     xotiradagi implementatsiya (testlar uchun)
  repository/specific.py        UserRepository, ProductRepository, ...
  unit_of_work.py               tranzaksiya chegarasi
  services/                     OrderService, AccountService, AuthService, ProductService
  security/                     PasswordService (Argon2), SQL Injection namoyishi
  cache.py                      Redis kesh (cache-aside, TTL)
  postgres_demo.py              PostgreSQL: izolyatsiya darajalari va SQL Injection (DROP)
  demo_*.py                     namoyish dasturlari
tests/                          pytest testlari
docs/                           arxitektura va ER diagrammalar, xavfsizlik hisoboti, least_privilege.sql
```

## Ishga tushirish

```bash
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env

python -m app.demo_repository   # Vazifa 1
python -m app.demo_transaction  # Vazifa 2: rollback
python -m app.demo_cache        # Vazifa 3: Redis kesh
python -m app.demo_sqli         # Vazifa 3: SQL Injection va parol hash'lari
python -m pytest -q             # testlar
```

Hammasi birdaniga: `./run.sh` (Windows: `run.bat`).

Redis ishlamasa, `demo_cache` xotiradagi `fakeredis` ga o'tadi va bu haqda xabar beradi. Haqiqiy Redis uchun `.env` dagi `REDIS_URL` ni to'g'rilang.

### PostgreSQL bilan

`requirements.txt` ichida `psycopg2-binary` qatorini oching, `.env` da `DATABASE_URL` ni PostgreSQL ga o'zgartiring:

```
DATABASE_URL=postgresql+psycopg2://shop:parol@localhost:5432/shop_db
```

So'ng `python -m app.seed` (jadvallar va namunaviy ma'lumot) va `python -m app.postgres_demo` (izolyatsiya darajalari, SQL Injection).

Testlarni haqiqiy xizmatlar bilan ham o'tkazish mumkin (testlar ikkala muhitda takrorlanadi):

```bash
TEST_POSTGRES_URL=postgresql+psycopg2://shop:parol@localhost:5432/shop_db \
TEST_REDIS_URL=redis://localhost:6379/15 python -m pytest -q
```

## Testlar

Standart ishga tushirishda (SQLite + fakeredis) 94 ta test o'tadi, 9 tasi faqat PostgreSQL uchun bo'lgani sababli o'tkazib yuboriladi. PostgreSQL 16 va Redis 7 bilan: 206 ta test o'tadi.
