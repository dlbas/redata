import json
from sqlalchemy.sql import text
from redata.db_operations import metrics_session
from sqlalchemy import update
from redata.models.table import MonitoredTable
from redata.models.metrics import MetricsSchemaChanges


def insert_schema_changed_record(table, operation, column_name, column_type, column_count, conf):
    metric = MetricsSchemaChanges(
        table_id=table.id,
        operation=operation,
        column_name=column_name,
        column_type=column_type,
        column_count=column_count,
        created_at=conf.for_time
    )
    metrics_session.add(metric)
    metrics_session.commit()


def check_for_new_tables(db, conf):
    
    for namespace in db.namespaces:
        tables = db.table_names(namespace)
        
        monitored_tables = MonitoredTable.get_monitored_tables_per_namespace(db.name, namespace)
        monitored_tables_names = set([table.table_name for table in monitored_tables])

        for table_name in tables:
            if table_name not in monitored_tables_names:
                table = MonitoredTable.setup_for_source_table(db, table_name, namespace)
                if table:
                    insert_schema_changed_record(
                        table, 'table created', None, None, None, conf
                    )


def check_if_schema_changed(db, table, conf):

    def schema_to_dict(schema):
        return dict([(el['name'], el['type'])for el in schema])

    def sorted_to_compare(schema):
        return sorted(schema, key=lambda x: sorted(x.items()))

    last_schema = table.schema['columns']
    table_name = table.table_name

    current_schema = db.get_table_schema(table.table_name, table.namespace)

    if sorted_to_compare(last_schema) != sorted_to_compare(current_schema):
        last_dict = schema_to_dict(last_schema)
        current_dict = schema_to_dict(current_schema)

        for el in last_dict:
            if el not in current_dict:
                print (f"{el} was removed from schema")
                insert_schema_changed_record(table, 'column removed', el, last_dict[el], len(current_dict), conf)

        for el in current_dict:
            if el not in last_dict:
                print (f"{el} was added to schema")
                insert_schema_changed_record(table, 'column added', el, current_dict[el], len(current_dict), conf)
            else:
                prev_type = last_dict[el]
                curr_type = current_dict[el]

                if curr_type != prev_type:
                    print (f"Type of column: {el} changed from {prev_type} to {curr_type}")
                    insert_schema_changed_record(table, 'column changed', el, current_dict[el], len(current_dict), conf)
        
        table.schema = {'columns': current_schema}
        metrics_session.commit()
