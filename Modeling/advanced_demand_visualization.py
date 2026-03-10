# -*- coding: utf-8 -*-
"""
Advanced Demand Visualization Suite
Provides specialized visualizations for demand-weighted optimization analysis.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from collections import defaultdict


def create_demand_heatmap(parameters, solution_data):
    """
    Create a heatmap showing demand coverage by station and time.
    
    Parameters:
        parameters: Dictionary of problem parameters
        solution_data: Dictionary of solution variables
    
    Returns:
        plotly.graph_objects.Figure
    """
    print("\n" + "="*70)
    print("CREATING DEMAND HEATMAP")
    print("="*70)
    
    # Time bins (hourly)
    time_bins = list(range(0, 1440, 60))
    
    # Get all stations
    stations = sorted(list(set(parameters['flight_station_out'].values()) | 
                          set(parameters['flight_station_in'].values())))
    
    # Initialize matrices
    demand_matrix = np.zeros((len(stations), len(time_bins)))
    served_matrix = np.zeros((len(stations), len(time_bins)))
    
    # Fill matrices for outgoing flights
    for k in parameters['K_out']:
        station = parameters['flight_station_out'][k]
        time = parameters['D_k'][k]
        demand = parameters['demand_out'][k]
        covered = solution_data['C'][k].X > 0.5
        
        station_idx = stations.index(station)
        time_idx = int(time // 60)
        
        if time_idx < len(time_bins):
            demand_matrix[station_idx, time_idx] += demand
            if covered:
                served_matrix[station_idx, time_idx] += demand
    
    # Fill matrices for incoming flights
    for m in parameters['K_in']:
        station = parameters['flight_station_in'][m]
        time = parameters['A_m'][m]
        demand = parameters['demand_in'][m]
        covered = solution_data['C_in'][m].X > 0.5
        
        station_idx = stations.index(station)
        time_idx = int(time // 60)
        
        if time_idx < len(time_bins):
            demand_matrix[station_idx, time_idx] += demand
            if covered:
                served_matrix[station_idx, time_idx] += demand
    
    # Calculate coverage percentage
    coverage_matrix = np.divide(served_matrix, demand_matrix, 
                                out=np.zeros_like(served_matrix), 
                                where=demand_matrix!=0) * 100
    
    # Create subplots
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=(
            '<b>Total Demand (passengers)</b>',
            '<b>Served Demand (passengers)</b>',
            '<b>Coverage Rate (%)</b>'
        ),
        horizontal_spacing=0.12
    )
    
    # Time labels
    time_labels = [f"{h:02d}:00" for h in range(24)]
    station_labels = [f"Station {s}" for s in stations]
    
    # Heatmap 1: Total Demand
    fig.add_trace(go.Heatmap(
        z=demand_matrix,
        x=time_labels,
        y=station_labels,
        colorscale='Blues',
        showscale=True,
        colorbar=dict(x=0.29, len=0.9, title='Passengers'),
        hovertemplate='<b>%{y}</b><br>Time: %{x}<br>Demand: %{z:.0f} pax<extra></extra>'
    ), row=1, col=1)
    
    # Heatmap 2: Served Demand
    fig.add_trace(go.Heatmap(
        z=served_matrix,
        x=time_labels,
        y=station_labels,
        colorscale='Greens',
        showscale=True,
        colorbar=dict(x=0.645, len=0.9, title='Passengers'),
        hovertemplate='<b>%{y}</b><br>Time: %{x}<br>Served: %{z:.0f} pax<extra></extra>'
    ), row=1, col=2)
    
    # Heatmap 3: Coverage Rate
    fig.add_trace(go.Heatmap(
        z=coverage_matrix,
        x=time_labels,
        y=station_labels,
        colorscale='RdYlGn',
        zmin=0,
        zmax=100,
        showscale=True,
        colorbar=dict(x=1.0, len=0.9, title='Coverage (%)'),
        hovertemplate='<b>%{y}</b><br>Time: %{x}<br>Coverage: %{z:.1f}%<extra></extra>'
    ), row=1, col=3)
    
    fig.update_layout(
        title=dict(
            text='<b>Demand Coverage Heatmap by Station and Time</b>',
            x=0.5,
            xanchor='center',
            font=dict(size=20)
        ),
        height=400 + len(stations) * 30,
        showlegend=False
    )
    
    # Update axes
    for col in [1, 2, 3]:
        fig.update_xaxes(title_text="Time of Day", row=1, col=col, side='bottom')
    
    print(f"Heatmap created for {len(stations)} stations and 24 hours")
    return fig


def create_flight_ranking_chart(parameters, solution_data):
    """
    Create a chart ranking flights by demand and coverage status.
    
    Parameters:
        parameters: Dictionary of problem parameters
        solution_data: Dictionary of solution variables
    
    Returns:
        plotly.graph_objects.Figure
    """
    print("\n" + "="*70)
    print("CREATING FLIGHT RANKING CHART")
    print("="*70)
    
    # Collect all flights with their metrics
    all_flights = []
    
    for k in parameters['K_out']:
        covered = solution_data['C'][k].X > 0.5
        demand = parameters['demand_out'][k]
        station = parameters['flight_station_out'][k]
        time = parameters['D_k'][k]
        
        # Count connected trains
        connections = sum(1 for i in parameters['I_T'] 
                         if (i, k) in solution_data['P'] and solution_data['P'][i, k].X > 0.5)
        
        all_flights.append({
            'id': f'Out-{k}',
            'flight': k,
            'type': 'Outgoing',
            'demand': demand,
            'covered': covered,
            'station': station,
            'time': time,
            'connections': connections
        })
    
    for m in parameters['K_in']:
        covered = solution_data['C_in'][m].X > 0.5
        demand = parameters['demand_in'][m]
        station = parameters['flight_station_in'][m]
        time = parameters['A_m'][m]
        
        # Count connected trains
        connections = sum(1 for i in parameters['I_T'] 
                         if (i, m) in solution_data['Q'] and solution_data['Q'][i, m].X > 0.5)
        
        all_flights.append({
            'id': f'In-{m}',
            'flight': m,
            'type': 'Incoming',
            'demand': demand,
            'covered': covered,
            'station': station,
            'time': time,
            'connections': connections
        })
    
    # Sort by demand (descending)
    all_flights.sort(key=lambda x: x['demand'], reverse=True)
    
    # Take top 30 for visibility
    top_flights = all_flights[:30]
    
    df = pd.DataFrame(top_flights)
    
    # Create figure
    fig = go.Figure()
    
    # Covered flights
    df_covered = df[df['covered'] == True]
    fig.add_trace(go.Bar(
        x=df_covered['id'],
        y=df_covered['demand'],
        name='Covered',
        marker_color='#2ca02c',
        text=df_covered['connections'],
        texttemplate='%{text} conn',
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Demand: %{y} pax<br>Connections: %{text}<extra></extra>'
    ))
    
    # Uncovered flights
    df_uncovered = df[df['covered'] == False]
    fig.add_trace(go.Bar(
        x=df_uncovered['id'],
        y=df_uncovered['demand'],
        name='Not Covered',
        marker_color='#d62728',
        text=['0']*len(df_uncovered),
        texttemplate='%{text} conn',
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Demand: %{y} pax<br>Not covered<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text='<b>Top 30 Flights Ranked by Demand</b>',
            x=0.5,
            xanchor='center',
            font=dict(size=20)
        ),
        xaxis=dict(
            title='Flight ID',
            tickangle=-45
        ),
        yaxis=dict(
            title='Passenger Demand'
        ),
        height=600,
        barmode='overlay',
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )
    
    print(f"Flight ranking chart created with top {len(top_flights)} flights")
    return fig


def create_train_productivity_chart(parameters, solution_data):
    """
    Create a chart showing train productivity (passengers served per train).
    
    Parameters:
        parameters: Dictionary of problem parameters
        solution_data: Dictionary of solution variables
    
    Returns:
        plotly.graph_objects.Figure
    """
    print("\n" + "="*70)
    print("CREATING TRAIN PRODUCTIVITY CHART")
    print("="*70)
    
    train_metrics = []
    
    for i in parameters['I']:
        # Calculate passengers served by this train
        passengers_served = 0
        sync_count = 0
        
        # Outgoing flights
        for k in parameters['K_out']:
            if (i, k) in solution_data['P'] and solution_data['P'][i, k].X > 0.5:
                passengers_served += parameters['demand_out'][k]
                sync_count += 1
        
        # Incoming flights
        for m in parameters['K_in']:
            if (i, m) in solution_data['Q'] and solution_data['Q'][i, m].X > 0.5:
                passengers_served += parameters['demand_in'][m]
                sync_count += 1
        
        # Get route info
        route = parameters['S_i'][i]
        route_str = "→".join([f"S{s}" for s in route])
        
        train_metrics.append({
            'train': i,
            'passengers': passengers_served,
            'synchronizations': sync_count,
            'route': route_str
        })
    
    # Sort by passengers served
    train_metrics.sort(key=lambda x: x['passengers'], reverse=True)
    
    df = pd.DataFrame(train_metrics)
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Bar chart for passengers
    fig.add_trace(
        go.Bar(
            x=[f"Train {t['train']}" for t in train_metrics],
            y=[t['passengers'] for t in train_metrics],
            name='Passengers Served',
            marker_color='#1f77b4',
            hovertemplate='<b>%{x}</b><br>Passengers: %{y}<extra></extra>'
        ),
        secondary_y=False
    )
    
    # Line chart for synchronizations
    fig.add_trace(
        go.Scatter(
            x=[f"Train {t['train']}" for t in train_metrics],
            y=[t['synchronizations'] for t in train_metrics],
            name='Synchronizations',
            mode='lines+markers',
            marker=dict(size=8, color='#ff7f0e'),
            line=dict(width=3, color='#ff7f0e'),
            hovertemplate='<b>%{x}</b><br>Syncs: %{y}<extra></extra>'
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title=dict(
            text='<b>Train Productivity Analysis</b>',
            x=0.5,
            xanchor='center',
            font=dict(size=20)
        ),
        xaxis=dict(
            title='Train',
            tickangle=-45
        ),
        height=600,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )
    
    fig.update_yaxes(title_text="<b>Passengers Served</b>", secondary_y=False)
    fig.update_yaxes(title_text="<b>Synchronizations</b>", secondary_y=True)
    
    # Calculate statistics
    total_passengers = sum(t['passengers'] for t in train_metrics)
    avg_passengers = total_passengers / len(train_metrics) if train_metrics else 0
    productive_trains = sum(1 for t in train_metrics if t['passengers'] > 0)
    
    print(f"Total passengers served: {total_passengers}")
    print(f"Average per train: {avg_passengers:.1f}")
    print(f"Productive trains: {productive_trains}/{len(train_metrics)}")
    
    return fig


def create_connection_quality_scatter(parameters, solution_data):
    """
    Create scatter plot showing connection quality (transfer time vs penalty).
    
    Parameters:
        parameters: Dictionary of problem parameters
        solution_data: Dictionary of solution variables
    
    Returns:
        plotly.graph_objects.Figure
    """
    print("\n" + "="*70)
    print("CREATING CONNECTION QUALITY SCATTER PLOT")
    print("="*70)
    
    connections = []
    
    # Outgoing connections
    for i in parameters['I_T']:
        for k in parameters['K_out']:
            if (i, k) in solution_data['P'] and solution_data['P'][i, k].X > 0.5:
                st_k = parameters['flight_station_out'][k]
                if (i, st_k) in solution_data['a']:
                    transfer_time = parameters['D_k'][k] - solution_data['a'][i, st_k].X
                    penalty = solution_data['p'][i, k].X if (i, k) in solution_data['p'] else 0
                    demand = parameters['demand_out'][k]
                    
                    connections.append({
                        'type': 'Outgoing',
                        'train': i,
                        'flight': k,
                        'transfer_time': transfer_time,
                        'penalty': penalty,
                        'demand': demand,
                        'station': st_k
                    })
    
    # Incoming connections
    for i in parameters['I_T']:
        for m in parameters['K_in']:
            if (i, m) in solution_data['Q'] and solution_data['Q'][i, m].X > 0.5:
                st_m = parameters['flight_station_in'][m]
                if (i, st_m) in solution_data['d']:
                    transfer_time = solution_data['d'][i, st_m].X - parameters['A_m'][m]
                    penalty = solution_data['p_in'][i, m].X if (i, m) in solution_data['p_in'] else 0
                    demand = parameters['demand_in'][m]
                    
                    connections.append({
                        'type': 'Incoming',
                        'train': i,
                        'flight': m,
                        'transfer_time': transfer_time,
                        'penalty': penalty,
                        'demand': demand,
                        'station': st_m
                    })
    
    df = pd.DataFrame(connections)
    
    # Create figure
    fig = go.Figure()
    
    # Outgoing connections
    df_out = df[df['type'] == 'Outgoing']
    fig.add_trace(go.Scatter(
        x=df_out['transfer_time'],
        y=df_out['penalty'],
        mode='markers',
        name='Outgoing',
        marker=dict(
            size=df_out['demand'] / 10,  # Scale marker size by demand
            color='#ff7f0e',
            opacity=0.6,
            line=dict(width=1, color='DarkSlateGrey')
        ),
        text=[f"Train {row['train']} → Flight {row['flight']}<br>Demand: {row['demand']} pax<br>Station {row['station']}" 
              for _, row in df_out.iterrows()],
        hovertemplate='<b>%{text}</b><br>Transfer: %{x:.1f} min<br>Penalty: %{y:.2f}<extra></extra>'
    ))
    
    # Incoming connections
    df_in = df[df['type'] == 'Incoming']
    fig.add_trace(go.Scatter(
        x=df_in['transfer_time'],
        y=df_in['penalty'],
        mode='markers',
        name='Incoming',
        marker=dict(
            size=df_in['demand'] / 10,
            color='#2ca02c',
            opacity=0.6,
            line=dict(width=1, color='DarkSlateGrey')
        ),
        text=[f"Flight {row['flight']} → Train {row['train']}<br>Demand: {row['demand']} pax<br>Station {row['station']}" 
              for _, row in df_in.iterrows()],
        hovertemplate='<b>%{text}</b><br>Transfer: %{x:.1f} min<br>Penalty: %{y:.2f}<extra></extra>'
    ))
    
    # Add optimal zone (low penalty)
    fig.add_hrect(
        y0=0, y1=5,
        fillcolor="green", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="Optimal Zone", annotation_position="top left"
    )
    
    # Add acceptable zone
    fig.add_hrect(
        y0=5, y1=15,
        fillcolor="yellow", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="Acceptable Zone", annotation_position="top left"
    )
    
    # Add transfer time boundaries
    fig.add_vline(x=20, line_dash="dash", line_color="red", 
                  annotation_text="Min Transfer", annotation_position="top")
    fig.add_vline(x=70, line_dash="dash", line_color="red", 
                  annotation_text="Max Transfer", annotation_position="top")
    fig.add_vline(x=45, line_dash="dot", line_color="blue", 
                  annotation_text="Optimal", annotation_position="bottom")
    
    fig.update_layout(
        title=dict(
            text='<b>Connection Quality Analysis</b><br><sub>Marker size represents passenger demand</sub>',
            x=0.5,
            xanchor='center',
            font=dict(size=20)
        ),
        xaxis=dict(
            title='Transfer Time (minutes)',
            range=[15, 75]
        ),
        yaxis=dict(
            title='Passenger Penalty'
        ),
        height=600,
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        hovermode='closest'
    )
    
    print(f"Scatter plot created with {len(connections)} connections")
    return fig


def generate_demand_visualizations(model, parameters, save_html=True, output_dir='visualizations'):
    """
    Generate all demand-specific visualizations.
    
    Parameters:
        model: Solved Gurobi model
        parameters: Dictionary of problem parameters
        save_html: Whether to save HTML files
        output_dir: Directory for HTML files
    
    Returns:
        dict: Dictionary of figures
    """
    import os
    
    if save_html:
        os.makedirs(output_dir, exist_ok=True)
    
    print("\n" + "="*70)
    print("GENERATING DEMAND-SPECIFIC VISUALIZATIONS")
    print("="*70)
    
    # Extract solution
    solution_data = {
        'a': {}, 'd': {}, 'P': {}, 'Q': {}, 
        'C': {}, 'C_in': {}, 'p': {}, 'p_in': {}
    }
    
    for v in model.getVars():
        if v.VarName.startswith('a_'):
            parts = v.VarName.split('_')
            solution_data['a'][int(parts[1]), int(parts[2])] = v
        elif v.VarName.startswith('d_'):
            parts = v.VarName.split('_')
            solution_data['d'][int(parts[1]), int(parts[2])] = v
        elif v.VarName.startswith('P_'):
            parts = v.VarName.split('_')
            solution_data['P'][int(parts[1]), int(parts[2])] = v
        elif v.VarName.startswith('Q_'):
            parts = v.VarName.split('_')
            solution_data['Q'][int(parts[1]), int(parts[2])] = v
        elif v.VarName.startswith('C_in_'):
            solution_data['C_in'][int(v.VarName.split('_')[2])] = v
        elif v.VarName.startswith('C_'):
            solution_data['C'][int(v.VarName.split('_')[1])] = v
        elif v.VarName.startswith('p_in_'):
            parts = v.VarName.split('_')
            solution_data['p_in'][int(parts[2]), int(parts[3])] = v
        elif v.VarName.startswith('p_'):
            parts = v.VarName.split('_')
            solution_data['p'][int(parts[1]), int(parts[2])] = v
    
    figures = {}
    
    # 1. Demand Heatmap
    print("\n1. Demand Heatmap...")
    figures['heatmap'] = create_demand_heatmap(parameters, solution_data)
    if save_html:
        figures['heatmap'].write_html(f"{output_dir}/demand_heatmap.html")
        print(f"   Saved to {output_dir}/demand_heatmap.html")
    
    # 2. Flight Ranking
    print("\n2. Flight Ranking Chart...")
    figures['ranking'] = create_flight_ranking_chart(parameters, solution_data)
    if save_html:
        figures['ranking'].write_html(f"{output_dir}/flight_ranking.html")
        print(f"   Saved to {output_dir}/flight_ranking.html")
    
    # 3. Train Productivity
    print("\n3. Train Productivity Chart...")
    figures['productivity'] = create_train_productivity_chart(parameters, solution_data)
    if save_html:
        figures['productivity'].write_html(f"{output_dir}/train_productivity.html")
        print(f"   Saved to {output_dir}/train_productivity.html")
    
    # 4. Connection Quality
    print("\n4. Connection Quality Scatter...")
    figures['quality'] = create_connection_quality_scatter(parameters, solution_data)
    if save_html:
        figures['quality'].write_html(f"{output_dir}/connection_quality.html")
        print(f"   Saved to {output_dir}/connection_quality.html")
    
    print("\n" + "="*70)
    print("ALL DEMAND VISUALIZATIONS GENERATED")
    print("="*70)
    
    return figures
