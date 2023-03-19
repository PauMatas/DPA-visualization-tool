import numpy as np
import pandas as pd
import altair as alt
import warnings

from .steering import Steering
from .throttle import Throttle

class Lap:
    def __init__(self, df: pd.DataFrame, **kwargs) -> None:
        self.number = kwargs.get('number', -1)
        self.driver = kwargs.get('driver', 'Unknown')

        self.df = df

        # Times
        df['TimeStamp'] -= df['TimeStamp'].min()
        self.laptime = self.expected_unique('laptime')
        self.global_delta = self.expected_unique('globalDelta')
        self.delta = self.changing_points_df('delta')
        df['delta_color'] = df['delta'].apply(lambda x: 'red' if x < 0 else 'green')

        # Controls
        self.steering = Steering(df)
        self.throttle = Throttle(df)

        # Vector Nav
        df['dist1'] -= df['dist1'].min()

    def expected_unique(self, column: str) -> float | None:
        unique = self.df[column].unique()
        if len(unique) == 1:
            return unique[0]
        
        warnings.warn(f"Multiple {column} found for lap {self.number}")
        return None
    
    def changing_points_df(self, column: str) -> pd.DataFrame:
        previous = None
        changing_points = []

        for i, (_, row) in enumerate(self.df[column].items()):
            if previous is None or row != previous:
                changing_points.append({'time': self.df['TimeStamp'][i], column: row})
                previous = row

        return pd.DataFrame(changing_points)
    
    def gg_diagram(self):
        return alt.Chart(self.df).mark_point().encode(
            x='VN_ax:Q',
            y='VN_ay:Q',
            tooltip=['TimeStamp', 'VN_ax', 'VN_ay']
        )
    
    def positions_chart(self):
        # Racing line chart
        racing_line = alt.Chart(self.df).mark_line().encode(
            x = alt.X('xPosition:Q', scale=alt.Scale(zero=False)),
            y = alt.Y('yPosition:Q', scale=alt.Scale(zero=False)),
            color = alt.Color('delta_color:N', scale=alt.Scale(
                domain=['red', 'green'],
                range=['red', 'green'])
                ),
            order='index:Q',
            tooltip=['TimeStamp', 'xPosition', 'yPosition']
        )

        # Circuit direction icon
        p1 = self.df[['xPosition', 'yPosition']].head(1).to_numpy()[0]
        p100 = self.df[['xPosition', 'yPosition']].head(100).tail(1).to_numpy()[0]
        v = p100 - p1 # direction vector

        # Angle between vector and x axis
        angle = np.degrees(np.arctan2(v[1], v[0]))

        # Icon position
        normal = np.array([-v[1], v[0]])
        normal /= np.linalg.norm(normal)
        desp = normal * 1.5
        icon = p1 + desp

        start_df = pd.DataFrame([{'xPosition': icon[0], 'yPosition': icon[1]}])
        start = alt.Chart(start_df).mark_point().encode(
            x='xPosition:Q',
            y='yPosition:Q',
            shape=alt.value('wedge'),
            angle=alt.value(90 - angle),
            color=alt.value('black'),
            size=alt.value(150),
        )

        return racing_line + start
    

    def __repr__(self) -> str:
        return f"[Lap {self.number}] {self.laptime}s -> {self.driver}"