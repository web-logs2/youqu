from common.db.dbconfig import db

from playhouse.migrate import MySQLMigrator, migrate


def add_field_if_not_exist(table_name, field_name, field_properties):
    # create a field in existing table if not exist
    query = "SHOW COLUMNS FROM user LIKE '{}'".format(field_name)
    result = db.execute_sql(query)
    is_field_exist = False
    for row in result:
        if row[0] == field_name:
            is_field_exist = True
            break
    if not is_field_exist:
        migrator = MySQLMigrator(db)
        migrate(
            migrator.add_column(table_name, field_name, field_properties),
        )
