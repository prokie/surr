# Surr

Surr is self hosted discord alternative. The name `Surr` comes from the swedish which means roghly means `buzz`. Audio and video is handled by livekit server. You can also share video using OBS over WHIP. 

The focus is to have lower latency than discord and allow for higher qualiy video sharing. You also self host it and own your own data.



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
