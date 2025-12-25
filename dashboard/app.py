"""
DFS Dashboard - Real-time monitoring and visualization
"""
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import yaml
from datetime import datetime
import pytz
from tzlocal import get_localzone
import sys
sys.path.append('..')
from database import DatabaseManager, Drone, Task, FireDetection, DroneState, TaskState
from utils.logger import get_logger

logger = get_logger()


class DFSDashboard:
    """
    Real-time monitoring dashboard using Dash/Plotly
    
    Shows drone positions, fire detections, system status on a map.
    Updates every 500ms - fast enough to feel real-time without
    hammering the database.
    
    TODO: Add historical playback feature
    TODO: Implement drone camera feed streaming
    TODO: Add mission planning interface (currently CLI only)
    
    Known issue: Map sometimes lags with 10+ drones. Need to optimize
    the marker rendering or switch to clustering.
    """
    def __init__(self, config_path='../config/dfs_config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.db_manager = DatabaseManager(config_path)
        self.gps_cache = {}  # Cache GPS data to avoid reloading
        self.click_counts = {}  # Track click counts for double-click detection
        
        # Initialize Dash app
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.DARKLY],
            suppress_callback_exceptions=True
        )
        
        # Add custom CSS for hover effects
        self.app.index_string = '''
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>{%title%}</title>
                {%favicon%}
                {%css%}
                <style>
                    .task-row:hover {
                        background-color: rgba(0, 255, 255, 0.2) !important;
                    }
                </style>
            </head>
            <body>
                {%app_entry%}
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
            </body>
        </html>
        '''
        
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """Setup dashboard layout"""
        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Img(src='/assets/anshul-drone.png', style={'height': '80px', 'marginRight': '15px'}),
                        html.Span("Drone Firefighting System", style={'fontSize': '1.8em', 'fontWeight': 'bold'})
                    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}),
                    html.P("Ground Control Dashboard", className="text-center text-muted", style={'marginTop': '5px', 'marginBottom': '10px', 'fontSize': '1.2em'})
                ], width=10),
                dbc.Col([
                    html.Div([
                        html.Img(src='/assets/Anshul.png', style={'height': '80px', 'marginRight': '15px'}),
                        html.P("Developed by Anshul Ojha", style={'fontSize': '0.85em', 'marginBottom': '2px', 'fontWeight': '500'}),
                        html.P("© 2025 All Rights Reserved", style={'fontSize': '0.75em', 'marginBottom': '0px', 'color': '#6c757d'})
                    ], style={'textAlign': 'right', 'paddingTop': '20px'})
                ], width=2)
            ], className="mb-2"),
            
            # System Status Cards - Compact
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Drones", className="card-title", style={'marginBottom': '5px'}),
                            html.H4(id="drone-count", className="text-success", style={'marginBottom': '2px'}),
                            html.P(id="drone-status", className="text-muted", style={'fontSize': '0.75em', 'marginBottom': '0'})
                        ], style={'padding': '10px'})
                    ])
                ], width=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Active Tasks", className="card-title", style={'marginBottom': '5px'}),
                            html.H4(id="task-count", className="text-info", style={'marginBottom': '2px'}),
                            html.P(id="task-status", className="text-muted", style={'fontSize': '0.75em', 'marginBottom': '0'})
                        ], style={'padding': '10px'})
                    ])
                ], width=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Fire Detections", className="card-title", style={'marginBottom': '5px'}),
                            html.H4(id="detection-count", className="text-danger", style={'marginBottom': '2px'}),
                            html.P(id="detection-status", className="text-muted", style={'fontSize': '0.75em', 'marginBottom': '0'})
                        ], style={'padding': '10px'})
                    ])
                ], width=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("System Status", className="card-title", style={'marginBottom': '5px'}),
                            html.H4(id="system-status", className="text-warning", style={'marginBottom': '2px'}),
                            html.P(id="system-uptime", className="text-muted", style={'fontSize': '0.75em', 'marginBottom': '0'})
                        ], style={'padding': '10px'})
                    ])
                ], width=3),
            ], className="mb-2"),
            
            # Map and Charts
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            "Mission Map",
                            html.Span(" (Click a task below to view its area)", className="text-muted", style={'fontSize': '0.8em'})
                        ]),
                        dbc.CardBody([
                            dcc.Graph(id="mission-map", style={'height': '500px'}),
                            html.Div(id="selected-task-info", className="mt-2 text-muted", style={'fontSize': '0.9em'})
                        ])
                    ])
                ], width=8),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Drone Fleet Status"),
                        dbc.CardBody([
                            dcc.Graph(id="drone-status-chart", style={'height': '250px'}),
                            html.Hr(),
                            html.Div(id="drone-list")
                        ])
                    ])
                ], width=4),
            ], className="mb-4"),
            
            # Operational Controls
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(" Operational Controls"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.H6("Task Management"),
                                    dbc.InputGroup([
                                        dbc.Input(id="task-id-input", placeholder="Task ID (e.g., TASK-20251220-0001)"),
                                        dbc.Button("Cancel Task", id="cancel-task-btn", color="warning", n_clicks=0)
                                    ], className="mb-2"),
                                    dbc.Button("Reset Stale Tasks", id="reset-stale-btn", color="danger", n_clicks=0, className="w-100"),
                                    html.Div(id="task-control-output", className="mt-2")
                                ], width=6),
                                dbc.Col([
                                    html.H6("Drone Control"),
                                    dbc.InputGroup([
                                        dbc.Input(id="drone-id-input", placeholder="Drone ID (e.g., SD-001)"),
                                        dbc.Button("RTS (Return to Station)", id="rts-btn", color="info", n_clicks=0)
                                    ], className="mb-2"),
                                    html.Div(id="drone-control-output", className="mt-2")
                                ], width=6)
                            ])
                        ])
                    ])
                ])
            ], className="mb-4"),
            
            # Task Table
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Div([
                                html.Span("Recent Tasks", className="me-3"),
                                html.Small("(Click  to highlight, Double-click  for waypoints)", className="text-muted me-3"),
                                dbc.Button(
                                    "⏸ Pause",
                                    id="refresh-toggle-btn",
                                    color="secondary",
                                    size="sm",
                                    outline=True
                                )
                            ], className="d-flex align-items-center justify-content-between")
                        ]),
                        dbc.CardBody([
                            html.Div(
                                id="task-table",
                                style={
                                    'maxHeight': '400px',
                                    'overflowY': 'auto',
                                    'overflowX': 'auto'
                                }
                            )
                        ])
                    ])
                ])
            ], className="mb-4"),
            
            # Store components for task interaction
            dcc.Store(id='highlighted-task-id', data=''),  # Single click - highlight only
            dcc.Store(id='waypoint-task-id', data=''),     # Double click - show waypoints
            dcc.Store(id='refresh-paused', data=False),    # Pause/resume refresh
            
            # Auto-refresh (5 seconds)
            dcc.Interval(
                id='interval-component',
                interval=500,  # 0.5 seconds
                n_intervals=0,
                disabled=False
            )
        ], fluid=True)
    
    def setup_callbacks(self):
        """Setup dashboard callbacks"""
        
        @self.app.callback(
            [Output('drone-count', 'children'),
             Output('drone-status', 'children'),
             Output('task-count', 'children'),
             Output('task-status', 'children'),
             Output('detection-count', 'children'),
             Output('detection-status', 'children'),
             Output('system-status', 'children'),
             Output('system-uptime', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_status_cards(n):
            session = self.db_manager.get_session()
            
            try:
                # Drone stats
                drones = session.query(Drone).all()
                idle_drones = len([d for d in drones if d.state == DroneState.IDLE])
                flying_drones = len([d for d in drones if d.state == DroneState.FLYING])
                
                # Task stats
                tasks = session.query(Task).all()
                active_tasks = len([t for t in tasks if t.state in [TaskState.ASSIGNED, TaskState.EXECUTING]])
                completed_tasks = len([t for t in tasks if t.state == TaskState.COMPLETED])
                
                # Detection stats
                detections = session.query(FireDetection).all()
                active_fires = len([d for d in detections if d.status == 'detected'])
                suppressed_fires = len([d for d in detections if d.status == 'suppressed'])
                
                return (
                    f"{len(drones)}",
                    f"{idle_drones} idle, {flying_drones} flying",
                    f"{active_tasks}",
                    f"{completed_tasks} completed",
                    f"{len(detections)}",
                    f"{active_fires} active, {suppressed_fires} suppressed",
                    "OPERATIONAL",
                    datetime.now().strftime("%H:%M:%S")
                )
            finally:
                self.db_manager.close_session(session)
        
        @self.app.callback(
            Output('mission-map', 'figure'),
            [Input('interval-component', 'n_intervals'),
             Input('highlighted-task-id', 'data'),
             Input('waypoint-task-id', 'data')]
        )
        def update_map(n, highlighted_task_id, waypoint_task_id):
            session = self.db_manager.get_session()
            
            try:
                # Get all drones and detections
                drones = session.query(Drone).all()
                detections = session.query(FireDetection).all()
                # Get all tasks (not just executing/assigned) to show on map
                all_tasks = session.query(Task).filter(
                    Task.corner_a_lat.isnot(None)
                ).order_by(Task.created_at.desc()).limit(10).all()
                
                fig = go.Figure()
                
                # Plot drones
                drone_lats = [d.current_latitude for d in drones if d.current_latitude]
                drone_lons = [d.current_longitude for d in drones if d.current_longitude]
                drone_ids = [d.drone_id for d in drones if d.current_latitude]
                drone_states = [d.state.value for d in drones if d.current_latitude]
                
                if drone_lats:
                    fig.add_trace(go.Scattermapbox(
                        lat=drone_lats,
                        lon=drone_lons,
                        mode='markers+text',
                        marker=dict(size=15, color='blue'),
                        text=drone_ids,
                        textposition='top center',
                        name='Drones',
                        hovertemplate='<b>%{text}</b><br>State: %{customdata}<extra></extra>',
                        customdata=drone_states
                    ))
                
                # Plot fire detections
                fire_lats = [d.latitude for d in detections]
                fire_lons = [d.longitude for d in detections]
                fire_temps = [f"{d.temperature_c:.1f}°C" for d in detections]
                fire_status = [d.status for d in detections]
                
                if fire_lats:
                    fig.add_trace(go.Scattermapbox(
                        lat=fire_lats,
                        lon=fire_lons,
                        mode='markers',
                        marker=dict(size=20, color='red', symbol='fire-station'),
                        name='Fire Detections',
                        hovertemplate='<b>Fire</b><br>Temp: %{customdata[0]}<br>Status: %{customdata[1]}<extra></extra>',
                        customdata=list(zip(fire_temps, fire_status))
                    ))
                
                # Plot task areas with different colors based on state
                for task in all_tasks:
                    if task.corner_a_lat:
                        # Color based on task state
                        color_map = {
                            'executing': 'yellow',
                            'assigned': 'orange',
                            'completed': 'green',
                            'cancelled': 'gray'
                        }
                        task_color = color_map.get(task.state.value, 'white')
                        
                        # Highlight if clicked or showing waypoints
                        line_width = 3
                        opacity = 1.0
                        if highlighted_task_id and task.task_id == highlighted_task_id:
                            line_width = 6
                            task_color = 'cyan'
                            opacity = 1.0
                        elif waypoint_task_id and task.task_id == waypoint_task_id:
                            line_width = 6
                            task_color = 'cyan'
                            opacity = 1.0
                        
                        # Draw flight area polygon
                        fig.add_trace(go.Scattermapbox(
                            lat=[task.corner_a_lat, task.corner_b_lat, task.corner_c_lat, task.corner_d_lat, task.corner_a_lat],
                            lon=[task.corner_a_lon, task.corner_b_lon, task.corner_c_lon, task.corner_d_lon, task.corner_a_lon],
                            mode='lines',
                            line=dict(width=line_width, color=task_color),
                            name=f'{task.task_id} ({task.state.value})',
                            hovertemplate=f'<b>{task.task_id}</b><br>State: {task.state.value}<br>Type: {task.task_type}<br><i>Double-click row to show path</i><extra></extra>',
                            showlegend=True,
                            opacity=opacity
                        ))
                        
                        # Add corner markers
                        fig.add_trace(go.Scattermapbox(
                            lat=[task.corner_a_lat, task.corner_b_lat, task.corner_c_lat, task.corner_d_lat],
                            lon=[task.corner_a_lon, task.corner_b_lon, task.corner_c_lon, task.corner_d_lon],
                            mode='markers',
                            marker=dict(size=8, color=task_color, symbol='circle'),
                            text=['A', 'B', 'C', 'D'],
                            name=f'{task.task_id} corners',
                            hovertemplate='Corner %{text}<extra></extra>',
                            showlegend=False
                        ))
                        
                        # If task is double-clicked, show full waypoint path
                        if waypoint_task_id and task.task_id == waypoint_task_id:
                            # Check cache first
                            if task.task_id not in self.gps_cache:
                                # Try to find and load GPS data
                                import os
                                import glob
                                
                                gps_file = None
                                if task.data_path and os.path.exists(task.data_path):
                                    # Try the expected path
                                    gps_file = os.path.join(task.data_path, 'gps', f"{os.path.basename(task.data_path)}_gps.csv")
                                    if not os.path.exists(gps_file):
                                        # Try to find any GPS file in the data directory
                                        gps_pattern = os.path.join(task.data_path, 'gps', '*_gps.csv')
                                        gps_files = glob.glob(gps_pattern)
                                        if gps_files:
                                            gps_file = gps_files[0]
                                
                                if gps_file and os.path.exists(gps_file):
                                    try:
                                        import pandas as pd
                                        gps_data = pd.read_csv(gps_file)
                                        # Cache the GPS data
                                        self.gps_cache[task.task_id] = {
                                            'lats': gps_data['latitude'].tolist(),
                                            'lons': gps_data['longitude'].tolist()
                                        }
                                        logger.info(f"[OK] Loaded {len(gps_data)} waypoints for {task.task_id} from {gps_file}")
                                    except Exception as e:
                                        logger.error(f"[FAIL] Error loading GPS data for {task.task_id}: {e}")
                                        self.gps_cache[task.task_id] = None
                                else:
                                    logger.warning(f"[WARN] No GPS file found for {task.task_id} (data_path: {task.data_path})")
                                    self.gps_cache[task.task_id] = None
                            
                            # Use cached data if available
                            if task.task_id in self.gps_cache and self.gps_cache[task.task_id]:
                                cached_data = self.gps_cache[task.task_id]
                                # Show full flight path with line
                                fig.add_trace(go.Scattermapbox(
                                    lat=cached_data['lats'],
                                    lon=cached_data['lons'],
                                    mode='lines+markers',
                                    line=dict(width=2, color='magenta'),
                                    marker=dict(size=3, color='magenta', opacity=0.7),
                                    name=f'{task.task_id} flight path',
                                    hovertemplate='Waypoint %{pointNumber}<br>Lat: %{lat:.6f}<br>Lon: %{lon:.6f}<extra></extra>',
                                    showlegend=True
                                ))
                                # Add start and end markers
                                fig.add_trace(go.Scattermapbox(
                                    lat=[cached_data['lats'][0], cached_data['lats'][-1]],
                                    lon=[cached_data['lons'][0], cached_data['lons'][-1]],
                                    mode='markers+text',
                                    marker=dict(size=12, color=['green', 'red'], symbol=['circle', 'square']),
                                    text=['START', 'END'],
                                    textposition='top center',
                                    name=f'{task.task_id} start/end',
                                    showlegend=False
                                ))
                
                # Set map center
                center_lat = self.config['dashboard']['map']['default_center'][0]
                center_lon = self.config['dashboard']['map']['default_center'][1]
                
                fig.update_layout(
                    mapbox=dict(
                        style='open-street-map',
                        center=dict(lat=center_lat, lon=center_lon),
                        zoom=self.config['dashboard']['map']['default_zoom']
                    ),
                    showlegend=True,
                    margin=dict(l=0, r=0, t=0, b=0),
                    paper_bgcolor='#222',
                    plot_bgcolor='#222',
                    height=600,
                    uirevision='constant'  # Preserve map state between updates
                )
                
                return fig
            finally:
                self.db_manager.close_session(session)
        
        @self.app.callback(
            Output('drone-status-chart', 'figure'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_drone_chart(n):
            session = self.db_manager.get_session()
            
            try:
                drones = session.query(Drone).all()
                
                # Count by state
                state_counts = {}
                for drone in drones:
                    state = drone.state.value
                    state_counts[state] = state_counts.get(state, 0) + 1
                
                fig = go.Figure(data=[
                    go.Pie(
                        labels=list(state_counts.keys()),
                        values=list(state_counts.values()),
                        hole=0.3
                    )
                ])
                
                fig.update_layout(
                    showlegend=True,
                    margin=dict(l=0, r=0, t=0, b=0),
                    paper_bgcolor='#222',
                    plot_bgcolor='#222'
                )
                
                return fig
            finally:
                self.db_manager.close_session(session)
        
        @self.app.callback(
            Output('drone-list', 'children'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_drone_list(n):
            session = self.db_manager.get_session()
            
            try:
                drones = session.query(Drone).all()
                
                drone_items = []
                for drone in drones:
                    color = 'success' if drone.state == DroneState.IDLE else 'warning' if drone.state == DroneState.FLYING else 'secondary'
                    
                    drone_items.append(
                        html.Div([
                            dbc.Badge(drone.drone_id, color=color, className="me-2"),
                            html.Small(f"{drone.battery_percent:.0f}%", className="text-muted")
                        ], className="mb-2")
                    )
                
                return drone_items
            finally:
                self.db_manager.close_session(session)
        
        @self.app.callback(
            Output('task-table', 'children'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_task_table(n):
            session = self.db_manager.get_session()
            
            try:
                # Show last 50 tasks instead of 10 (scrollable container handles display)
                tasks = session.query(Task).order_by(Task.created_at.desc()).limit(50).all()
                
                if not tasks:
                    return html.P("No tasks yet", className="text-muted")
                
                table_rows = []
                for task in tasks:
                    drone_id = session.query(Drone).get(task.drone_id).drone_id if task.drone_id else "Unassigned"
                    
                    color = {
                        'created': 'secondary',
                        'assigned': 'info',
                        'executing': 'warning',
                        'completed': 'success',
                        'failed': 'danger',
                        'cancelled': 'dark'
                    }.get(task.state.value, 'secondary')
                    
                    # Format timestamp in local time with date and time
                    if task.created_at:
                        # Convert UTC to local timezone
                        local_tz = get_localzone()
                        utc_time = task.created_at.replace(tzinfo=pytz.UTC)
                        local_time = utc_time.astimezone(local_tz)
                        created_str = local_time.strftime("%Y-%m-%d %H:%M:%S %Z")
                    else:
                        created_str = ""
                    
                    # Make row clickable with proper ID
                    row_id = f"task-row-{task.task_id}"
                    table_rows.append(
                        html.Tr([
                            html.Td(task.task_id),
                            html.Td(task.task_type),
                            html.Td(drone_id),
                            html.Td(dbc.Badge(task.state.value, color=color)),
                            html.Td(created_str),
                            html.Td(
                                dbc.Button(
                                    "👁",
                                    id={'type': 'task-view-btn', 'task_id': task.task_id},
                                    color="link",
                                    size="sm",
                                    className="p-0",
                                    title="Click to highlight area, Double-click to show waypoints"
                                )
                            )
                        ], 
                        id=row_id,
                        className='task-row')
                    )
                
                return dbc.Table([
                    html.Thead(html.Tr([
                        html.Th("Task ID"),
                        html.Th("Type"),
                        html.Th("Drone"),
                        html.Th("Status"),
                        html.Th("Created"),
                        html.Th("View")
                    ])),
                    html.Tbody(table_rows)
                ], bordered=True, dark=True, hover=True, size='sm')
            finally:
                self.db_manager.close_session(session)
        
        # Operational control callbacks
        @self.app.callback(
            Output('task-control-output', 'children'),
            [Input('cancel-task-btn', 'n_clicks'),
             Input('reset-stale-btn', 'n_clicks')],
            [State('task-id-input', 'value')]
        )
        def handle_task_controls(cancel_clicks, reset_clicks, task_id):
            from mission_control.orchestrator import MissionOrchestrator
            orchestrator = MissionOrchestrator()
            
            ctx = dash.callback_context
            if not ctx.triggered:
                return ""
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if button_id == 'cancel-task-btn' and cancel_clicks > 0:
                if not task_id:
                    return dbc.Alert("Please enter a Task ID", color="warning", dismissable=True)
                
                success = orchestrator.cancel_task(task_id)
                if success:
                    return dbc.Alert(f"[OK] Task {task_id} cancelled OK", color="success", dismissable=True)
                else:
                    return dbc.Alert(f"[FAIL] Failed to cancel task {task_id}", color="danger", dismissable=True)
            
            elif button_id == 'reset-stale-btn' and reset_clicks > 0:
                count = orchestrator.reset_stale_tasks(max_age_hours=1)
                return dbc.Alert(f"[OK] Reset {count} stale task(s)", color="success", dismissable=True)
            
            return ""
        
        @self.app.callback(
            Output('drone-control-output', 'children'),
            [Input('rts-btn', 'n_clicks')],
            [State('drone-id-input', 'value')]
        )
        def handle_drone_rts(n_clicks, drone_id):
            if n_clicks == 0:
                return ""
            
            if not drone_id:
                return dbc.Alert("Please enter a Drone ID", color="warning", dismissable=True)
            
            from mission_control.orchestrator import MissionOrchestrator
            orchestrator = MissionOrchestrator()
            
            success = orchestrator.return_drone_to_station(drone_id)
            if success:
                return dbc.Alert(f"[OK] RTS command sent to {drone_id}", color="success", dismissable=True)
            else:
                return dbc.Alert(f"[FAIL] Failed to send RTS to {drone_id}", color="danger", dismissable=True)
        
        # Callback to handle pause/resume refresh button
        @self.app.callback(
            [Output('interval-component', 'disabled'),
             Output('refresh-toggle-btn', 'children')],
            [Input('refresh-toggle-btn', 'n_clicks')],
            [State('interval-component', 'disabled')],
            prevent_initial_call=True
        )
        def toggle_refresh(n_clicks, is_paused):
            if n_clicks:
                new_state = not is_paused
                button_text = " Resume" if new_state else "⏸ Pause"
                return new_state, button_text
            return is_paused, "⏸ Pause" if not is_paused else " Resume"
        
        # Callback to handle task view button clicks
        @self.app.callback(
            [Output('highlighted-task-id', 'data'),
             Output('waypoint-task-id', 'data')],
            [Input({'type': 'task-view-btn', 'task_id': dash.dependencies.ALL}, 'n_clicks')],
            [State('highlighted-task-id', 'data'),
             State('waypoint-task-id', 'data')],
            prevent_initial_call=True
        )
        def handle_task_click(n_clicks_list, current_highlighted, current_waypoint):
            ctx = dash.callback_context
            if not ctx.triggered:
                return current_highlighted, current_waypoint
            
            # Get which button was clicked
            triggered_id = ctx.triggered[0]['prop_id']
            if 'task-view-btn' in triggered_id:
                import json
                try:
                    id_dict = json.loads(triggered_id.split('.')[0])
                    task_id = id_dict['task_id']
                    
                    # Check if this is a double-click (same task clicked twice quickly)
                    import time
                    current_time = time.time()
                    
                    if task_id in self.click_counts:
                        last_click_time = self.click_counts[task_id]
                        time_diff = current_time - last_click_time
                        
                        if time_diff < 1.0:  # Double-click within 1 second
                            # Double-click detected
                            self.click_counts.pop(task_id, None)
                            
                            if current_waypoint == task_id:
                                # Turn off waypoints
                                return '', ''
                            else:
                                # Show waypoints
                                return task_id, task_id
                    
                    # Single click: just highlight
                    self.click_counts[task_id] = current_time
                    if current_highlighted == task_id:
                        # Toggle off highlight
                        return '', ''
                    else:
                        # Highlight only
                        return task_id, ''
                except Exception as e:
                    pass
            
            return current_highlighted, current_waypoint
        
        # Callback to update selected task info display
        @self.app.callback(
            Output('selected-task-info', 'children'),
            [Input('highlighted-task-id', 'data'),
             Input('waypoint-task-id', 'data')]
        )
        def update_task_info(highlighted_task_id, waypoint_task_id):
            if waypoint_task_id:
                # Check if waypoints are loaded
                if waypoint_task_id in self.gps_cache and self.gps_cache[waypoint_task_id]:
                    num_waypoints = len(self.gps_cache[waypoint_task_id]['lats'])
                    return html.Div([
                        html.I(className="bi bi-check-circle-fill me-2", style={'color': 'lime'}),
                        html.Span(f"Showing flight path for {waypoint_task_id} ({num_waypoints} waypoints)", 
                                 style={'color': 'cyan'})
                    ])
                else:
                    return html.Div([
                        html.I(className="bi bi-exclamation-triangle-fill me-2", style={'color': 'orange'}),
                        html.Span(f"No GPS data available for {waypoint_task_id}", 
                                 style={'color': 'orange'})
                    ])
            elif highlighted_task_id:
                return html.Div([
                    html.I(className="bi bi-eye-fill me-2", style={'color': 'cyan'}),
                    html.Span(f"Highlighting area for {highlighted_task_id}", 
                             style={'color': 'cyan'})
                ])
            else:
                return html.Span("Click 👁 to highlight task area, double-click to show waypoints")
    
    def run(self, debug=None):
        """Run the dashboard"""
        host = self.config['dashboard']['host']
        port = self.config['dashboard']['port']
        # Allow override of debug setting from command line
        if debug is None:
            debug = self.config['dashboard']['debug']
        
        logger.info(f"\n  Starting DFS Dashboard...")
        logger.info(f"   URL: http://{host}:{port}")
        
        self.app.run_server(host=host, port=port, debug=debug)


if __name__ == '__main__':
    dashboard = DFSDashboard()
    dashboard.run()
