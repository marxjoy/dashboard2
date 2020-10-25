import datetime as dt
import os

from werkzeug.utils import secure_filename
from flask import Flask, jsonify, send_from_directory, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go

import pandas as pd


app = Flask(__name__)
app.config.from_object("project.config.Config")
db = SQLAlchemy(app)

dash_app = dash.Dash(
    __name__,
    server=app,
    routes_pathname_prefix='/dash/'
)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}


class CurrencyDaily(db.Model):
    __tablename__ = "currency"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(8), nullable=False)
    bid = db.Column(db.Numeric)
    ask = db.Column(db.Numeric)
    timestamp = db.Column(db.DateTime)
    date = db.Column(db.Date)

    def __init__(self, name, code, bid, ask, date):
        self.name = name
        self.code = code
        self.bid = bid
        self.ask = ask
        self.date = date
        self.timestamp = dt.datetime.now()


@app.route("/actual/<code>")
def get_actual_currency(code):
    query = CurrencyDaily.query.filter_by(code=code.upper()).order_by(CurrencyDaily.date.desc()).first()
    if query is None:
        return jsonify(code=code, warning="Code not found"), 404
    else:
        return jsonify(name=query.name,
                       code=query.code,
                       bid=float(query.bid),
                       ask=float(query.ask),
                       date=url_for('archive', date=query.date),
                       timestamp=query.timestamp), 200


@app.route("/archive/<date>")
def archive(date):
    query = CurrencyDaily.query.filter_by(date=date).all()
    bids = {q.code: str(q.bid) for q in query}
    asks = {q.code: str(q.ask) for q in query}
    if not bids and not asks:
        return jsonify(date=date, warning="No records available"), 404
    else:
        return jsonify(date=date, bids=bids, asks=asks), 200


@app.route("/static/<path:filename>")
def staticfiles(filename):
    return send_from_directory(app.config["STATIC_FOLDER"], filename)


@app.route("/media/<path:filename>")
def mediafiles(filename):
    return send_from_directory(app.config["MEDIA_FOLDER"], filename)


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["MEDIA_FOLDER"], filename))
    return """
    <!doctype html>
    <title>upload new file</title>
    <form action="" method=post enctype=multipart/form-data>
        <p><input type=file name=file><input type=submit value=Upload>
    </form>
    """


def serve_layout():
    # available_indicators = df['code'].unique()
    available_indicators = ['USD', 'AUD', 'CAD', 'EUR', 'HUF', 'CHF', 'GBP', 'JPY', 'CZK', 'DKK', 'NOK', 'SEK', 'XDR', 'EEK']
    return html.Div([html.H1('Currency comparision in time', style={'text-align': 'center'}),
                     html.Div([html.Div([
                             dcc.Dropdown(
                                 id='a-column',
                                 options=[{'label': i, 'value': i} for i in available_indicators],
                                 value='EUR'
                             ),
                             dcc.RadioItems(
                                 id='a-type',
                                 options=[{'label': i, 'value': i} for i in ['bid', 'ask']],
                                 value='bid',
                                 labelStyle={'display': 'inline-block'}
                             )], style={'width': '25%', 'display': 'inline-block'}),


                         html.Div([
                             dcc.Dropdown(
                                 id='b-column',
                                 options=[{'label': i, 'value': i} for i in available_indicators],
                                 value='USD'
                             ),
                             dcc.RadioItems(
                                 id='b-type',
                                 options=[{'label': i, 'value': i} for i in ['bid', 'ask']],
                                 value='bid',
                                 labelStyle={'display': 'inline-block'}
                             )], style={'width': '25%', 'display': 'inline-block'}),

                         html.Div([
                             dcc.Dropdown(
                                 id='c-column',
                                 options=[{'label': i, 'value': i} for i in available_indicators],
                                 value=''
                             ),
                             dcc.RadioItems(
                                 id='c-type',
                                 options=[{'label': i, 'value': i} for i in ['bid', 'ask']],
                                 value='ask',
                                 labelStyle={'display': 'inline-block'}
                             )], style={'width': '25%', 'display': 'inline-block'}),

                         html.Div([
                             dcc.Dropdown(
                                 id='d-column',
                                 options=[{'label': i, 'value': i} for i in available_indicators],
                                 value=''
                             ),
                             dcc.RadioItems(
                                 id='d-type',
                                 options=[{'label': i, 'value': i} for i in ['bid', 'ask']],
                                 value='ask',
                                 labelStyle={'display': 'inline-block'}
                             )], style={'width': '25%', 'display': 'inline-block'}),]),
                     dcc.Graph(id='live-update-graph'),
                     dcc.Interval(id='interval-component', interval=1 * 100000, n_intervals=0)]) # in milliseconds




@dash_app.callback(Output('live-update-text', 'children'),
                   [Input('interval-component', 'n_intervals')])
def update_metrics(n):
    query = CurrencyDaily.query.all()
    data = {i: [row.date, row.code, row.bid, row.ask, row.name] for i, row in enumerate(query)}
    df = pd.DataFrame.from_dict(data, orient='index', columns=['date', 'code', 'bid', 'ask', 'name'])
    return [html.H2('Bid and ask currency comparision', style={'text-align: center'}),
            html.Div([
            dcc.Dropdown(id='b_column',
                         options=[{'label': i + c, 'value': (i, c)} for i in df.code.unique() for c in ('bid', 'ask')],
                         value='currency'),
            dcc.Dropdown(id='a_column',
                         options=[{'label': i + c, 'value': (i, c)} for i in df.code.unique() for c in ('bid', 'ask')],
                         value='currency')],
                         style={'width': '48%'})]


@dash_app.callback(Output('live-update-graph', 'figure'),
                    [Input('interval-component', 'n_intervals'),
                     Input('a-column', 'value'),
                     Input('b-column', 'value'),
                     Input('c-column', 'value'),
                     Input('d-column', 'value'),
                     Input('a-type', 'value'),
                     Input('b-type', 'value'),
                     Input('c-type', 'value'),
                     Input('d-type', 'value')])
def update_graph(n, a_column_name, b_column_name,c_column_name,d_column_name,
                 a_type, b_type, c_type, d_type):
    # df = pd.read_csv('curr_and_gold.csv')
    query = CurrencyDaily.query.all()
    data = {i: [row.date, row.code, row.bid, row.ask, row.name] for i, row in enumerate(query)}
    df = pd.DataFrame.from_dict(data, orient='index', columns=['date', 'code', 'bid', 'ask', 'name'])
    df_a = df[df['code'] == a_column_name].sort_values(by='date').set_index('date')
    df_b = df[df['code'] == b_column_name].sort_values(by='date').set_index('date')
    df_c = df[df['code'] == c_column_name].sort_values(by='date').set_index('date')
    df_d = df[df['code'] == d_column_name].sort_values(by='date').set_index('date')

    y0 = df_a[a_type]
    x0 = y0.index
    y1 = df_b[b_type]
    x1 = y1.index
    y2 = df_c[c_type]
    x2 = y2.index
    y3 = df_d[d_type]
    x3 = y3.index

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x0, y=y0,
                            mode='lines',
                            name=a_column_name))
    fig.add_trace(go.Scatter(x=x1, y=y1,
                        mode='lines',
                        name=b_column_name))
    fig.add_trace(go.Scatter(x=x2, y=y2,
                        mode='lines',
                        name=c_column_name))
    fig.add_trace(go.Scatter(x=x3, y=y3,
                        mode='lines',
                        name=d_column_name))

    fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

    fig.update_xaxes(title='date')
    fig.update_yaxes(title='value')

    return fig


dash_app.layout = serve_layout
