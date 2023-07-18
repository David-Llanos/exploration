import os
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.io as pio
import base64
import dash_table
from dash_dangerously_set_inner_html import DangerouslySetInnerHTML
import urllib.parse
import io

# define the location of the csv files
data_folder = 'C:/Users/drlla/Documents/exploration/data/'

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Label('Select File'),
    dcc.Dropdown(
        id='file-dropdown',
        options=[{'label': i, 'value': i} for i in os.listdir(data_folder) if i.endswith('.csv')]
    ),
    html.Label('Select Graph Type'),
    dcc.Dropdown(id='graph-dropdown'),
    html.Label('Select X Axis'),
    dcc.Dropdown(id='xaxis-dropdown'),
    html.Label('Select Y Axis'),
    dcc.Dropdown(id='yaxis-dropdown'),
    dcc.Graph(id='graph'),
    html.Label('Summary Statistics'),
    dash_table.DataTable(id='summary-statistics'),
    html.A('Download Data', id='download-link', download="rawdata.html", href="", target="_blank")
])

@app.callback(
    Output('graph-dropdown', 'options'),
    Input('file-dropdown', 'value')
)
def update_graph_dropdown(selected_file):
    if selected_file:
        return [{'label': 'Line', 'value': 'line'},
                {'label': 'Scatter', 'value': 'scatter'},
                {'label': 'Box', 'value': 'box'}]
    return []

@app.callback(
    [Output('xaxis-dropdown', 'options'),
     Output('yaxis-dropdown', 'options'),
     Output('xaxis-dropdown', 'style')],
    [Input('file-dropdown', 'value'),
     Input('graph-dropdown', 'value')]
)
def update_axis_dropdowns(selected_file, selected_graph):
    if selected_file and selected_graph:
        df = pd.read_csv(data_folder + selected_file)
        options = [{'label': i, 'value': i} for i in df.columns if df[i].dtype in ['int64', 'float64']]
        if selected_graph != 'box':
            return options, options, {'display': 'block'}
        return [], options, {'display': 'none'}
    return [], [], {'display': 'none'}

@app.callback(
    Output('graph', 'figure'),
    [Input('file-dropdown', 'value'),
     Input('graph-dropdown', 'value'),
     Input('xaxis-dropdown', 'value'),
     Input('yaxis-dropdown', 'value')]
)
def update_graph(selected_file, selected_graph, x_axis, y_axis):
    if all([selected_file, selected_graph, y_axis]):
        df = pd.read_csv(data_folder + selected_file)
        if selected_graph == 'line':
            fig = px.line(df, x=x_axis, y=y_axis)
        elif selected_graph == 'scatter':
            fig = px.scatter(df, x=x_axis, y=y_axis)
        elif selected_graph == 'box':
            fig = px.box(df, y=y_axis)
        else:
            fig = {}

        return fig
    return {}



@app.callback(
    Output('summary-statistics', 'data'),
    Output('summary-statistics', 'columns'),
    [Input('file-dropdown', 'value')]
)
def update_summary_statistics(selected_file):
    if selected_file:
        df = pd.read_csv(data_folder + selected_file)  # Assuming you have this folder and files
        summary_stats = df.describe().reset_index()

        columns = [{"name": i, "id": i} for i in summary_stats.columns]
        data = summary_stats.to_dict('records')

        return data, columns
    else:
        return dash.no_update, dash.no_update  # If no file is selected, don't update

@app.callback(
    Output('download-link', 'href'),
    [Input('summary-statistics', 'data'),
     Input('summary-statistics', 'columns'),
     Input('graph', 'figure')]
)
def update_download_link(table_data, table_columns, figure):
    # only check if table_data and table_columns are present since figure can be an empty dictionary
    if table_data and table_columns:
        df = pd.DataFrame(table_data, columns=[col['name'] for col in table_columns])

        # Create an HTML table from DataFrame
        html_table = df.to_html(index=False)

        # Convert Plotly graph to static PNG image
        img_tag = ''
        if 'data' in figure:  # make sure there's actual data in the figure
            figure_in_base64 = pio.to_image(figure, format='png')
            figure_in_base64 = base64.b64encode(figure_in_base64).decode()
            img_tag = f'<img src="data:image/png;base64,{figure_in_base64}" />'

        # Create a single HTML file with table and image
        html_string = f'<html><body>{html_table}<br>{img_tag}</body></html>'

        # Create a downloadable link for the HTML file
        buffer = io.StringIO()
        buffer.write(html_string)
        buffer.seek(0)
        b64 = base64.b64encode(buffer.read().encode()).decode()

        download_link = f'data:text/html;base64,{b64}'
        print(f"Generated download link: {download_link}")  # Debugging statement

        return download_link
    else:
        print("Not all inputs are present, so not generating a download link.")  # Debugging statement
        return dash.no_update


if __name__ == '__main__':
    app.run_server(debug=True)
