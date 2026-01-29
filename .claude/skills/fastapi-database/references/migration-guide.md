# Database Migrations with Alembic

Reference for managing schema changes in PostgreSQL production databases.

## Development vs Production

### Development: Direct Table Creation

For development/testing, use SQLModel's metadata:

```python
from sqlmodel import SQLModel

SQLModel.metadata.create_all(engine)
```

**Advantages:**
- Simple, quick
- No migration files to manage
- Good for prototyping

**Disadvantages:**
- No version history
- Can't roll back changes
- Not suitable for production
- Data loss possible

### Production: Alembic Migrations

For production PostgreSQL databases, use Alembic:

```bash
pip install alembic
```

**Advantages:**
- Full schema version history
- Can roll back/forward changes
- Safe data migration
- Tracks all changes
- Supports multiple database versions

## Alembic Setup

### Initialize

```bash
alembic init migrations
```

This creates:
```
migrations/
├── alembic.ini          # Configuration
├── env.py               # Migration environment
├── script.py.template   # Template for new migrations
└── versions/            # Migration scripts
```

### Configure Database URL

Edit `alembic.ini`:

```ini
sqlalchemy.url = postgresql://user:password@localhost/mydb
```

Or use environment variable:

```ini
sqlalchemy.url = driver://user:password@localhost/dbname?key=value
```

### Update env.py

```python
from sqlmodel import SQLModel
from myapp.models import *  # Import all models

target_metadata = SQLModel.metadata
```

## Creating Migrations

### Auto-Generate Migration

After modifying models, generate migration:

```bash
alembic revision --autogenerate -m "add user table"
```

Creates file: `migrations/versions/001_add_user_table.py`

### Manual Migration

For complex changes:

```bash
alembic revision -m "custom change"
```

Edit the generated file with custom SQL.

## Migration Files

### Structure

```python
from alembic import op
import sqlalchemy as sa

revision = 'abc123def456'
down_revision = 'xyz789uvw012'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Upgrade to this version (forward)"""
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

def downgrade() -> None:
    """Downgrade from this version (backward)"""
    op.drop_table('user')
```

### Common Operations

**Create table:**
```python
op.create_table(
    'user',
    sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
    sa.Column('email', sa.String(), nullable=False, unique=True),
)
```

**Add column:**
```python
op.add_column('user', sa.Column('full_name', sa.String()))
```

**Drop column:**
```python
op.drop_column('user', 'old_field')
```

**Create index:**
```python
op.create_index(op.f('ix_user_email'), 'user', ['email'])
```

**Add foreign key:**
```python
op.create_foreign_key('fk_post_user', 'post', 'user', ['user_id'], ['id'])
```

**Drop foreign key:**
```python
op.drop_constraint('fk_post_user', 'post', type_='foreignkey')
```

## Running Migrations

### Apply All Pending

```bash
alembic upgrade head
```

### Apply Specific Version

```bash
alembic upgrade abc123def456
```

### Apply N Versions Forward

```bash
alembic upgrade +2
```

### Downgrade All

```bash
alembic downgrade base
```

### Downgrade N Versions

```bash
alembic downgrade -2
```

### Current Version

```bash
alembic current
```

### History

```bash
alembic history
```

## FastAPI Integration

### Startup Migration

Run migrations on FastAPI startup:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from alembic.config import Config
from alembic import command

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run pending migrations
    alembic_config = Config("alembic.ini")
    command.upgrade(alembic_config, "head")
    yield
    # Shutdown

app = FastAPI(lifespan=lifespan)
```

## Zero-Downtime Migrations

For production systems with active users, avoid:
- `DROP TABLE` (use CREATE new table pattern)
- `ALTER TABLE table ADD COLUMN non_null_type` (locks table)
- Large index creation on busy tables

### Pattern: Add Column

**Instead of immediate NOT NULL:**

```python
# Step 1: Add nullable column
def upgrade() -> None:
    op.add_column('user', sa.Column('phone', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('user', 'phone')
```

**Later migration, after data is populated:**

```python
# Step 2: Set NOT NULL
def upgrade() -> None:
    op.alter_column('user', 'phone', nullable=False)

def downgrade() -> None:
    op.alter_column('user', 'phone', nullable=True)
```

### Pattern: Rename Column

```python
# Avoid rename which locks table
# Instead: new column + copy data + drop old

def upgrade() -> None:
    # Step 1: Add new column
    op.add_column('user', sa.Column('phone_new', sa.String()))
    # Step 2: Copy data
    op.execute('UPDATE "user" SET phone_new = phone')
    # Step 3: Drop old
    op.drop_column('user', 'phone')
    # Step 4: Rename new
    op.alter_column('user', 'phone_new', new_column_name='phone')
```

### Pattern: Add Index Concurrently

```python
# Avoid locking during index creation
def upgrade() -> None:
    op.create_index(
        'ix_user_email',
        'user',
        ['email'],
        postgresql_concurrently=True  # PostgreSQL specific
    )
```

## Best Practices

1. **One change per migration** - Easier to debug and rollback

2. **Test locally first** - Run migration on copy of production data

3. **Backup before production** - Always backup before applying

4. **Commit migrations to version control** - Track all changes

5. **Name migrations clearly** - `001_create_users_table`, not `rev_001`

6. **Document breaking changes** - Add comments for team awareness

7. **Use transaction support** - Alembic transactions wrap migrations by default

8. **Avoid schema changes in code** - Use migrations, not ORM metadata.create_all()

## Example Workflow

```bash
# 1. Modify models
# Edit myapp/models.py - add new field

# 2. Generate migration
alembic revision --autogenerate -m "add user.phone field"

# 3. Review generated migration
cat migrations/versions/xyz_add_user_phone_field.py

# 4. Test locally
alembic upgrade head
# Run tests

# 5. Commit to version control
git add migrations/versions/xyz_add_user_phone_field.py
git commit -m "migration: add user.phone field"

# 6. Deploy to production
# - Backup database
# - Run: alembic upgrade head
# - Verify data
```
