from flask import Flask, render_template, request
from CyclePaths.navigation.navigation import googleMapsSucks
import folium

app = Flask(__name__)


@app.route("/route")
def find_route():
    start = request.args.get('start')
    end = request.args.get('end')
    map = googleMapsSucks(start, end)
    return render_template('index.html', _map = map._repr_html_())


@app.route("/")
def home():

    map = folium.Map(location=[51.508273,-0.121259], min_zoom=12, max_zoom=16)

    return render_template('index.html', _map = map._repr_html_())


if __name__ == '__main__':
    app.run(debug=True)