# Surr









### 🔄 **Database Migrations**
Track schema changes with Alembic:
```bash
# Generate migration
alembic revision --autogenerate -m "Add user table"

# Apply migrations
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```