# -*- coding: utf-8 -*-
"""
Visualization Module for Air-Rail Synchronization
Provides comprehensive visualization tools including:
- Interactive Gantt charts for train schedules
- Synchronization quality metrics
- Demand coverage analysis
- Network flow visualization
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict


class AirRailVisualizer:
    """
    Comprehensive visualization suite for air-rail synchronization optimization results.
    """
    
    def __init__(self, solution_data, parameters):
        """
        Initialize visualizer with solution and parameter data.
        
        Parameters:
            solution_data (dict): Dictionary containing:
                - 'a': arrival time variables
                - 'd': departure time variables
                - 'P': outgoing flight synchronization variables
                - 'Q': incoming flight synchronization variables
                - 'C': outgoing flight coverage variables
                - 'C_in': incoming flight coverage variables
                - 'p': outgoing penalties
                - 'p_in': incoming penalties
            
            parameters (dict): Dictionary containing:
                - 'I', 'I_T': train sets
                - 'K_out', 'K_in': flight sets
                - 'S_i': train routes
                - 'ori_i', 'des_i': train origins/destinations
                - 'D_k', 'A_m': flight times
                - 'demand_out', 'demand_in': passenger demands
                - 'flight_station_out', 'flight_station_in': flight stations
                - 'station_coords': station coordinates
                - 'l_k', 'u_k', 'l_m', 'u_m': connection windows
        """
        self.sol = solution_data
        self.params = parameters
        
        # Extract frequently used parameters
        self.I = parameters['I']
        self.I_T = parameters['I_T']
        self.K_out = parameters['K_out']
        self.K_in = parameters['K_in']
        self.S_i = parameters['S_i']
        self.ori_i = parameters['ori_i']
        self.des_i = parameters['des_i']
        
    def create_gantt_chart(self, show_flights=True, show_connections=True):
        """
        Create interactive Gantt chart showing train schedules and flight connections.
        
        Parameters:
            show_flights (bool): Whether to show flight departure/arrival times
            show_connections (bool): Whether to show train-flight connections
        
        Returns:
            plotly.graph_objects.Figure
        """
        print("\n" + "="*70)
        print("CREATING GANTT CHART")
        print("="*70)
        
        # Prepare data for Gantt chart
        gantt_data = []
        
        # Add trains
        for i in self.I:
            route = self.S_i[i]
            origin = self.ori_i[i]
            dest = self.des_i[i]
            
            # Get departure from origin
            if (i, origin) in self.sol['d']:
                start_time = self.sol['d'][i, origin].X
            else:
                continue
                
            # Get arrival at destination
            if (i, dest) in self.sol['a']:
                end_time = self.sol['a'][i, dest].X
            else:
                continue
            
            # Create route description
            route_str = " → ".join([f"S{s}" for s in route])
            
            # Count synchronizations for this train
            sync_count_out = sum(1 for k in self.K_out 
                                if (i, k) in self.sol['P'] and self.sol['P'][i, k].X > 0.5)
            sync_count_in = sum(1 for m in self.K_in 
                               if (i, m) in self.sol['Q'] and self.sol['Q'][i, m].X > 0.5)
            total_sync = sync_count_out + sync_count_in
            
            gantt_data.append({
                'Task': f'Train {i}',
                'Start': start_time,
                'Finish': end_time,
                'Resource': 'Train',
                'Description': route_str,
                'Syncs': total_sync,
                'Type': 'Train'
            })
        
        # Add outgoing flights (departures)
        if show_flights:
            for k in self.K_out:
                dep_time = self.params['D_k'][k]
                station = self.params['flight_station_out'][k]
                demand = self.params['demand_out'][k]
                covered = self.sol['C'][k].X > 0.5
                
                # Flight shown as a short bar around departure time
                gantt_data.append({
                    'Task': f'Flight {k} (Out)',
                    'Start': dep_time - 5,
                    'Finish': dep_time + 5,
                    'Resource': 'Outgoing Flight',
                    'Description': f'Station {station}, Demand: {demand} pax',
                    'Syncs': sum(1 for i in self.I_T 
                                if (i, k) in self.sol['P'] and self.sol['P'][i, k].X > 0.5),
                    'Type': 'Flight_Out',
                    'Covered': covered
                })
        
            # Add incoming flights (arrivals)
            for m in self.K_in:
                arr_time = self.params['A_m'][m]
                station = self.params['flight_station_in'][m]
                demand = self.params['demand_in'][m]
                covered = self.sol['C_in'][m].X > 0.5
                
                gantt_data.append({
                    'Task': f'Flight {m} (In)',
                    'Start': arr_time - 5,
                    'Finish': arr_time + 5,
                    'Resource': 'Incoming Flight',
                    'Description': f'Station {station}, Demand: {demand} pax',
                    'Syncs': sum(1 for i in self.I_T 
                                if (i, m) in self.sol['Q'] and self.sol['Q'][i, m].X > 0.5),
                    'Type': 'Flight_In',
                    'Covered': covered
                })
        
        # Create DataFrame
        df = pd.DataFrame(gantt_data)
        
        # Sort by start time
        df = df.sort_values('Start')
        
        # Create figure
        fig = go.Figure()
        
        # Color mapping
        color_map = {
            'Train': '#1f77b4',
            'Outgoing Flight': '#ff7f0e',
            'Incoming Flight': '#2ca02c'
        }
        
        # Add bars for each resource type
        for resource in ['Train', 'Outgoing Flight', 'Incoming Flight']:
            df_resource = df[df['Resource'] == resource]
            
            for idx, row in df_resource.iterrows():
                # Determine color based on coverage for flights
                if resource in ['Outgoing Flight', 'Incoming Flight']:
                    color = color_map[resource] if row.get('Covered', True) else '#d3d3d3'
                    line_width = 3 if row.get('Covered', True) else 1
                else:
                    # Color intensity for trains based on synchronizations
                    if row['Syncs'] > 0:
                        color = color_map[resource]
                        line_width = 3
                    else:
                        color = '#a8a8a8'
                        line_width = 1
                
                # Hover text
                hover_text = (
                    f"<b>{row['Task']}</b><br>"
                    f"{row['Description']}<br>"
                    f"Start: {self._format_time(row['Start'])}<br>"
                    f"End: {self._format_time(row['Finish'])}<br>"
                    f"Duration: {row['Finish'] - row['Start']:.1f} min<br>"
                    f"Synchronizations: {row['Syncs']}"
                )
                
                fig.add_trace(go.Bar(
                    x=[row['Finish'] - row['Start']],
                    y=[row['Task']],
                    base=row['Start'],
                    orientation='h',
                    marker=dict(
                        color=color,
                        line=dict(color=color, width=line_width)
                    ),
                    name=resource,
                    legendgroup=resource,
                    showlegend=idx == df_resource.index[0],  # Only show legend once per group
                    hovertemplate=hover_text + '<extra></extra>'
                ))
        
        # Update layout
        fig.update_layout(
            title=dict(
                text='<b>Train Schedule Gantt Chart with Flight Connections</b>',
                x=0.5,
                xanchor='center',
                font=dict(size=20)
            ),
            xaxis=dict(
                title='Time (minutes from midnight)',
                tickmode='linear',
                tick0=0,
                dtick=60,
                gridcolor='lightgray',
                showgrid=True
            ),
            yaxis=dict(
                title='',
                autorange='reversed',
                showgrid=False
            ),
            barmode='overlay',
            height=max(600, len(df) * 20),
            hovermode='closest',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            ),
            plot_bgcolor='white'
        )
        
        # Add time markers
        time_markers = list(range(0, 1440, 180))  # Every 3 hours
        for t in time_markers:
            fig.add_vline(
                x=t, 
                line_dash="dash", 
                line_color="gray", 
                opacity=0.3,
                annotation_text=self._format_time(t),
                annotation_position="top"
            )
        
        print(f"Gantt chart created with {len(df)} items")
        return fig
    
    def create_synchronization_network(self):
        """
        Create network visualization showing train-flight connections.
        
        Returns:
            plotly.graph_objects.Figure
        """
        print("\n" + "="*70)
        print("CREATING SYNCHRONIZATION NETWORK")
        print("="*70)
        
        # Create subplots for each station
        stations = set(self.params['flight_station_out'].values()) | \
                   set(self.params['flight_station_in'].values())
        stations = sorted(list(stations))
        
        n_stations = len(stations)
        fig = make_subplots(
            rows=1, cols=n_stations,
            subplot_titles=[f'<b>Station {s}</b>' for s in stations],
            horizontal_spacing=0.05
        )
        
        for idx, station in enumerate(stations, 1):
            # Get trains serving this station
            trains_at_station = [i for i in self.I if station in self.S_i[i]]
            
            # Get flights at this station
            flights_out_at_station = [k for k in self.K_out 
                                     if self.params['flight_station_out'][k] == station]
            flights_in_at_station = [m for m in self.K_in 
                                    if self.params['flight_station_in'][m] == station]
            
            # Create node positions
            n_trains = len(trains_at_station)
            n_flights_out = len(flights_out_at_station)
            n_flights_in = len(flights_in_at_station)
            
            # Train nodes on the left
            train_y = np.linspace(0, 1, n_trains) if n_trains > 0 else []
            train_x = [0.2] * n_trains
            
            # Outgoing flight nodes on the right top
            flight_out_y = np.linspace(0.6, 1, n_flights_out) if n_flights_out > 0 else []
            flight_out_x = [0.8] * n_flights_out
            
            # Incoming flight nodes on the right bottom
            flight_in_y = np.linspace(0, 0.4, n_flights_in) if n_flights_in > 0 else []
            flight_in_x = [0.8] * n_flights_in
            
            # Draw connections (edges)
            for i_idx, i in enumerate(trains_at_station):
                # Outgoing connections
                for k_idx, k in enumerate(flights_out_at_station):
                    if (i, k) in self.sol['P'] and self.sol['P'][i, k].X > 0.5:
                        # Draw connection line
                        fig.add_trace(go.Scatter(
                            x=[train_x[i_idx], flight_out_x[k_idx]],
                            y=[train_y[i_idx], flight_out_y[k_idx]],
                            mode='lines',
                            line=dict(color='#1f77b4', width=2),
                            showlegend=False,
                            hoverinfo='skip'
                        ), row=1, col=idx)
                
                # Incoming connections
                for m_idx, m in enumerate(flights_in_at_station):
                    if (i, m) in self.sol['Q'] and self.sol['Q'][i, m].X > 0.5:
                        # Draw connection line
                        fig.add_trace(go.Scatter(
                            x=[flight_in_x[m_idx], train_x[i_idx]],
                            y=[flight_in_y[m_idx], train_y[i_idx]],
                            mode='lines',
                            line=dict(color='#2ca02c', width=2),
                            showlegend=False,
                            hoverinfo='skip'
                        ), row=1, col=idx)
            
            # Draw train nodes
            for i_idx, i in enumerate(trains_at_station):
                sync_count = sum(1 for k in flights_out_at_station 
                               if (i, k) in self.sol['P'] and self.sol['P'][i, k].X > 0.5)
                sync_count += sum(1 for m in flights_in_at_station 
                                if (i, m) in self.sol['Q'] and self.sol['Q'][i, m].X > 0.5)
                
                fig.add_trace(go.Scatter(
                    x=[train_x[i_idx]],
                    y=[train_y[i_idx]],
                    mode='markers+text',
                    marker=dict(size=20, color='#1f77b4', symbol='square'),
                    text=[f'T{i}'],
                    textposition='middle left',
                    textfont=dict(size=10, color='white'),
                    hovertemplate=f'<b>Train {i}</b><br>Connections: {sync_count}<extra></extra>',
                    showlegend=False
                ), row=1, col=idx)
            
            # Draw outgoing flight nodes
            for k_idx, k in enumerate(flights_out_at_station):
                covered = self.sol['C'][k].X > 0.5
                color = '#ff7f0e' if covered else '#d3d3d3'
                demand = self.params['demand_out'][k]
                
                fig.add_trace(go.Scatter(
                    x=[flight_out_x[k_idx]],
                    y=[flight_out_y[k_idx]],
                    mode='markers+text',
                    marker=dict(size=15, color=color, symbol='triangle-up'),
                    text=[f'F{k}'],
                    textposition='middle right',
                    textfont=dict(size=8),
                    hovertemplate=f'<b>Flight {k} (Out)</b><br>Demand: {demand} pax<br>Covered: {covered}<extra></extra>',
                    showlegend=False
                ), row=1, col=idx)
            
            # Draw incoming flight nodes
            for m_idx, m in enumerate(flights_in_at_station):
                covered = self.sol['C_in'][m].X > 0.5
                color = '#2ca02c' if covered else '#d3d3d3'
                demand = self.params['demand_in'][m]
                
                fig.add_trace(go.Scatter(
                    x=[flight_in_x[m_idx]],
                    y=[flight_in_y[m_idx]],
                    mode='markers+text',
                    marker=dict(size=15, color=color, symbol='triangle-down'),
                    text=[f'F{m}'],
                    textposition='middle right',
                    textfont=dict(size=8),
                    hovertemplate=f'<b>Flight {m} (In)</b><br>Demand: {demand} pax<br>Covered: {covered}<extra></extra>',
                    showlegend=False
                ), row=1, col=idx)
            
            # Update axes for this subplot
            fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False, row=1, col=idx)
            fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False, row=1, col=idx)
        
        fig.update_layout(
            title=dict(
                text='<b>Train-Flight Synchronization Network by Station</b>',
                x=0.5,
                xanchor='center',
                font=dict(size=20)
            ),
            height=600,
            showlegend=False,
            plot_bgcolor='white'
        )
        
        print(f"Network visualization created for {n_stations} stations")
        return fig
    
    def create_demand_coverage_analysis(self):
        """
        Create comprehensive demand coverage visualization.
        
        Returns:
            plotly.graph_objects.Figure with multiple subplots
        """
        print("\n" + "="*70)
        print("CREATING DEMAND COVERAGE ANALYSIS")
        print("="*70)
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                '<b>Outgoing Flight Demand vs Coverage</b>',
                '<b>Incoming Flight Demand vs Coverage</b>',
                '<b>Demand Coverage by Time of Day</b>',
                '<b>Cumulative Passenger Coverage</b>'
            ),
            specs=[[{'type': 'bar'}, {'type': 'bar'}],
                   [{'type': 'scatter'}, {'type': 'scatter'}]],
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        # ========================================
        # Subplot 1: Outgoing Flight Demand vs Coverage
        # ========================================
        flights_out_data = []
        for k in self.K_out:
            covered = self.sol['C'][k].X > 0.5
            demand = self.params['demand_out'][k]
            served = demand if covered else 0
            
            flights_out_data.append({
                'flight': k,
                'demand': demand,
                'served': served,
                'covered': covered,
                'time': self.params['D_k'][k],
                'station': self.params['flight_station_out'][k]
            })
        
        df_out = pd.DataFrame(flights_out_data).sort_values('time')
        
        # Stacked bar: served (green) + unserved (red)
        fig.add_trace(go.Bar(
            x=df_out['flight'],
            y=df_out['served'],
            name='Covered Demand',
            marker_color='#2ca02c',
            legendgroup='out',
            hovertemplate='Flight %{x}<br>Served: %{y} pax<extra></extra>'
        ), row=1, col=1)
        
        fig.add_trace(go.Bar(
            x=df_out['flight'],
            y=df_out['demand'] - df_out['served'],
            name='Uncovered Demand',
            marker_color='#d62728',
            legendgroup='out',
            hovertemplate='Flight %{x}<br>Unserved: %{y} pax<extra></extra>'
        ), row=1, col=1)
        
        # ========================================
        # Subplot 2: Incoming Flight Demand vs Coverage
        # ========================================
        flights_in_data = []
        for m in self.K_in:
            covered = self.sol['C_in'][m].X > 0.5
            demand = self.params['demand_in'][m]
            served = demand if covered else 0
            
            flights_in_data.append({
                'flight': m,
                'demand': demand,
                'served': served,
                'covered': covered,
                'time': self.params['A_m'][m],
                'station': self.params['flight_station_in'][m]
            })
        
        df_in = pd.DataFrame(flights_in_data).sort_values('time')
        
        fig.add_trace(go.Bar(
            x=df_in['flight'],
            y=df_in['served'],
            name='Covered Demand',
            marker_color='#2ca02c',
            legendgroup='in',
            showlegend=False,
            hovertemplate='Flight %{x}<br>Served: %{y} pax<extra></extra>'
        ), row=1, col=2)
        
        fig.add_trace(go.Bar(
            x=df_in['flight'],
            y=df_in['demand'] - df_in['served'],
            name='Uncovered Demand',
            marker_color='#d62728',
            legendgroup='in',
            showlegend=False,
            hovertemplate='Flight %{x}<br>Unserved: %{y} pax<extra></extra>'
        ), row=1, col=2)
        
        # ========================================
        # Subplot 3: Demand Coverage by Time of Day
        # ========================================
        # Bin flights by hour
        time_bins = list(range(0, 1440, 60))  # Hourly bins
        
        outgoing_by_hour = defaultdict(lambda: {'total': 0, 'served': 0})
        for _, row in df_out.iterrows():
            hour_bin = int(row['time'] // 60) * 60
            outgoing_by_hour[hour_bin]['total'] += row['demand']
            outgoing_by_hour[hour_bin]['served'] += row['served']
        
        incoming_by_hour = defaultdict(lambda: {'total': 0, 'served': 0})
        for _, row in df_in.iterrows():
            hour_bin = int(row['time'] // 60) * 60
            incoming_by_hour[hour_bin]['total'] += row['demand']
            incoming_by_hour[hour_bin]['served'] += row['served']
        
        hours = sorted(set(list(outgoing_by_hour.keys()) + list(incoming_by_hour.keys())))
        
        fig.add_trace(go.Scatter(
            x=[self._format_time(h) for h in hours],
            y=[outgoing_by_hour[h]['served'] / outgoing_by_hour[h]['total'] * 100 
               if outgoing_by_hour[h]['total'] > 0 else 0 for h in hours],
            mode='lines+markers',
            name='Outgoing',
            line=dict(color='#ff7f0e', width=3),
            marker=dict(size=8),
            hovertemplate='%{x}<br>Coverage: %{y:.1f}%<extra></extra>'
        ), row=2, col=1)
        
        fig.add_trace(go.Scatter(
            x=[self._format_time(h) for h in hours],
            y=[incoming_by_hour[h]['served'] / incoming_by_hour[h]['total'] * 100 
               if incoming_by_hour[h]['total'] > 0 else 0 for h in hours],
            mode='lines+markers',
            name='Incoming',
            line=dict(color='#2ca02c', width=3),
            marker=dict(size=8),
            hovertemplate='%{x}<br>Coverage: %{y:.1f}%<extra></extra>'
        ), row=2, col=1)
        
        # ========================================
        # Subplot 4: Cumulative Passenger Coverage
        # ========================================
        # Sort all flights by time
        all_flights = []
        
        for k in self.K_out:
            all_flights.append({
                'time': self.params['D_k'][k],
                'demand': self.params['demand_out'][k],
                'served': self.params['demand_out'][k] if self.sol['C'][k].X > 0.5 else 0,
                'type': 'out'
            })
        
        for m in self.K_in:
            all_flights.append({
                'time': self.params['A_m'][m],
                'demand': self.params['demand_in'][m],
                'served': self.params['demand_in'][m] if self.sol['C_in'][m].X > 0.5 else 0,
                'type': 'in'
            })
        
        all_flights.sort(key=lambda x: x['time'])
        
        cumulative_demand = np.cumsum([f['demand'] for f in all_flights])
        cumulative_served = np.cumsum([f['served'] for f in all_flights])
        times = [f['time'] for f in all_flights]
        
        fig.add_trace(go.Scatter(
            x=[self._format_time(t) for t in times],
            y=cumulative_demand,
            mode='lines',
            name='Total Demand',
            line=dict(color='gray', width=2, dash='dash'),
            fill='tonexty',
            hovertemplate='Time: %{x}<br>Total: %{y} pax<extra></extra>'
        ), row=2, col=2)
        
        fig.add_trace(go.Scatter(
            x=[self._format_time(t) for t in times],
            y=cumulative_served,
            mode='lines',
            name='Served Demand',
            line=dict(color='#2ca02c', width=3),
            fill='tozeroy',
            hovertemplate='Time: %{x}<br>Served: %{y} pax<extra></extra>'
        ), row=2, col=2)
        
        # Update axes
        fig.update_xaxes(title_text="Flight ID", row=1, col=1)
        fig.update_xaxes(title_text="Flight ID", row=1, col=2)
        fig.update_xaxes(title_text="Time of Day", row=2, col=1, tickangle=-45)
        fig.update_xaxes(title_text="Time of Day", row=2, col=2, tickangle=-45)
        
        fig.update_yaxes(title_text="Passengers", row=1, col=1)
        fig.update_yaxes(title_text="Passengers", row=1, col=2)
        fig.update_yaxes(title_text="Coverage (%)", row=2, col=1)
        fig.update_yaxes(title_text="Cumulative Passengers", row=2, col=2)
        
        # Update layout
        fig.update_layout(
            title=dict(
                text='<b>Demand Coverage Analysis Dashboard</b>',
                x=0.5,
                xanchor='center',
                font=dict(size=22)
            ),
            height=900,
            barmode='stack',
            hovermode='closest',
            showlegend=True,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.15,
                xanchor='center',
                x=0.5
            )
        )
        
        # Calculate statistics
        total_demand = sum(self.params['demand_out'].values()) + sum(self.params['demand_in'].values())
        total_served = sum(df_out['served']) + sum(df_in['served'])
        coverage_rate = (total_served / total_demand * 100) if total_demand > 0 else 0
        
        print(f"Total demand: {total_demand} passengers")
        print(f"Total served: {total_served} passengers")
        print(f"Coverage rate: {coverage_rate:.1f}%")
        
        return fig
    
    def create_quality_metrics_dashboard(self):
        """
        Create dashboard showing key quality metrics.
        
        Returns:
            plotly.graph_objects.Figure
        """
        print("\n" + "="*70)
        print("CREATING QUALITY METRICS DASHBOARD")
        print("="*70)
        
        # Calculate metrics
        metrics = self._calculate_metrics()
        
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                '<b>Synchronization Count</b>',
                '<b>Flight Coverage</b>',
                '<b>Transfer Time Distribution</b>',
                '<b>Penalty Distribution</b>',
                '<b>Station-wise Performance</b>',
                '<b>Train Utilization</b>'
            ),
            specs=[[{'type': 'indicator'}, {'type': 'indicator'}],
                   [{'type': 'histogram'}, {'type': 'box'}],
                   [{'type': 'bar'}, {'type': 'bar'}]],
            vertical_spacing=0.12,
            horizontal_spacing=0.15
        )
        
        # ========================================
        # KPI 1: Synchronization Count
        # ========================================
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=metrics['total_synchronizations'],
            title={'text': "Total<br>Synchronizations"},
            delta={'reference': metrics['total_flights'] * 0.5, 'relative': False},
            domain={'x': [0, 1], 'y': [0, 1]}
        ), row=1, col=1)
        
        # ========================================
        # KPI 2: Flight Coverage
        # ========================================
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=metrics['coverage_rate'],
            title={'text': "Coverage<br>Rate (%)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#2ca02c"},
                'steps': [
                    {'range': [0, 50], 'color': "#ffe6e6"},
                    {'range': [50, 75], 'color': "#fff4e6"},
                    {'range': [75, 100], 'color': "#e6f7e6"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            },
            domain={'x': [0, 1], 'y': [0, 1]}
        ), row=1, col=2)
        
        # ========================================
        # Subplot 3: Transfer Time Distribution
        # ========================================
        transfer_times = metrics['transfer_times']
        
        fig.add_trace(go.Histogram(
            x=transfer_times,
            nbinsx=20,
            marker_color='#1f77b4',
            name='Transfer Times',
            hovertemplate='Transfer Time: %{x:.0f} min<br>Count: %{y}<extra></extra>'
        ), row=2, col=1)
        
        # Add vertical lines for min/max acceptable transfer times
        fig.add_vline(x=20, line_dash="dash", line_color="red", 
                     annotation_text="Min", row=2, col=1)
        fig.add_vline(x=70, line_dash="dash", line_color="red", 
                     annotation_text="Max", row=2, col=1)
        
        # ========================================
        # Subplot 4: Penalty Distribution
        # ========================================
        penalties = metrics['penalties']
        
        fig.add_trace(go.Box(
            y=penalties,
            name='Penalties',
            marker_color='#ff7f0e',
            boxmean='sd',
            hovertemplate='Penalty: %{y:.2f}<extra></extra>'
        ), row=2, col=2)
        
        # ========================================
        # Subplot 5: Station-wise Performance
        # ========================================
        station_metrics = metrics['station_metrics']
        
        stations = list(station_metrics.keys())
        sync_counts = [station_metrics[s]['synchronizations'] for s in stations]
        demands = [station_metrics[s]['demand_served'] for s in stations]
        
        fig.add_trace(go.Bar(
            x=[f'Station {s}' for s in stations],
            y=sync_counts,
            name='Synchronizations',
            marker_color='#1f77b4',
            yaxis='y',
            hovertemplate='Station %{x}<br>Syncs: %{y}<extra></extra>'
        ), row=3, col=1)
        
        fig.add_trace(go.Bar(
            x=[f'Station {s}' for s in stations],
            y=demands,
            name='Demand Served',
            marker_color='#2ca02c',
            yaxis='y2',
            hovertemplate='Station %{x}<br>Passengers: %{y}<extra></extra>'
        ), row=3, col=1)
        
        # ========================================
        # Subplot 6: Train Utilization
        # ========================================
        train_metrics = metrics['train_metrics']
        
        trains_sorted = sorted(train_metrics.keys(), 
                              key=lambda x: train_metrics[x]['synchronizations'], 
                              reverse=True)[:15]  # Top 15 trains
        
        fig.add_trace(go.Bar(
            x=[f'T{i}' for i in trains_sorted],
            y=[train_metrics[i]['synchronizations'] for i in trains_sorted],
            marker_color='#9467bd',
            hovertemplate='Train %{x}<br>Syncs: %{y}<extra></extra>'
        ), row=3, col=2)
        
        # Update axes
        fig.update_xaxes(title_text="Transfer Time (min)", row=2, col=1)
        fig.update_xaxes(title_text="", row=2, col=2, showticklabels=False)
        fig.update_xaxes(title_text="Station", row=3, col=1)
        fig.update_xaxes(title_text="Train", row=3, col=2)
        
        fig.update_yaxes(title_text="Count", row=2, col=1)
        fig.update_yaxes(title_text="Penalty Value", row=2, col=2)
        fig.update_yaxes(title_text="Count", row=3, col=1)
        fig.update_yaxes(title_text="Synchronizations", row=3, col=2)
        
        # Add secondary y-axis for station plot
        fig.update_yaxes(title_text="Passengers", secondary_y=True, row=3, col=1)
        
        # Update layout
        fig.update_layout(
            title=dict(
                text='<b>Synchronization Quality Metrics Dashboard</b>',
                x=0.5,
                xanchor='center',
                font=dict(size=22)
            ),
            height=1200,
            showlegend=True,
            hovermode='closest'
        )
        
        print("Quality metrics dashboard created")
        return fig
    
    def create_time_space_diagram(self):
        """
        Create time-space diagram showing train trajectories.
        
        Returns:
            plotly.graph_objects.Figure
        """
        print("\n" + "="*70)
        print("CREATING TIME-SPACE DIAGRAM")
        print("="*70)
        
        fig = go.Figure()
        
        # Get unique stations and sort them
        all_stations = set()
        for route in self.S_i.values():
            all_stations.update(route)
        stations_sorted = sorted(list(all_stations))
        
        # Create a mapping from station to y-coordinate
        station_y = {s: idx for idx, s in enumerate(stations_sorted)}
        
        # Plot each train's trajectory
        for i in self.I:
            route = self.S_i[i]
            times = []
            positions = []
            
            for s in route:
                # Add arrival time if not origin
                if s != self.ori_i[i] and (i, s) in self.sol['a']:
                    times.append(self.sol['a'][i, s].X)
                    positions.append(station_y[s])
                
                # Add departure time if not destination
                if s != self.des_i[i] and (i, s) in self.sol['d']:
                    times.append(self.sol['d'][i, s].X)
                    positions.append(station_y[s])
            
            # Plot train trajectory
            if len(times) > 0:
                # Count synchronizations
                sync_count = sum(1 for k in self.K_out 
                               if (i, k) in self.sol['P'] and self.sol['P'][i, k].X > 0.5)
                sync_count += sum(1 for m in self.K_in 
                                if (i, m) in self.sol['Q'] and self.sol['Q'][i, m].X > 0.5)
                
                color = '#1f77b4' if sync_count > 0 else '#d3d3d3'
                width = 2 if sync_count > 0 else 1
                
                route_str = " → ".join([f"S{s}" for s in route])
                
                fig.add_trace(go.Scatter(
                    x=times,
                    y=positions,
                    mode='lines+markers',
                    name=f'Train {i}',
                    line=dict(color=color, width=width),
                    marker=dict(size=6),
                    hovertemplate=f'<b>Train {i}</b><br>Route: {route_str}<br>Time: %{{x:.0f}} min<br>Syncs: {sync_count}<extra></extra>'
                ))
        
        # Update layout
        fig.update_layout(
            title=dict(
                text='<b>Time-Space Diagram</b>',
                x=0.5,
                xanchor='center',
                font=dict(size=20)
            ),
            xaxis=dict(
                title='Time (minutes from midnight)',
                gridcolor='lightgray',
                showgrid=True
            ),
            yaxis=dict(
                title='Station',
                tickmode='array',
                tickvals=list(range(len(stations_sorted))),
                ticktext=[f'Station {s}' for s in stations_sorted],
                gridcolor='lightgray',
                showgrid=True
            ),
            height=600,
            showlegend=False,
            hovermode='closest',
            plot_bgcolor='white'
        )
        
        print(f"Time-space diagram created with {len(self.I)} trains")
        return fig
    
    def _calculate_metrics(self):
        """Calculate various quality metrics."""
        metrics = {}
        
        # Total synchronizations
        sync_out = sum(1 for i in self.I_T for k in self.K_out 
                      if (i, k) in self.sol['P'] and self.sol['P'][i, k].X > 0.5)
        sync_in = sum(1 for i in self.I_T for m in self.K_in 
                     if (i, m) in self.sol['Q'] and self.sol['Q'][i, m].X > 0.5)
        metrics['total_synchronizations'] = sync_out + sync_in
        
        # Total flights
        metrics['total_flights'] = len(self.K_out) + len(self.K_in)
        
        # Coverage rate
        flights_covered = sum(1 for k in self.K_out if self.sol['C'][k].X > 0.5)
        flights_covered += sum(1 for m in self.K_in if self.sol['C_in'][m].X > 0.5)
        metrics['coverage_rate'] = (flights_covered / metrics['total_flights'] * 100) if metrics['total_flights'] > 0 else 0
        
        # Transfer times
        transfer_times = []
        for i in self.I_T:
            for k in self.K_out:
                if (i, k) in self.sol['P'] and self.sol['P'][i, k].X > 0.5:
                    st_k = self.params['flight_station_out'][k]
                    if (i, st_k) in self.sol['a']:
                        transfer_time = self.params['D_k'][k] - self.sol['a'][i, st_k].X
                        transfer_times.append(transfer_time)
            
            for m in self.K_in:
                if (i, m) in self.sol['Q'] and self.sol['Q'][i, m].X > 0.5:
                    st_m = self.params['flight_station_in'][m]
                    if (i, st_m) in self.sol['d']:
                        transfer_time = self.sol['d'][i, st_m].X - self.params['A_m'][m]
                        transfer_times.append(transfer_time)
        
        metrics['transfer_times'] = transfer_times
        
        # Penalties
        penalties = []
        for i in self.I_T:
            for k in self.K_out:
                if (i, k) in self.sol['p'] and self.sol['P'][i, k].X > 0.5:
                    penalties.append(self.sol['p'][i, k].X)
            for m in self.K_in:
                if (i, m) in self.sol['p_in'] and self.sol['Q'][i, m].X > 0.5:
                    penalties.append(self.sol['p_in'][i, m].X)
        
        metrics['penalties'] = penalties if penalties else [0]
        
        # Station-wise metrics
        station_metrics = {}
        stations = set(self.params['flight_station_out'].values()) | \
                   set(self.params['flight_station_in'].values())
        
        for station in stations:
            sync_count = 0
            demand_served = 0
            
            # Outgoing flights
            for k in self.K_out:
                if self.params['flight_station_out'][k] == station:
                    if self.sol['C'][k].X > 0.5:
                        demand_served += self.params['demand_out'][k]
                        sync_count += sum(1 for i in self.I_T 
                                        if (i, k) in self.sol['P'] and self.sol['P'][i, k].X > 0.5)
            
            # Incoming flights
            for m in self.K_in:
                if self.params['flight_station_in'][m] == station:
                    if self.sol['C_in'][m].X > 0.5:
                        demand_served += self.params['demand_in'][m]
                        sync_count += sum(1 for i in self.I_T 
                                        if (i, m) in self.sol['Q'] and self.sol['Q'][i, m].X > 0.5)
            
            station_metrics[station] = {
                'synchronizations': sync_count,
                'demand_served': demand_served
            }
        
        metrics['station_metrics'] = station_metrics
        
        # Train utilization
        train_metrics = {}
        for i in self.I:
            sync_count = sum(1 for k in self.K_out 
                           if (i, k) in self.sol['P'] and self.sol['P'][i, k].X > 0.5)
            sync_count += sum(1 for m in self.K_in 
                            if (i, m) in self.sol['Q'] and self.sol['Q'][i, m].X > 0.5)
            
            train_metrics[i] = {'synchronizations': sync_count}
        
        metrics['train_metrics'] = train_metrics
        
        return metrics
    
    def _format_time(self, minutes):
        """Convert minutes from midnight to HH:MM format."""
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours:02d}:{mins:02d}"
    
    def generate_all_visualizations(self, save_html=True, output_dir='visualizations'):
        """
        Generate all visualizations and optionally save them as HTML files.
        
        Parameters:
            save_html (bool): Whether to save visualizations as HTML files
            output_dir (str): Directory to save HTML files
        
        Returns:
            dict: Dictionary of all figures
        """
        import os
        
        if save_html:
            os.makedirs(output_dir, exist_ok=True)
        
        print("\n" + "="*70)
        print("GENERATING ALL VISUALIZATIONS")
        print("="*70)
        
        figures = {}
        
        # 1. Gantt Chart
        print("\n1. Gantt Chart...")
        figures['gantt'] = self.create_gantt_chart()
        if save_html:
            figures['gantt'].write_html(f"{output_dir}/gantt_chart.html")
            print(f"   Saved to {output_dir}/gantt_chart.html")
        
        # 2. Synchronization Network
        print("\n2. Synchronization Network...")
        figures['network'] = self.create_synchronization_network()
        if save_html:
            figures['network'].write_html(f"{output_dir}/synchronization_network.html")
            print(f"   Saved to {output_dir}/synchronization_network.html")
        
        # 3. Demand Coverage Analysis
        print("\n3. Demand Coverage Analysis...")
        figures['demand'] = self.create_demand_coverage_analysis()
        if save_html:
            figures['demand'].write_html(f"{output_dir}/demand_coverage.html")
            print(f"   Saved to {output_dir}/demand_coverage.html")
        
        # 4. Quality Metrics Dashboard
        print("\n4. Quality Metrics Dashboard...")
        figures['metrics'] = self.create_quality_metrics_dashboard()
        if save_html:
            figures['metrics'].write_html(f"{output_dir}/quality_metrics.html")
            print(f"   Saved to {output_dir}/quality_metrics.html")
        
        # 5. Time-Space Diagram
        print("\n5. Time-Space Diagram...")
        figures['timespace'] = self.create_time_space_diagram()
        if save_html:
            figures['timespace'].write_html(f"{output_dir}/time_space_diagram.html")
            print(f"   Saved to {output_dir}/time_space_diagram.html")
        
        print("\n" + "="*70)
        print("ALL VISUALIZATIONS GENERATED SUCCESSFULLY")
        print("="*70)
        
        return figures


# ========================================
# CONVENIENCE FUNCTION
# ========================================

def visualize_solution(model, parameters, save_html=True, output_dir='visualizations'):
    """
    Convenience function to visualize solution from Gurobi model.
    
    Parameters:
        model: Gurobi model with solved solution
        parameters: Dictionary of problem parameters
        save_html: Whether to save HTML files
        output_dir: Directory for HTML files
    
    Returns:
        dict: Dictionary of all figures
    """
    # Extract solution from model
    solution_data = {
        'a': {},
        'd': {},
        'P': {},
        'Q': {},
        'C': {},
        'C_in': {},
        'p': {},
        'p_in': {}
    }
    
    # Extract variables from model
    for v in model.getVars():
        if v.VarName.startswith('a_'):
            parts = v.VarName.split('_')
            i, s = int(parts[1]), int(parts[2])
            solution_data['a'][i, s] = v
        elif v.VarName.startswith('d_'):
            parts = v.VarName.split('_')
            i, s = int(parts[1]), int(parts[2])
            solution_data['d'][i, s] = v
        elif v.VarName.startswith('P_'):
            parts = v.VarName.split('_')
            i, k = int(parts[1]), int(parts[2])
            solution_data['P'][i, k] = v
        elif v.VarName.startswith('Q_'):
            parts = v.VarName.split('_')
            i, m = int(parts[1]), int(parts[2])
            solution_data['Q'][i, m] = v
        elif v.VarName.startswith('C_in_'):
            m = int(v.VarName.split('_')[2])
            solution_data['C_in'][m] = v
        elif v.VarName.startswith('C_'):
            k = int(v.VarName.split('_')[1])
            solution_data['C'][k] = v
        elif v.VarName.startswith('p_in_'):
            parts = v.VarName.split('_')
            i, m = int(parts[2]), int(parts[3])
            solution_data['p_in'][i, m] = v
        elif v.VarName.startswith('p_'):
            parts = v.VarName.split('_')
            i, k = int(parts[1]), int(parts[2])
            solution_data['p'][i, k] = v
    
    # Create visualizer
    visualizer = AirRailVisualizer(solution_data, parameters)
    
    # Generate all visualizations
    return visualizer.generate_all_visualizations(save_html=save_html, output_dir=output_dir)
