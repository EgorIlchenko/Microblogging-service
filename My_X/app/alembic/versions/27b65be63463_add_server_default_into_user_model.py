"""add server_default into User model

Revision ID: 01d30151319a
Revises: 44c62b263104
Create Date: 2024-12-20 13:19:27.939642

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "27b65be63463"
down_revision = "44c62b263104"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем значение по умолчанию на уровне базы данных для created_at
    op.alter_column(
        "users",  # Таблица, которую вы изменяете
        "created_at",  # Поле, для которого добавляется default
        server_default=sa.text("NOW()"),  # SQL-выражение для значения по умолчанию
        existing_type=sa.DateTime(),
    )


def downgrade() -> None:
    # Удаляем значение по умолчанию
    op.alter_column(
        "users",
        "created_at",
        server_default=None,
        existing_type=sa.DateTime(),
    )
