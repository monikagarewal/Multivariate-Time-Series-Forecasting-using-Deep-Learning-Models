!pip install pmdarima
import pandas as pd
import numpy as np

import os
from datetime import datetime
from google.colab import drive
drive.mount('/content/drive')
#Read the csv file
dir = '/content/drive/MyDrive/Telecom/2013-8/'
count = 0
j = 0
tmp = 1.1
df = pd.DataFrame(columns=['Timestamp [ms]', 'CPU cores', 'CPU capacity provisioned [MHZ]', 'CPU usage [MHZ]', 'CPU usage [%]', 'Memory capacity provisioned [KB]', 'Memory usage [KB]', 'Disk read throughput [KB/s]', 'Disk write throughput [KB/s]', 'Network received throughput [KB/s]', 'Network transmitted throughput [KB/s]'])
for filename in os.listdir(dir):
    f = os.path.join(dir, filename)
    # checking if it is a file
    if os.path.isfile(f):
        #print(f)
        data1 = pd.read_csv(f, sep = ";\t")
        data1.replace([np.inf, -np.inf], np.nan, inplace=True)
        data1 = data1.dropna()
        for i in range(data1.shape[0]):
            dt_obj = datetime.fromtimestamp(data1['Timestamp [ms]'][i])    #(int(data1['Timestamp [ms]'][i])).strftime('%Y-%m-%d')
            #tmp = float(dt_obj + '.0')
            data1['Timestamp [ms]'][i] = dt_obj
            j = j+1
        #data1['Timestamp [ms]'] = data1['Timestamp [ms]'].astype(float, errors = 'raise')
        data1['CPU cores'] = data1['CPU cores'].astype(float, errors = 'raise')
        df = df.append(data1)
        if(count > 30):
          break
        count = count+1
df.shape
print(df.info())
df.head()

#drop zeroes from dataset
df = df.replace(0, np.NaN)
df = df.dropna()
df.shape

#plotting the data
df.plot(x=0, y=8)

#applying dickey-fuller test
from statsmodels.tsa.stattools import adfuller
#creating a function for values 
def adf_test(dataset):
   dftest = adfuller(dataset, autolag = 'AIC')
   print("1. ADF : ",dftest[0])
   print("2. P-Value : ", dftest[1])
   print("3. Num Of Lags : ", dftest[2])
   print("4. Num Of Observations Used For ADF Regression and Critical Values Calculation :", dftest[3])
   print("5. Critical Values :")
   for key, val in dftest[4].items():
       print("\t",key, ": ", val)
#printing for AvgTemp
adf_test(df['Disk write throughput [KB/s]'])

#creating our ARIMA Model
from pmdarima import auto_arima
# Ignore harmless warnings
import warnings
warnings.filterwarnings("ignore")
#Calling our model and generating best possible ARIMA combination,
#calling our function
stepwise_fit = auto_arima(df['Disk write throughput [KB/s]'],suppress_warnings=True)           
stepwise_fit.summary()

from statsmodels.tsa.arima_model import ARIMA 
#splitting into train and test
print(df.shape)
train=df.iloc[:-18000]
test=df.iloc[-18000:]
print(train.shape,test.shape)
print(test.iloc[0],test.iloc[-1])

#model Training
import statsmodels.api as sm
model = sm.tsa.arima.ARIMA(train['Disk write throughput [KB/s]'], order = (3, 1, 4))
model = model.fit()
model.summary()

#making predictions on test set
#plotting the predictions
start=len(train)
end=len(train)+len(test)-1
print(start, end)
pred=model.predict(start=start,end=end,typ='levels').rename('ARIMA predictions')
#pred.index=index_future_dates
pred.plot(legend=True)
test['Disk write throughput [KB/s]'].plot(legend=True)

#knowing the mean Disk write throughput [KB/s]
test['Disk write throughput [KB/s]'].mean()

#calculating mean squared error
from sklearn.metrics import mean_squared_error
from math import sqrt
rmse=sqrt(mean_squared_error(pred,test['Disk write throughput [KB/s]']))
print(rmse)
#Printing the last five values to see on what date the dataset has its end.
#checking data end date
model2=sm.tsa.arima.ARIMA(df['Disk write throughput [KB/s]'],order=(5, 1, 0))
model2=model2.fit()
df.tail()

#printing predictions for next 30 days
index_future_dates=pd.date_range(start='2013-09-11',end='2013-10-11')
#print(index_future_dates)
pred=model2.predict(start=len(df),end=len(df)+30,typ='levels').rename('ARIMA Predictions')
#print(comp_pred)
pred.index=index_future_dates
print(pred)

import matplotlib.pyplot as plt
plt.plot(index_future_dates, pred)
plt.xlabel('Future Dates')
plt.ylabel('ARIMA Predictions')
