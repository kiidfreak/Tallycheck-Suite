import logging
from logging.config import fileConfig

from flask import current_app
from sqlalchemy import text

from alembic import context

# This project is multi-tenant by SCHEMA: every organization gets its own
# Postgres schema (tenant_<org_id>), and all models except Organization are
# unqualified so they resolve through the connection's search_path.
#
# Stock Flask-Migrate runs migrations exactly once against the default schema,
# which would leave every tenant schema untouched. So `flask db upgrade` here
# runs one pass per schema:
#
#   1. public  — only the Organization table lives there
#   2. each tenant schema, in turn
#
# Each schema carries its OWN alembic_version table (version_table_schema), so
# tenants provisioned at different times can sit at different revisions and
# still upgrade correctly.
#
# Tenant schemas created by seed_org.py via db.metadata.create_all() have no
# alembic_version row at all — they must be baselined before their first
# upgrade, or Alembic will try to replay the entire history against tables that
# already exist. Use `flask stamp-tenants` for that.

PUBLIC_SCHEMA = 'public'

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')


def get_engine():
    try:
        return current_app.extensions['migrate'].db.get_engine()
    except (TypeError, AttributeError):
        return current_app.extensions['migrate'].db.engine


def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace(
            '%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')

config.set_main_option('sqlalchemy.url', get_engine_url())
target_db = current_app.extensions['migrate'].db

def get_metadata():
    if hasattr(target_db, 'metadatas'):
        return target_db.metadatas[None]
    return target_db.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=get_metadata(), literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def tenant_schemas(connection):
    """Every tenant schema name, read from public.organizations.

    Deliberately NOT filtered by is_active: a deactivated tenant that misses a
    migration silently drifts and then breaks when it is reactivated.
    """
    exists = connection.execute(text(
        "SELECT to_regclass('public.organizations')"
    )).scalar()
    if not exists:
        # Fresh database — the organizations table itself has not been created
        # yet, so there are no tenants to migrate on this pass.
        return []

    rows = connection.execute(text(
        "SELECT schema_name FROM public.organizations ORDER BY schema_name"
    )).fetchall()

    present = set(connection.execute(text(
        "SELECT nspname FROM pg_namespace"
    )).scalars().all())

    schemas = []
    for (name,) in rows:
        if name in present:
            schemas.append(name)
        else:
            # Registered in public.organizations but never actually provisioned.
            logger.warning("skipping tenant %r: schema does not exist", name)
    return schemas


def make_include_object(schema_name):
    """Keep each pass to the objects that belong in that schema.

    Only Organization declares an explicit schema ('public'); every other model
    is unqualified and belongs to whichever tenant schema is being migrated.
    Without this, autogenerate against a tenant would see 'organizations' as
    missing and try to drop or recreate it.
    """
    def include_object(object, name, type_, reflected, compare_to):
        if type_ == 'table':
            table_schema = getattr(object, 'schema', None)
            if schema_name == PUBLIC_SCHEMA:
                return table_schema == PUBLIC_SCHEMA
            return table_schema is None
        return True
    return include_object


def run_migrations_for_schema(connection, schema_name, conf_args):
    """Run the full migration chain against one schema."""
    logger.info("running migrations for schema: %s", schema_name)

    connection.execute(text(f'SET search_path TO "{schema_name}", public'))

    args = dict(conf_args)
    args.pop('include_object', None)

    context.configure(
        connection=connection,
        target_metadata=get_metadata(),
        version_table_schema=schema_name,
        include_schemas=False,
        include_object=make_include_object(schema_name),
        **args
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode, once per schema.

    One pass for public (Organization), then one per tenant schema.
    """

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    conf_args = current_app.extensions['migrate'].configure_args
    if conf_args.get("process_revision_directives") is None:
        conf_args["process_revision_directives"] = process_revision_directives

    connectable = get_engine()

    with connectable.connect() as connection:
        # Autogenerate compares against a single schema and writes one revision
        # file; running it per tenant would emit duplicates. Generate against
        # public only, then let `flask db upgrade` fan the result out.
        if getattr(config.cmd_opts, 'autogenerate', False):
            run_migrations_for_schema(connection, PUBLIC_SCHEMA, conf_args)
            connection.commit()
            return

        schemas = [PUBLIC_SCHEMA] + tenant_schemas(connection)
        logger.info("migrating %d schema(s): %s", len(schemas), ", ".join(schemas))

        for schema_name in schemas:
            run_migrations_for_schema(connection, schema_name, conf_args)

        # Leave the connection on a predictable search_path.
        connection.execute(text(f'SET search_path TO "{PUBLIC_SCHEMA}"'))
        connection.commit()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
