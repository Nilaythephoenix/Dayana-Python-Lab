# -*- coding: utf-8 -*-
"""btc_price_predictor.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1RNWcBloZAicMXbyf9T6OKtJJA8806Ga-

> import required libraries
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from keras.models import Sequential
from keras.layers import  Dense
from keras.layers import LSTM

""">loading  data set from file"""

data_set = pd.read_csv("/content/drive/MyDrive/bitcoin_ticker.csv")
data_set.head()

"""> some development actions, to get some understanding on data set"""

data_set['rpt_key'].value_counts()

"""# New Section

> building btc data frame
"""

data_frame = data_set.loc[(data_set['rpt_key'] == 'btc_usd')]
data_frame.head()

""">Convert datetime_id to data type and filter dates greater than  2017-06-28 00:00:00""""

data_frame = data_frame.reset_index(drop=True)
data_frame['datetime'] = pd.to_datetime(data_frame['datetime_id'])
data_frame = data_frame.loc[data_frame['datetime'] > pd.to_datetime('2017-06-28 00:00:00')]

data_frame.head(3)

data_frame.drop(['date_id', 'datetime_id', 'market', 'rpt_key', 'created_at', 'updated_at'], inplace=True, axis=1)
data_frame.head()

"""> we require only the last value, so we subset that and convert it to numpy array"""

df = data_frame[['last']]
df.head()

dataset = df.values
dataset = dataset.astype('float32')
dataset

""">Neural networks are sensitive to input data, especiallly when we are using activation functions like sigmoid or tanh activation functions are used. So we rescale our data to the range of 0-to-1, using MinMaxScaler"""

scaler = MinMaxScaler(feature_range=(0, 1))
dataset = scaler.fit_transform(dataset)

dataset

train_size = int(len(dataset) * 0.67)
test_size = len(dataset) - train_size
train, test = dataset[0:train_size, :], dataset[train_size:len(dataset), :]
print(len(train), len(test))

""">Now let us define the function called create_dataset, which take two inputs,
1. Dataset - numpy array that we want to convert into a dataset,
2. look_back - number of previous time steps to use as input variables to predict the next time period
"""

# convert an array of values into a dataset
def create_dataset(dataset, look_back=1):
  dataX, dataY = [], []
  for i in range(len(dataset)-look_back-1):
    a = dataset[i:(i+look_back), 0]
    dataX.append(a)
    dataY.append(dataset[i + look_back, 0])
  return np.array(dataX), np.array(dataY)

look_back = 10
trainX, trainY = create_dataset(train, look_back=look_back)
testX, testY = create_dataset(test, look_back=look_back)

trainX

trainY

# reshape input to be [samples, time steps, features]
trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
testX = np.reshape(testX, (testX.shape[0], 1, testX.shape[1]))

""">Build our Model"""

model = Sequential()
model.add(LSTM(4, input_shape=(1, look_back)))
model.add(Dense(1))
model.compile(loss='mean_squared_error', optimizer='adam')
model.fit(trainX, trainY, epochs=100, batch_size=256, verbose=2)

trainPredict = model.predict(trainX)
testPredict = model.predict(testX)

""">We have to invert the predictions before calculating error to so that reports will be in same units as our original data"""

trainPredict = scaler.inverse_transform(trainPredict)
trainY = scaler.inverse_transform([trainY])
testPredict = scaler.inverse_transform(testPredict)
testY = scaler.inverse_transform([testY])

trainScore = math.sqrt(mean_squared_error(trainY[0], trainPredict[:, 0]))
print('Train Score: %.2f RMSE' % (trainScore))
testScore = math.sqrt(mean_squared_error(testY[0], testPredict[:, 0]))
print('Test Score: %.2f RMSE' % (testScore))

# shift train predictions for plotting
trainPredictPlot = np.empty_like(dataset)
trainPredictPlot[:, :] = np.nan
trainPredictPlot[look_back:len(trainPredict) + look_back, :] = trainPredict

# shift test predictions for plotting
testPredictPlot = np.empty_like(dataset)
testPredictPlot[:, :] = np.nan
testPredictPlot[len(trainPredict) + (look_back * 2) + 1:len(dataset) - 1, :] = testPredict

plt.plot(df['last'], label='Actual')
plt.plot(pd.DataFrame(trainPredictPlot, columns=["close"], index=df.index).close, label='Training')
plt.plot(pd.DataFrame(testPredictPlot, columns=["close"], index=df.index).close, label='Testing')
plt.legend(loc='best')
plt.show()