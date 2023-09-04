from playhouse.migrate import MySQLMigrator, migrate

from common.db.dbconfig import db


def add_field_if_not_exist(table_name, field_name, field_properties):
    # create a field in existing table if not exist
    # TODO use the following sql to check if multiple fields exists in one table
    #  SHOW COLUMNS FROM user WHERE Field IN ('avatar', 'available', 'available_balance');
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
