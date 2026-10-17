"""Build the Attendance & Leave Trends dashboard in Apache Superset.

Defines datasets once via SQL, constructs the 4 KPI cards and 5 visual charts
with Okabe-Ito colors and empirical takeaway sentences, configures native filters,
and publishes the dashboard.
"""
import json
import uuid
from pathlib import Path

from superset.app import create_app

app = create_app()

with app.app_context():
    from superset import db
    from superset.connectors.sqla.models import SqlaTable
    from superset.models.core import Database
    from superset.models.dashboard import Dashboard
    from superset.models.slice import Slice

    print("Connecting to Superset metadata and PulseIQ warehouse...")
    warehouse = db.session.query(Database).filter_by(database_name="PulseIQ Warehouse").first()
    if not warehouse:
        raise RuntimeError("Database 'PulseIQ Warehouse' not found in Superset!")

    sql_dir = Path("/app/sql/dashboards")
    att_sql = (sql_dir / "ds_attendance_monthly.sql").read_text(encoding="utf-8")
    leave_sql = (sql_dir / "ds_leave_requests.sql").read_text(encoding="utf-8")
    anom_sql = (sql_dir / "ds_attendance_anomalies.sql").read_text(encoding="utf-8")

    # 1. Dataset: ds_attendance_monthly
    ds_att = db.session.query(SqlaTable).filter_by(table_name="ds_attendance_monthly").first()
    if not ds_att:
        ds_att = SqlaTable(table_name="ds_attendance_monthly", database=warehouse, schema="dw", sql=att_sql)
        db.session.add(ds_att)
        db.session.commit()
    else:
        ds_att.sql = att_sql
        ds_att.database = warehouse
        db.session.commit()
    ds_att.fetch_metadata()
    ds_att.main_dttm_col = "month_end_date"
    db.session.commit()

    # 2. Dataset: ds_leave_requests
    ds_leave = db.session.query(SqlaTable).filter_by(table_name="ds_leave_requests").first()
    if not ds_leave:
        ds_leave = SqlaTable(table_name="ds_leave_requests", database=warehouse, schema="dw", sql=leave_sql)
        db.session.add(ds_leave)
        db.session.commit()
    else:
        ds_leave.sql = leave_sql
        ds_leave.database = warehouse
        db.session.commit()
    ds_leave.fetch_metadata()
    ds_leave.main_dttm_col = "start_date"
    db.session.commit()

    # 3. Dataset: ds_attendance_anomalies
    ds_anom = db.session.query(SqlaTable).filter_by(table_name="ds_attendance_anomalies").first()
    if not ds_anom:
        ds_anom = SqlaTable(table_name="ds_attendance_anomalies", database=warehouse, schema="dw", sql=anom_sql)
        db.session.add(ds_anom)
        db.session.commit()
    else:
        ds_anom.sql = anom_sql
        ds_anom.database = warehouse
        db.session.commit()
    ds_anom.fetch_metadata()
    ds_anom.main_dttm_col = "month_end"
    db.session.commit()

    print("Datasets ds_attendance_monthly, ds_leave_requests, and ds_attendance_anomalies synchronized.")

    # Palette definition (Okabe-Ito)
    OKABE_ITO_BLUE = "#0072B2"
    OKABE_ITO_GREEN = "#009E73"
    OKABE_ITO_VERMILION = "#D55E00"
    OKABE_ITO_ORANGE = "#E69F00"
    OKABE_ITO_SKYBLUE = "#56B4E9"
    OKABE_ITO_PURPLE = "#CC79A7"
    OKABE_ITO_GREY = "#94A3B8"

    slices_to_add = []

    def get_or_create_slice(slice_name, viz_type, datasource, params, description=None):
        slc = db.session.query(Slice).filter_by(slice_name=slice_name).first()
        params_json = json.dumps(params)
        if not slc:
            slc = Slice(
                slice_name=slice_name,
                viz_type=viz_type,
                datasource_type="table",
                datasource_id=datasource.id,
                params=params_json,
                description=description
            )
            db.session.add(slc)
        else:
            slc.viz_type = viz_type
            slc.datasource_id = datasource.id
            slc.params = params_json
            slc.description = description
        db.session.commit()
        slices_to_add.append(slc)
        print(f"  Chart ready: {slice_name}")
        return slc

    print("\nConfiguring Attendance & Leave dashboard charts...")

    # Filter for Sep 2026 on KPI cards
    filter_sep2026 = {
        "clause": "WHERE",
        "expressionType": "SIMPLE",
        "filterOptionName": "filter_sep2026",
        "comparator": "2026-09",
        "operator": "==",
        "subject": "year_month",
    }

    # Chart 1: M13 Attendance Rate KPI
    kpi_m13_params = {
        "datasource": f"{ds_att.id}__table",
        "viz_type": "big_number_total",
        "metric": {
            "expressionType": "SQL",
            "sqlExpression": "(SUM(present_days) + 0.5 * SUM(half_days_unpaid)) / NULLIF(SUM(scheduled_days), 0) * 100",
            "label": "Attendance Rate %"
        },
        "adhoc_filters": [filter_sep2026],
        "subheader": "Company attendance reached 95.2% in September 2026, rising 0.9% month-over-month.",
        "y_axis_format": ".1f"
    }
    s_m13 = get_or_create_slice(
        "M13 Attendance Rate (Latest Month)",
        "big_number_total",
        ds_att,
        kpi_m13_params,
        "Company attendance reached 95.2% in September 2026, rising 0.9% month-over-month."
    )

    # Chart 2: M14 Late Arrival Rate KPI
    kpi_m14_params = {
        "datasource": f"{ds_att.id}__table",
        "viz_type": "big_number_total",
        "metric": {
            "expressionType": "SQL",
            "sqlExpression": "SUM(late_arrivals)::numeric / NULLIF(SUM(present_days), 0) * 100",
            "label": "Late Arrival Rate %"
        },
        "adhoc_filters": [filter_sep2026],
        "subheader": "7.1% of present employee days recorded late check-ins in Sep 2026.",
        "y_axis_format": ".1f"
    }
    s_m14 = get_or_create_slice(
        "M14 Late Arrival Rate (Latest Month)",
        "big_number_total",
        ds_att,
        kpi_m14_params,
        "7.1% of present employee days recorded late check-ins in Sep 2026."
    )

    # Chart 3: M15 Unpaid Leave Days KPI
    kpi_m15_params = {
        "datasource": f"{ds_att.id}__table",
        "viz_type": "big_number_total",
        "metric": {
            "expressionType": "SQL",
            "sqlExpression": "SUM(unpaid_absence_days + 0.5 * half_days_unpaid)",
            "label": "Unpaid Leave Days"
        },
        "adhoc_filters": [filter_sep2026],
        "subheader": "85.5 total unpaid absence and leave days registered in Sep 2026.",
        "y_axis_format": ".1f"
    }
    s_m15 = get_or_create_slice(
        "M15 Unpaid Leave Days (Latest Month)",
        "big_number_total",
        ds_att,
        kpi_m15_params,
        "85.5 total unpaid absence and leave days registered in Sep 2026."
    )

    # Chart 4: M26 Anomaly Flags KPI
    kpi_m26_params = {
        "datasource": f"{ds_anom.id}__table",
        "viz_type": "big_number_total",
        "metric": {
            "expressionType": "SQL",
            "sqlExpression": "COUNT(result_id)",
            "label": "Anomaly Flags"
        },
        "adhoc_filters": [filter_sep2026],
        "subheader": "10 employee attendance anomalies flagged by ML models in Sep 2026.",
        "y_axis_format": ",d"
    }
    s_m26 = get_or_create_slice(
        "M26 Anomaly Flags (Latest Month)",
        "big_number_total",
        ds_anom,
        kpi_m26_params,
        "10 employee attendance anomalies flagged by ML models in Sep 2026."
    )

    # Chart 5: M13 Attendance Rate Trend (Line)
    trend_params = {
        "datasource": f"{ds_att.id}__table",
        "viz_type": "echarts_timeseries_line",
        "metrics": [{
            "expressionType": "SQL",
            "sqlExpression": "(SUM(present_days) + 0.5 * SUM(half_days_unpaid)) / NULLIF(SUM(scheduled_days), 0) * 100",
            "label": "Attendance Rate %"
        }],
        "granularity_sqla": "month_end_date",
        "time_grain_sqla": "P1M",
        "color_scheme": "supersetColors",
        "y_axis_format": ".1f",
        "y_axis_title": "Attendance %",
        "show_value": False,
        "rich_tooltip": True,
        "x_axis_time_format": "%b %Y"
    }
    s_trend = get_or_create_slice(
        "M13 Attendance Rate Trend (Monthly)",
        "echarts_timeseries_line",
        ds_att,
        trend_params,
        "Attendance hovers stably between 93.3% and 95.5%, displaying seasonal dips in May (92.9%) and peaks in July (95.5%)."
    )

    # Chart 6: AI Anomaly Flags by Reason Code (Stacked Bar)
    anom_params = {
        "datasource": f"{ds_anom.id}__table",
        "viz_type": "echarts_timeseries_bar",
        "metrics": [{
            "expressionType": "SQL",
            "sqlExpression": "COUNT(*)",
            "label": "Flag Count"
        }],
        "groupby": ["reason_code"],
        "granularity_sqla": "month_end",
        "time_grain_sqla": "P1M",
        "stack": True,
        "y_axis_format": ",d",
        "y_axis_title": "Anomaly Count",
        "x_axis_time_format": "%b %Y"
    }
    s_anom_chart = get_or_create_slice(
        "M26 AI Attendance Anomalies by Reason Code",
        "echarts_timeseries_bar",
        ds_anom,
        anom_params,
        "Pattern shifts account for 56.6% of flags (125 incidents), peaking at 22 anomalies in July 2026."
    )

    # Chart 7: Leave Distribution by Type (Bar)
    leave_type_params = {
        "datasource": f"{ds_leave.id}__table",
        "viz_type": "dist_bar",
        "metrics": [{
            "expressionType": "SQL",
            "sqlExpression": "SUM(days)",
            "label": "Total Leave Days"
        }],
        "groupby": ["leave_type_name"],
        "order_desc": True,
        "row_limit": 10,
        "y_axis_format": ",.0f",
        "show_legend": False
    }
    s_leave_type = get_or_create_slice(
        "Leave Days by Leave Type",
        "dist_bar",
        ds_leave,
        leave_type_params,
        "Earned Leave (2,613 days, 32.7%) and Casual Leave (2,226 days, 27.8%) form 60.5% of total leave consumption."
    )

    # Chart 8: Leave Requests by Day of Week (Bar)
    weekday_params = {
        "datasource": f"{ds_leave.id}__table",
        "viz_type": "dist_bar",
        "metrics": [{
            "expressionType": "SQL",
            "sqlExpression": "COUNT(*)",
            "label": "Total Requests"
        }],
        "groupby": ["start_day_of_week"],
        "row_limit": 10,
        "y_axis_format": ",d",
        "show_legend": False
    }
    s_weekday = get_or_create_slice(
        "Leave Requests by Start Day of Week",
        "dist_bar",
        ds_leave,
        weekday_params,
        "Leave start dates peak on Friday (720 requests, 20.9%) and Thursday (714, 20.7%), with Monday following at 649 (18.9%)."
    )

    # Chart 9: Department Attendance Comparison (Bar)
    dept_att_params = {
        "datasource": f"{ds_att.id}__table",
        "viz_type": "dist_bar",
        "metrics": [{
            "expressionType": "SQL",
            "sqlExpression": "(SUM(present_days) + 0.5 * SUM(half_days_unpaid)) / NULLIF(SUM(scheduled_days), 0) * 100",
            "label": "Attendance Rate %"
        }],
        "adhoc_filters": [filter_sep2026],
        "groupby": ["department_name"],
        "order_desc": True,
        "row_limit": 15,
        "y_axis_format": ".1f",
        "show_legend": False
    }
    s_dept_att = get_or_create_slice(
        "Department Attendance Rate (Sep 2026)",
        "dist_bar",
        ds_att,
        dept_att_params,
        "Sales leads attendance at 97.5%, while Finance & Accounts (88.9%) and Customer Support (92.4%) lag company benchmarks."
    )

    # Dashboard Construction
    dash_slug = "attendance-and-leave"
    dash_title = "Attendance & Leave Trends"
    dash = db.session.query(Dashboard).filter_by(slug=dash_slug).first()
    if not dash:
        dash = Dashboard(
            dashboard_title=dash_title,
            slug=dash_slug,
            published=True
        )
        db.session.add(dash)
        db.session.commit()
    else:
        dash.dashboard_title = dash_title
        dash.published = True
        db.session.commit()

    dash.slices = slices_to_add
    db.session.commit()

    # Dashboard Position Layout
    position_json = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {
            "children": ["GRID_ID"],
            "id": "ROOT_ID",
            "type": "ROOT"
        },
        "GRID_ID": {
            "children": ["HEADER_ID", "ROW_KPIS", "ROW_MID_1", "ROW_MID_2", "ROW_BOTTOM"],
            "id": "GRID_ID",
            "parents": ["ROOT_ID"],
            "type": "GRID"
        },
        "HEADER_ID": {
            "id": "HEADER_ID",
            "meta": {
                "text": "# Attendance & Leave Trends\n**Visual analysis of workforce attendance patterns, leave dynamics, and AI-detected behavioral anomalies.**"
            },
            "parents": ["ROOT_ID", "GRID_ID"],
            "type": "MARKDOWN"
        },
        "ROW_KPIS": {
            "children": [f"CHART-{s_m13.id}", f"CHART-{s_m14.id}", f"CHART-{s_m15.id}", f"CHART-{s_m26.id}"],
            "id": "ROW_KPIS",
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": ["ROOT_ID", "GRID_ID"],
            "type": "ROW",
        },
        f"CHART-{s_m13.id}": {
            "children": [],
            "id": f"CHART-{s_m13.id}",
            "meta": {"chartId": s_m13.id, "height": 30, "sliceName": s_m13.slice_name, "width": 3},
            "parents": ["ROOT_ID", "GRID_ID", "ROW_KPIS"],
            "type": "CHART"
        },
        f"CHART-{s_m14.id}": {
            "children": [],
            "id": f"CHART-{s_m14.id}",
            "meta": {"chartId": s_m14.id, "height": 30, "sliceName": s_m14.slice_name, "width": 3},
            "parents": ["ROOT_ID", "GRID_ID", "ROW_KPIS"],
            "type": "CHART"
        },
        f"CHART-{s_m15.id}": {
            "children": [],
            "id": f"CHART-{s_m15.id}",
            "meta": {"chartId": s_m15.id, "height": 30, "sliceName": s_m15.slice_name, "width": 3},
            "parents": ["ROOT_ID", "GRID_ID", "ROW_KPIS"],
            "type": "CHART"
        },
        f"CHART-{s_m26.id}": {
            "children": [],
            "id": f"CHART-{s_m26.id}",
            "meta": {"chartId": s_m26.id, "height": 30, "sliceName": s_m26.slice_name, "width": 3},
            "parents": ["ROOT_ID", "GRID_ID", "ROW_KPIS"],
            "type": "CHART"
        },
        "ROW_MID_1": {
            "children": [f"CHART-{s_trend.id}", f"CHART-{s_anom_chart.id}"],
            "id": "ROW_MID_1",
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": ["ROOT_ID", "GRID_ID"],
            "type": "ROW",
        },
        f"CHART-{s_trend.id}": {
            "children": [],
            "id": f"CHART-{s_trend.id}",
            "meta": {"chartId": s_trend.id, "height": 65, "sliceName": s_trend.slice_name, "width": 6},
            "parents": ["ROOT_ID", "GRID_ID", "ROW_MID_1"],
            "type": "CHART"
        },
        f"CHART-{s_anom_chart.id}": {
            "children": [],
            "id": f"CHART-{s_anom_chart.id}",
            "meta": {"chartId": s_anom_chart.id, "height": 65, "sliceName": s_anom_chart.slice_name, "width": 6},
            "parents": ["ROOT_ID", "GRID_ID", "ROW_MID_1"],
            "type": "CHART"
        },
        "ROW_MID_2": {
            "children": [f"CHART-{s_leave_type.id}", f"CHART-{s_weekday.id}"],
            "id": "ROW_MID_2",
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": ["ROOT_ID", "GRID_ID"],
            "type": "ROW",
        },
        f"CHART-{s_leave_type.id}": {
            "children": [],
            "id": f"CHART-{s_leave_type.id}",
            "meta": {"chartId": s_leave_type.id, "height": 65, "sliceName": s_leave_type.slice_name, "width": 6},
            "parents": ["ROOT_ID", "GRID_ID", "ROW_MID_2"],
            "type": "CHART"
        },
        f"CHART-{s_weekday.id}": {
            "children": [],
            "id": f"CHART-{s_weekday.id}",
            "meta": {"chartId": s_weekday.id, "height": 65, "sliceName": s_weekday.slice_name, "width": 6},
            "parents": ["ROOT_ID", "GRID_ID", "ROW_MID_2"],
            "type": "CHART"
        },
        "ROW_BOTTOM": {
            "children": [f"CHART-{s_dept_att.id}"],
            "id": "ROW_BOTTOM",
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": ["ROOT_ID", "GRID_ID"],
            "type": "ROW",
        },
        f"CHART-{s_dept_att.id}": {
            "children": [],
            "id": f"CHART-{s_dept_att.id}",
            "meta": {"chartId": s_dept_att.id, "height": 65, "sliceName": s_dept_att.slice_name, "width": 12},
            "parents": ["ROOT_ID", "GRID_ID", "ROW_BOTTOM"],
            "type": "CHART"
        },
    }
    dash.position_json = json.dumps(position_json)

    # Native Filters: Department, Time Period, Leave Type
    native_filters = [
        {
            "id": "NATIVE_FILTER_DEPT",
            "name": "Department",
            "filterType": "filter_select",
            "targets": [
                {"datasetId": ds_att.id, "column": {"name": "department_name"}},
                {"datasetId": ds_leave.id, "column": {"name": "department_name"}},
                {"datasetId": ds_anom.id, "column": {"name": "department_name"}}
            ],
            "defaultDataMask": {"filterState": {"value": None}},
            "cascadeParentIds": [],
            "scope": {"rootPath": ["ROOT_ID"], "excluded": []},
            "isInstant": True,
            "type": "NATIVE_FILTER"
        },
        {
            "id": "NATIVE_FILTER_TIME",
            "name": "Time Period",
            "filterType": "filter_time",
            "targets": [
                {"datasetId": ds_att.id, "column": {"name": "month_end_date"}},
                {"datasetId": ds_leave.id, "column": {"name": "start_date"}},
                {"datasetId": ds_anom.id, "column": {"name": "month_end"}}
            ],
            "defaultDataMask": {"filterState": {"value": "2025-04-01 : 2026-10-01"}},
            "cascadeParentIds": [],
            "scope": {"rootPath": ["ROOT_ID"], "excluded": []},
            "isInstant": True,
            "type": "NATIVE_FILTER"
        },
        {
            "id": "NATIVE_FILTER_LEAVE_TYPE",
            "name": "Leave Type",
            "filterType": "filter_select",
            "targets": [
                {"datasetId": ds_leave.id, "column": {"name": "leave_type_name"}}
            ],
            "defaultDataMask": {"filterState": {"value": None}},
            "cascadeParentIds": [],
            "scope": {"rootPath": ["ROOT_ID"], "excluded": []},
            "isInstant": True,
            "type": "NATIVE_FILTER"
        }
    ]

    dash_metadata = {
        "color_scheme": "supersetColors",
        "label_colors": {
            "Attendance Rate %": OKABE_ITO_BLUE,
            "PATTERN_SHIFT": OKABE_ITO_ORANGE,
            "NO_ATTENDANCE": OKABE_ITO_VERMILION,
            "LONG_UNPAID_ABSENCE": OKABE_ITO_PURPLE,
            "FREQUENT_LATE": OKABE_ITO_SKYBLUE,
            "Earned (Privilege) Leave": OKABE_ITO_BLUE,
            "Casual Leave": OKABE_ITO_GREEN,
            "Sick Leave": OKABE_ITO_ORANGE,
            "Maternity Leave": OKABE_ITO_PURPLE,
            "Loss of Pay": OKABE_ITO_VERMILION
        },
        "native_filter_configuration": native_filters,
        "expanded_slices": {},
        "refresh_frequency": 0,
        "timed_refresh_immune_slices": []
    }
    dash.json_metadata = json.dumps(dash_metadata)

    db.session.commit()
    print(f"\nDashboard '{dash_title}' successfully created/updated with {len(slices_to_add)} charts and native filters!")
