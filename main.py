import pandas as pd

from bokeh.layouts import column, row
from bokeh.models import Select, Panel, Tabs
from bokeh.plotting import curdoc, figure


nedPlot = figure(title="Position")
nedPlot.circle(x=1, y=2)
positionTab = Panel(child=nedPlot, title="Position")

accelPlot = figure(title="Accelerometer")
accelPlot.circle(x=1, y=2)
developerTab = Panel(child=accelPlot, title="Developer")


layout = Tabs(tabs=[positionTab, developerTab])

curdoc().add_root(layout)
curdoc().title = "CRW Payload Team 2021 - 2022"
