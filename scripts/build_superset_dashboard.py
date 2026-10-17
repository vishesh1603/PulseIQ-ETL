"""Build the Headcount & Departments dashboard in Apache Superset.

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
    from superset.connectors.sqla.models import SqlaTable, SqlMetric
    from superset.models.core import Database
    from superset.models.dashboard import Dashboard
    from superset.models.slice import Slice

    print("Connecting to Superset metadata and PulseIQ warehouse...")
    warehouse = db.session.query(Database).filter_by(database_name="PulseIQ Warehouse").first()
    if not warehouse:
        raise RuntimeError("Database 'PulseIQ Warehouse' not found in Superset!")

    sql_dir = Path("/app/sql/dashboards")
    hc_sql = (sql_dir / "ds_headcount_monthly.sql").read_text(encoding="utf-8")
    demo_sql = (sql_dir / "ds_employee_demographics.sql").read_text(encoding="utf-8")

    # 1. Dataset: ds_headcount_monthly
    ds_hc = db.session.query(SqlaTable).filter_by(table_name="ds_headcount_monthly").first()
    if not ds_hc:
        ds_hc = SqlaTable(table_name="ds_headcount_monthly", database=warehouse, schema="dw", sql=hc_sql)
        db.session.add(ds_hc)
        db.session.commit()
    else:
        ds_hc.sql = hc_sql
        ds_hc.database = warehouse
        db.session.commit()
    ds_hc.fetch_metadata()
    ds_hc.main_dttm_col = "month_end"
    db.session.commit()

    # 2. Dataset: ds_employee_demographics
    ds_demo = db.session.query(SqlaTable).filter_by(table_name="ds_employee_demographics").first()
    if not ds_demo:
        ds_demo = SqlaTable(table_name="ds_employee_demographics", database=warehouse, schema="dw", sql=demo_sql)
        db.session.add(ds_demo)
        db.session.commit()
    else:
        ds_demo.sql = demo_sql
        ds_demo.database = warehouse
        db.session.commit()
    ds_demo.fetch_metadata()
    ds_demo.main_dttm_col = "hire_date"
    db.session.commit()

    print("Datasets ds_headcount_monthly and ds_employee_demographics synchronized.")

    # Palette definition (Okabe-Ito)
    OKABE_ITO_BLUE = "#0072B2"
    OKABE_ITO_GREEN = "#009E73"
    OKABE_ITO_VERMILION = "#D55E00"
    OKABE_ITO_ORANGE = "#E69F00"
    OKABE_ITO_GREY = "#94A3B8"

    slices_to_add = []

    # Helper function to create or update a Slice
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

    print("\nConfiguring dashboard charts...")

    # Chart 1: M01 Headcount KPI
    kpi_m01_params = {
        "datasource": f"{ds_hc.id}__table",
        "viz_type": "big_number_total",
        "metric": {"expressionType": "SQL", "sqlExpression": "SUM(headcount_end)", "label": "Headcount"},
        "time_range": "No filter",
        "adhoc_filters": [{
            "clause": "WHERE",
            "expressionType": "SIMPLE",
            "comparator": "2026-09",
            "operator": "==",
            "subject": "year_month"
        }],
        "subheader": "Active employees on 30 Sep 2026 (+14 vs Aug 2026)",
        "y_axis_format": ",d",
    }
    s_m01 = get_or_create_slice(
        "M01 Headcount", "big_number_total", ds_hc, kpi_m01_params,
        "Total active headcount on 30 Sep 2026 is 441 (+14 vs Aug 2026)."
    )

    # Chart 2: M02 Joiners KPI
    kpi_m02_params = {
        "datasource": f"{ds_hc.id}__table",
        "viz_type": "big_number_total",
        "metric": {"expressionType": "SQL", "sqlExpression": "SUM(joiners)", "label": "Joiners"},
        "time_range": "No filter",
        "adhoc_filters": [{
            "clause": "WHERE",
            "expressionType": "SIMPLE",
            "comparator": "2026-09",
            "operator": "==",
            "subject": "year_month"
        }],
        "subheader": "New hires in Sep 2026 (+9 vs Aug 2026)",
        "y_axis_format": ",d",
    }
    s_m02 = get_or_create_slice(
        "M02 Joiners (Month)", "big_number_total", ds_hc, kpi_m02_params,
        "17 new hires joined in Sep 2026, highest monthly inflow this year."
    )

    # Chart 3: M03 Leavers KPI
    kpi_m03_params = {
        "datasource": f"{ds_hc.id}__table",
        "viz_type": "big_number_total",
        "metric": {"expressionType": "SQL", "sqlExpression": "SUM(leavers)", "label": "Leavers"},
        "time_range": "No filter",
        "adhoc_filters": [{
            "clause": "WHERE",
            "expressionType": "SIMPLE",
            "comparator": "2026-09",
            "operator": "==",
            "subject": "year_month"
        }],
        "subheader": "Exits in Sep 2026 (2 voluntary, 1 other)",
        "y_axis_format": ",d",
    }
    s_m03 = get_or_create_slice(
        "M03 Leavers (Month)", "big_number_total", ds_hc, kpi_m03_params,
        "3 employees exited in Sep 2026 (2 voluntary resignations, 1 other)."
    )

    # Chart 4: M04 Attrition Rate KPI
    kpi_m04_params = {
        "datasource": f"{ds_hc.id}__table",
        "viz_type": "big_number_total",
        "metric": {
            "expressionType": "SQL",
            "sqlExpression": "ROUND((SUM(leavers)::numeric / NULLIF(SUM(headcount_start), 0)) * 100, 2)",
            "label": "Attrition Rate"
        },
        "time_range": "No filter",
        "adhoc_filters": [{
            "clause": "WHERE",
            "expressionType": "SIMPLE",
            "comparator": "2026-09",
            "operator": "==",
            "subject": "year_month"
        }],
        "subheader": "Monthly exits / starting headcount (Sep 2026)",
        "y_axis_format": ".1f",
    }
    s_m04 = get_or_create_slice(
        "M04 Attrition Rate (Monthly)", "big_number_total", ds_hc, kpi_m04_params,
        "0.70% monthly attrition in Sep 2026, remaining well below the 1.5% threshold."
    )

    # Chart 5: Headcount Trend (Line)
    trend_params = {
        "datasource": f"{ds_hc.id}__table",
        "viz_type": "echarts_timeseries_line",
        "granularity_sqla": "month_end",
        "time_grain_sqla": "P1M",
        "time_range": "2020-01-01 : 2026-10-01",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "SUM(headcount_end)", "label": "Total Headcount"}],
        "y_axis_format": ",d",
        "color_scheme": "supersetColors",
        "seriesType": "line",
        "show_value": False,
        "area": True,
        "opacity": 0.2,
        "rich_tooltip": True,
    }
    s_trend = get_or_create_slice(
        "M01 Headcount Trend (Monthly)", "echarts_timeseries_line", ds_hc, trend_params,
        "Headcount expanded from 380 in April 2025 to 441 in September 2026 (+16.1%), with accelerated expansion in Q3 2026."
    )

    # Chart 6: Department Split (Bar) - using dist_bar for categorical distribution
    dept_params = {
        "datasource": f"{ds_hc.id}__table",
        "viz_type": "dist_bar",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "SUM(headcount_end)", "label": "Headcount"}],
        "groupby": ["department_name"],
        "show_legend": False,
        "time_range": "No filter",
        "adhoc_filters": [{
            "clause": "WHERE",
            "expressionType": "SIMPLE",
            "comparator": "2026-09",
            "operator": "==",
            "subject": "year_month"
        }],
        "order_desc": True,
        "row_limit": 50,
        "y_axis_format": ",d",
    }
    s_dept = get_or_create_slice(
        "M01 Department Split (Sep 2026)", "dist_bar", ds_hc, dept_params,
        "Engineering represents 37.9% of company headcount (167 staff), followed by Customer Support (59) and Data & AI (52)."
    )

    # Chart 7: Tenure Bands (Bar) - using dist_bar for categorical distribution
    tenure_params = {
        "datasource": f"{ds_demo.id}__table",
        "viz_type": "dist_bar",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(DISTINCT employee_id)", "label": "Active Employees"}],
        "groupby": ["tenure_band"],
        "show_legend": False,
        "time_range": "No filter",
        "order_desc": False,
        "row_limit": 50,
        "y_axis_format": ",d",
    }
    s_tenure = get_or_create_slice(
        "Active Workforce by Tenure Band", "dist_bar", ds_demo, tenure_params,
        "Half the organization (50.6%) has joined within the last 3 years (1-3 yrs: 123; <1 yr: 97), showing strong junior-to-mid career hiring."
    )

    # Chart 8: Role Mix (Bar) - using dist_bar for top roles
    role_params = {
        "datasource": f"{ds_demo.id}__table",
        "viz_type": "dist_bar",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(DISTINCT employee_id)", "label": "Active Employees"}],
        "groupby": ["role_title"],
        "row_limit": 10,
        "show_legend": False,
        "time_range": "No filter",
        "order_desc": True,
        "y_axis_format": ",d",
    }
    s_role = get_or_create_slice(
        "Role Mix — Top Roles", "dist_bar", ds_demo, role_params,
        "Core technical engineering positions lead the workforce, tied at 29 each for QA Engineers and Software Engineers."
    )

    # Chart 9: Joiners vs Leavers by Month (Grouped Bar)
    flow_params = {
        "datasource": f"{ds_hc.id}__table",
        "viz_type": "echarts_timeseries_bar",
        "granularity_sqla": "month_end",
        "time_grain_sqla": "P1M",
        "time_range": "2025-01-01 : 2026-10-01",
        "metrics": [
            {"expressionType": "SQL", "sqlExpression": "SUM(joiners)", "label": "M02 Joiners (Hires)"},
            {"expressionType": "SQL", "sqlExpression": "SUM(leavers)", "label": "M03 Leavers (Exits)"}
        ],
        "bar_stacked": False,
        "y_axis_format": ",d",
    }
    s_flow = get_or_create_slice(
        "M02 & M03 Joiners vs. Leavers by Month", "echarts_timeseries_bar", ds_hc, flow_params,
        "Hiring consistently outpaced leavers across 2025–2026, reaching a peak net addition of +14 in Sep 2026."
    )

    # 3. Create or update the Dashboard
    dash_title = "Headcount & Departments"
    dash = db.session.query(Dashboard).filter_by(dashboard_title=dash_title).first()
    if not dash:
        dash = Dashboard(
            dashboard_title=dash_title,
            slug="headcount-and-departments",
            published=True
        )
        db.session.add(dash)
        db.session.commit()
    else:
        dash.published = True

    # Associate slices to dashboard
    dash.slices = slices_to_add

    # Construct Dashboard Grid Layout JSON with full tree relationships (children AND parents)
    position_json = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {
            "children": ["GRID_ID"],
            "id": "ROOT_ID",
            "type": "ROOT"
        },
        "GRID_ID": {
            "children": ["ROW_HEADER", "ROW_KPIS", "ROW_MID_1", "ROW_MID_2", "ROW_BOTTOM"],
            "id": "GRID_ID",
            "parents": ["ROOT_ID"],
            "type": "GRID"
        },
        "ROW_HEADER": {
            "children": ["MARKDOWN_HEADER"],
            "id": "ROW_HEADER",
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": ["ROOT_ID", "GRID_ID"],
            "type": "ROW",
        },
        "MARKDOWN_HEADER": {
            "children": [],
            "id": "MARKDOWN_HEADER",
            "meta": {
                "code": "# PulseIQ: Headcount & Departments\n**As of 30 September 2026** | Enterprise HR Star-Schema Analytics (Schema `dw`). Use the filters on the left to filter all charts by Department or Time Period.",
                "height": 50,
                "width": 12
            },
            "parents": ["ROOT_ID", "GRID_ID", "ROW_HEADER"],
            "type": "MARKDOWN"
        },
        "ROW_KPIS": {
            "children": [f"CHART-{s_m01.id}", f"CHART-{s_m02.id}", f"CHART-{s_m03.id}", f"CHART-{s_m04.id}"],
            "id": "ROW_KPIS",
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": ["ROOT_ID", "GRID_ID"],
            "type": "ROW",
        },
        f"CHART-{s_m01.id}": {
            "children": [],
            "id": f"CHART-{s_m01.id}",
            "meta": {"chartId": s_m01.id, "height": 30, "sliceName": s_m01.slice_name, "width": 3},
            "parents": ["ROOT_ID", "GRID_ID", "ROW_KPIS"],
            "type": "CHART"
        },
        f"CHART-{s_m02.id}": {
            "children": [],
            "id": f"CHART-{s_m02.id}",
            "meta": {"chartId": s_m02.id, "height": 30, "sliceName": s_m02.slice_name, "width": 3},
            "parents": ["ROOT_ID", "GRID_ID", "ROW_KPIS"],
            "type": "CHART"
        },
        f"CHART-{s_m03.id}": {
            "children": [],
            "id": f"CHART-{s_m03.id}",
            "meta": {"chartId": s_m03.id, "height": 30, "sliceName": s_m03.slice_name, "width": 3},
            "parents": ["ROOT_ID", "GRID_ID", "ROW_KPIS"],
            "type": "CHART"
        },
        f"CHART-{s_m04.id}": {
            "children": [],
            "id": f"CHART-{s_m04.id}",
            "meta": {"chartId": s_m04.id, "height": 30, "sliceName": s_m04.slice_name, "width": 3},
            "parents": ["ROOT_ID", "GRID_ID", "ROW_KPIS"],
            "type": "CHART"
        },
        "ROW_MID_1": {
            "children": [f"CHART-{s_trend.id}", f"CHART-{s_dept.id}"],
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
        f"CHART-{s_dept.id}": {
            "children": [],
            "id": f"CHART-{s_dept.id}",
            "meta": {"chartId": s_dept.id, "height": 65, "sliceName": s_dept.slice_name, "width": 6},
            "parents": ["ROOT_ID", "GRID_ID", "ROW_MID_1"],
            "type": "CHART"
        },
        "ROW_MID_2": {
            "children": [f"CHART-{s_tenure.id}", f"CHART-{s_role.id}"],
            "id": "ROW_MID_2",
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": ["ROOT_ID", "GRID_ID"],
            "type": "ROW",
        },
        f"CHART-{s_tenure.id}": {
            "children": [],
            "id": f"CHART-{s_tenure.id}",
            "meta": {"chartId": s_tenure.id, "height": 65, "sliceName": s_tenure.slice_name, "width": 6},
            "parents": ["ROOT_ID", "GRID_ID", "ROW_MID_2"],
            "type": "CHART"
        },
        f"CHART-{s_role.id}": {
            "children": [],
            "id": f"CHART-{s_role.id}",
            "meta": {"chartId": s_role.id, "height": 65, "sliceName": s_role.slice_name, "width": 6},
            "parents": ["ROOT_ID", "GRID_ID", "ROW_MID_2"],
            "type": "CHART"
        },
        "ROW_BOTTOM": {
            "children": [f"CHART-{s_flow.id}"],
            "id": "ROW_BOTTOM",
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": ["ROOT_ID", "GRID_ID"],
            "type": "ROW",
        },
        f"CHART-{s_flow.id}": {
            "children": [],
            "id": f"CHART-{s_flow.id}",
            "meta": {"chartId": s_flow.id, "height": 65, "sliceName": s_flow.slice_name, "width": 12},
            "parents": ["ROOT_ID", "GRID_ID", "ROW_BOTTOM"],
            "type": "CHART"
        },
    }

    dash.position_json = json.dumps(position_json)

    # 4. Native Filters: Department and Time Period
    native_filters = [
        {
            "id": "NATIVE_FILTER_DEPT",
            "name": "Department",
            "filterType": "filter_select",
            "targets": [
                {"datasetId": ds_hc.id, "column": {"name": "department_name"}},
                {"datasetId": ds_demo.id, "column": {"name": "department_name"}}
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
                {"datasetId": ds_hc.id, "column": {"name": "month_end"}}
            ],
            "defaultDataMask": {"filterState": {"value": "2020-01-01 : 2026-10-01"}},
            "cascadeParentIds": [],
            "scope": {"rootPath": ["ROOT_ID"], "excluded": []},
            "isInstant": True,
            "type": "NATIVE_FILTER"
        }
    ]

    dash_metadata = {
        "color_scheme": "supersetColors",
        "label_colors": {
            "Total Headcount": OKABE_ITO_BLUE,
            "Engineering": OKABE_ITO_BLUE,
            "M02 Joiners (Hires)": OKABE_ITO_GREEN,
            "M03 Leavers (Exits)": OKABE_ITO_VERMILION
        },
        "native_filter_configuration": native_filters,
        "expanded_slices": {},
        "refresh_frequency": 0,
        "timed_refresh_immune_slices": []
    }
    dash.json_metadata = json.dumps(dash_metadata)

    db.session.commit()
    print(f"\nDashboard '{dash_title}' successfully rebuilt with {len(slices_to_add)} charts and native filters!")
