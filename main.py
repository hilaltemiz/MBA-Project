# pip install pandas
# pip install yfinance

import pandas as pd
import yfinance as yf
import curl_cffi.requests as requests

session = requests.Session(impersonate="chrome")
session.verify = False


def importData(symbol="GARAN.IS", date="2017-01-01"):
    #seçilen tarih için verileri indir
    df = yf.download(symbol, start=date, progress=False, session=session)
    
    #tarihi indexe ata
    df.index = pd.to_datetime(df.index)
    
    df.columns = df.columns.get_level_values(0)
    
    #tüm kolon isimlerini büyüt
    df.columns = df.columns.str.upper()
    
    return df


df = importData(symbol="GARAN.IS", date="2017-01-01")

print(df.head())

print(importData(symbol="GARAN.IS", date="2018-01-01").head())

import numpy as np
import pandas as pd
import copy





def applyMA(useSymbol="GARAN.IS", pMA=22):

    useDf = importData(symbol=useSymbol)

    useDf["SMA"] = useDf["CLOSE"].rolling(pMA).mean()

    useDf = useDf.dropna()

    useDf = copy.deepcopy(useDf)

    useDf["rawDECISION"] = np.where(
        useDf["CLOSE"] > useDf["SMA"],
        "BUY",
        "SELL"
    )

    useDfDec = useDf[
        useDf["rawDECISION"] != useDf["rawDECISION"].shift(1)
    ]

    useDfDec = copy.deepcopy(useDfDec)

    useDfDec = useDfDec.rename(columns={"rawDECISION": "DECISION"})

    useDfDec["RETURN"] = (
        (
            useDfDec["CLOSE"] /
            useDfDec["CLOSE"].shift(1)
        ) - 1
    ).shift(-1)


    useDfDec["realRETURN"] = np.where(
        useDfDec["DECISION"] == "SELL",
        -useDfDec["RETURN"],
        useDfDec["RETURN"]
    )

    useDfDec["realRETURN"] = (
        useDfDec["realRETURN"].shift(1)
    ) + 1

    useDfDec.loc[useDfDec.index[0], "realRETURN"] = 100

    useDfDec["realRETURN"] = useDfDec["realRETURN"].cumprod()

    df = pd.merge(
        useDf[["CLOSE", "SMA", "rawDECISION"]],
        useDfDec[["DECISION", "realRETURN"]],
        left_index=True,
        right_index=True,
        how="outer"
    )

    return df

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import os
pio.renderers.default = "browser"

def visualiseMA(useSymbol="GARAN.IS", pMA=22, download=False):

    """
    Seçilen hareketli ortalama uzunluğunda uygulanan alım satım stratejisini görselleştirir.
    """

    # Hareketli ortalamayı uygular ve sonucu 'useDfDec' değişkenine atar.
    useDf = applyMA(useSymbol, pMA)

    useDfDec = useDf.dropna(subset=["realRETURN"])
    

    
    # Boş değerleri önceki dolu değerle doldurur.
    useDf = useDf.ffill().bfill()
    print(useDfDec.head())
    
    # 'AL' ve 'SAT' sinyalleri için veri izleri oluşturur.
    trace1 = go.Scatter(
     x=useDfDec[useDfDec["DECISION"] == "BUY"].index,
     y=useDfDec[useDfDec["DECISION"] == "BUY"]["CLOSE"],
     mode="markers",
     line=dict(color="#92f890"),
     name="AL",
     opacity=0.8,
     marker=dict(
         size=8,
         line=dict(color="white", width=0.5)
     )
 )

    trace2 = go.Scatter(
        x=useDfDec[useDfDec["DECISION"] == "SELL"].index,
        y=useDfDec[useDfDec["DECISION"] == "SELL"]["CLOSE"],
        mode="markers",
        line=dict(color="#ff5566"),
        name="SAT",
        opacity=0.8,
        marker=dict(
            size=8,
            line=dict(color="white", width=0.5)
        )
    )
   
    # Grafiğin başlama ve bitiş tarihlerini belirler.
    startPlt, endPlt = (
    useDf.tail(600).index.values[0],
    useDf.tail(600).index.values[-1]
)

    startPlt = pd.to_datetime(startPlt)
    endPlt = pd.to_datetime(endPlt)

    # Alt grafiklerle birlikte bir ana grafik oluşturur.
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.7, 0.3]
    )

    fig.add_trace(trace1, row=1, col=1)
    fig.add_trace(trace2, row=1, col=1)
    
   # Kapanış fiyatları için veri izini ekler.
    fig.add_trace(
        go.Scatter(
            x=useDf.index,
            y=useDf["CLOSE"],
            line=dict(color="black", width=1),
            name="KAPANIŞ"
        ),
        row=1,
        col=1
    )

    # Hareketli ortalama için veri izini ekler.
    fig.add_trace(
        go.Scatter(
            x=useDf.index,
            y=useDf["SMA"],
            line=dict(color="#79addc", width=2),
            name="SMA (" + str(pMA) + ")"
        ),
        row=1,
        col=1
    )

    # Gerçek getiriler için veri izini ekler.
    fig.add_trace(
        go.Scatter(
            x=useDf.index,
            y=useDf["realRETURN"],
            line=dict(color="#000000", width=3),
            name="GETİRİ"
        ),
        row=2,
        col=1
    )

 

# İzi günceller.
    fig.update_traces(marker_size=14)

# Grafiğin düzenini belirler.
    layout = go.Layout(
    plot_bgcolor='#F8F9F9',
    title=useSymbol + " hissesinin " + str(pMA) + " günlük hareketli ortalaması için al/sat sinyal grafiği",
    font_color='#000000',
    font_size=12,
    xaxis=dict(
        rangeslider=dict(visible=False)
    )
)

    fig.update_layout(layout)

    fig.update_layout(
    autosize=False,
    width=900,
    height=600,
    margin=dict(l=50, r=50, b=100, t=100, pad=4)
)

    fig.update_layout(
    hovermode='x unified'
)

    fig.update_xaxes(
        type="date",
        range=[startPlt, endPlt]
    )

    fig.update_xaxes(
        tickformat="%d-%m-%Y"
    )

    # Grafiği indirme seçeneği etkinse, görüntü ve HTML olarak kaydeder.
    if download:

        if not os.path.exists("images"):
            os.mkdir("images")

        fig.write_image(
            "images/MA_" + useSymbol + ".png"
        )

        fig.write_html(
            "images/MA_" + useSymbol + ".html"
        )

    # Chrome'da gösterir
    fig.show(renderer="browser")

    return useDf

#visualiseMA(useSymbol="GARAN.IS", pMA=22, download=False)

from ta.trend import ADXIndicator


def applyADX(useSymbol="GARAN.IS", pADXMA=22, pADXThres=25):

    optDf = applyMA(useSymbol=useSymbol, pMA=pADXMA)

    trendDf = importData(symbol=useSymbol)

    adxIndicator = ADXIndicator(
        high=trendDf["HIGH"],
        low=trendDf["LOW"],
        close=trendDf["CLOSE"],
        window=pADXMA
    )

    trendDf["ADX"] = adxIndicator.adx()

    trendDf["TREND"] = np.where(
        trendDf["ADX"] > pADXThres,
        "UP",
        "DOWN"
    )

    optTrendDf = pd.merge(
        optDf[["CLOSE", "SMA", "rawDECISION"]],
        trendDf[["ADX", "TREND"]],
        left_index=True,
        right_index=True,
        how="outer"
    )

    optTrendDf["DECISION"] = np.where(
        optTrendDf["TREND"] == "UP",
        optTrendDf["rawDECISION"],
        "CLOSE"
    )

    optTrendDf = optTrendDf[
        optTrendDf["DECISION"] != optTrendDf["DECISION"].shift(1)
    ]

    optTrendDf = optTrendDf.copy()

    optTrendDf["RETURN"] = optTrendDf["CLOSE"].pct_change().shift(-1)

    optTrendDf["RETURN"] = np.where(
        optTrendDf["DECISION"] == "SELL",
        -optTrendDf["RETURN"],
        optTrendDf["RETURN"]
    )

    optTrendDf["RETURN"] = np.where(
        optTrendDf["DECISION"] == "CLOSE",
        0,
        optTrendDf["RETURN"]
    )

    optTrendDf["realRETURN"] = optTrendDf["RETURN"].shift(1) + 1

    optTrendDf.loc[optTrendDf.index[0], "realRETURN"] = 100

    optTrendDf["realRETURN"] = optTrendDf["realRETURN"].cumprod()

    return optTrendDf       


from ta.trend import ADXIndicator

def applyADX(useSymbol="GARAN.IS", pADXMA=22, pADXThres=25):

    optDf = applyMA(
        useSymbol=useSymbol,
        pMA=pADXMA
    )

    trendDf = importData(symbol=useSymbol)

    adxIndicator = ADXIndicator(
        high=trendDf["HIGH"],
        low=trendDf["LOW"],
        close=trendDf["CLOSE"],
        window=pADXMA
    )

    trendDf["ADX"] = adxIndicator.adx()

    trendDf["TREND"] = np.where(
        trendDf["ADX"] > pADXThres,
        "UP",
        "DOWN"
    )

    optTrendDf = pd.merge(
        optDf[["CLOSE", "SMA", "rawDECISION"]],
        trendDf[["ADX", "TREND"]],
        left_index=True,
        right_index=True,
        how="outer"
    )

    optTrendDf["DECISION"] = np.where(
        optTrendDf["TREND"] == "UP",
        optTrendDf["rawDECISION"],
        "CLOSE"
    )

    optTrendDf = optTrendDf[
        optTrendDf["DECISION"] != optTrendDf["DECISION"].shift(1)
    ]

    optTrendDf = optTrendDf.copy()

    optTrendDf["RETURN"] = optTrendDf["CLOSE"].pct_change().shift(-1)

    optTrendDf["RETURN"] = np.where(
        optTrendDf["DECISION"] == "SELL",
        -optTrendDf["RETURN"],
        optTrendDf["RETURN"]
    )

    optTrendDf["RETURN"] = np.where(
        optTrendDf["DECISION"] == "CLOSE",
        0,
        optTrendDf["RETURN"]
    )

    optTrendDf["realRETURN"] = optTrendDf["RETURN"].shift(1) + 1

    optTrendDf.loc[
        optTrendDf.index[0],
        "realRETURN"
    ] = 100

    optTrendDf["realRETURN"] = optTrendDf["realRETURN"].cumprod()

    return optTrendDf[
        ["CLOSE", "SMA", "rawDECISION", "ADX", "TREND", "DECISION", "realRETURN"]
    ]

def visualiseADX(useSymbol="GARAN.IS", pADXMA=22, pADXThres=25, download=False):

    useDf = applyADX(
        useSymbol=useSymbol,
        pADXMA=pADXMA,
        pADXThres=pADXThres
    )

    useDfDec = useDf.dropna(subset=["realRETURN"])
    useDf = useDf.ffill().bfill()

    startPlt, endPlt = (
        useDf.tail(600).index.values[0],
        useDf.tail(600).index.values[-1]
    )

    startPlt = pd.to_datetime(startPlt)
    endPlt = pd.to_datetime(endPlt)

    traceBuy = go.Scatter(
        x=useDfDec[useDfDec["DECISION"] == "BUY"].index,
        y=useDfDec[useDfDec["DECISION"] == "BUY"]["CLOSE"],
        mode="markers",
        name="AL",
        opacity=0.8,
        marker=dict(
            color="#92f890",
            size=12,
            line=dict(color="white", width=0.5)
        )
    )

    traceSell = go.Scatter(
        x=useDfDec[useDfDec["DECISION"] == "SELL"].index,
        y=useDfDec[useDfDec["DECISION"] == "SELL"]["CLOSE"],
        mode="markers",
        name="SAT",
        opacity=0.8,
        marker=dict(
            color="#ff5566",
            size=12,
            line=dict(color="white", width=0.5)
        )
    )

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.55, 0.25, 0.20]
    )

    fig.add_trace(
        go.Scatter(
            x=useDf.index,
            y=useDf["CLOSE"],
            line=dict(color="black", width=1),
            name="KAPANIŞ"
        ),
        row=1,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=useDf.index,
            y=useDf["SMA"],
            line=dict(color="#79addc", width=2),
            name="SMA (" + str(pADXMA) + ")"
        ),
        row=1,
        col=1
    )

    fig.add_trace(traceBuy, row=1, col=1)
    fig.add_trace(traceSell, row=1, col=1)

    fig.add_trace(
        go.Scatter(
            x=useDf.index,
            y=useDf["realRETURN"],
            line=dict(color="#000000", width=3),
            name="GETİRİ"
        ),
        row=2,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=useDf.index,
            y=useDf["ADX"],
            line=dict(color="#9467bd", width=2),
            name="ADX"
        ),
        row=3,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=useDf.index,
            y=[pADXThres] * len(useDf),
            line=dict(color="red", width=1, dash="dash"),
            name="ADX Eşik (" + str(pADXThres) + ")"
        ),
        row=3,
        col=1
    )

    fig.update_layout(
        plot_bgcolor="#F8F9F9",
        title=useSymbol + " hissesinin ADX destekli " + str(pADXMA) + " günlük hareketli ortalama al/sat sinyal grafiği",
        font_color="#000000",
        font_size=12,
        autosize=False,
        width=1000,
        height=750,
        margin=dict(l=50, r=50, b=100, t=100, pad=4),
        hovermode="x unified"
    )

    fig.update_xaxes(
        type="date",
        range=[startPlt, endPlt],
        tickformat="%d-%m-%Y"
    )

    fig.write_html(
        "adx_grafik.html",
        auto_open=True
    )

    return useDf


visualiseADX(
    useSymbol="GARAN.IS",
    pADXMA=22,
    pADXThres=25,
    download=False
)







