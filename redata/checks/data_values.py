from redata.checks.data_schema import check_for_new_tables
from redata.db_operations import metrics_db, metrics_session
from redata.models.metrics import MetricsDataValues


def check_generic(func_name, db, table, checked_column, time_interval, conf):
    result = db.check_generic(func_name, table, checked_column, time_interval, conf)

    metric = MetricsDataValues(
        table_id=table.id,
        column_name=checked_column,
        check_name=f'check_{func_name}',
        check_value=result.value,
        time_interval=time_interval,
        created_at=conf.for_time
    )

    metrics_session.add(metric)
    metrics_session.commit()

    
def check_avg(db, table, checked_column, time_interval, conf):
    check_generic(
        'avg', db, table, checked_column, time_interval, conf
    )

def check_min(db, table, checked_column, time_interval, conf):
    check_generic(
        'min', db, table, checked_column, time_interval, conf
    )

def check_max(db, table, checked_column, time_interval, conf):
    check_generic(
        'max', db, table, checked_column, time_interval, conf
    )

def check_count_nulls(db, table, checked_column, time_interval, conf):
    
    result = db.check_count_nulls(table, checked_column, time_interval, conf)

    metric = MetricsDataValues(
        table_id=table.id,
        column_name=checked_column,
        check_name='check_count_nulls',
        check_value=result.value,
        time_interval=time_interval,
        created_at=conf.for_time
    )

    metrics_session.add(metric)
    metrics_session.commit()


def check_count_per_value(db, table, checked_column, time_interval, conf):
    result = db.check_count_per_value(table, checked_column, time_interval, conf)

    for row in (result or []):

        metric = MetricsDataValues(
            table_id=table.id,
            column_name=checked_column,
            column_value=row.value,
            check_name='check_count_per_value',
            check_value=row.count,
            time_interval=time_interval,
            created_at=conf.for_time
        )

        metrics_session.add(metric)
    metrics_session.commit()