!pip install wandb
import wandb
wandb.init(project="MTP_Project", entity="cs20m040")
!wandb login fb3bb8a505ba908b667b747ed68e4b154b2f6fc5
from wandb.keras import WandbCallback
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM
from tensorflow.keras.layers import GRU
from tensorflow.keras.layers import Dense, Dropout
from keras import regularizers
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.preprocessing import StandardScaler
import seaborn as sns

from google.colab import drive
drive.mount('/content/drive')

#Read the csv file
df = pd.read_csv('/content/drive/MyDrive/Telecom/2013-8/100.csv', sep = ";\t")
print(df.head()) #7 columns, including the Date.


#Separate timestamp for future plotting
train_dates = df['Timestamp [ms]']
print(train_dates.tail(15)) #Check last few dates.

sweep_config = {
    'method' : 'random',
    'metric' : {
        'name' : 'accuracy',
        'goal' : 'maximize'
        },
    'parameters' : {
        'nFilters' : {'values' : [3, 16, 32, 64]},
        'epochs' : {'values' : [5, 10]},
        'batch_size' : {'values' : [16, 32, 64]},
        'activationFuncs' : {'values' : ['sigmoid', 'tanh', 'relu', 'softmax']},
        'dropout' :  {'values' : [0.4, 0.5]},
        'optimizer': {'values' : ['Adagrad', 'Adam', 'RMSprop', 'SGD', 'Nadam']},
        'loss' : {'values' : ['mape', 'mse']},
        'weight_decay' : {'values' : [0.05, 0.005, 0.0005]},
        'learning_rate' : {'values' : [0.01, 0.001, 0.0001]},
        } 
    }

#Variables for training
cols = list(df)[1:11]
#Date and volume columns are not used in training. 
print(cols)

#New dataframe with only training data
df_for_training = df[cols].astype(float)
print(df_for_training.head())

#LSTM uses sigmoid and tanh that are sensitive to magnitude so values need to be normalized
# normalize the dataset
scaler = StandardScaler()
scaler = scaler.fit(df_for_training)
df_for_training_scaled = scaler.transform(df_for_training)
print(df_for_training_scaled)
df_for_training_scaled.shape

#As required for LSTM networks, we require to reshape an input data into n_samples x timesteps x n_features. 
#In this example, the n_features is 10. We will make timesteps = 14 (past days data used for training). 

#Empty lists to be populated using formatted training data
trainX = []
trainY = []

n_future = 1   # Number of days we want to look into the future based on the past days.
n_past = 14  # Number of past days we want to use to predict the future.

#Reformat input data into a shape: (n_samples x timesteps x n_features)
#In my example, my df_for_training_scaled has a shape (20241, 10)
#20241 refers to the number of data points and 10 refers to the columns (multi-variables).
for i in range(n_past, len(df_for_training_scaled) - n_future + 1):
    trainX.append(df_for_training_scaled[i - n_past:i, 0:df_for_training.shape[1]])
    trainY.append(df_for_training_scaled[i + n_future - 1:i + n_future, 0:df_for_training.shape[1]])

trainX, trainY = np.array(trainX), np.array(trainY)

print('trainX shape == {}.'.format(trainX.shape))
print('trainY shape == {}.'.format(trainY.shape))

#LSTM
def train():
  config_defaults = {
      'nFilters' : 128,
      'epochs' : 5,
      'batch_size' : 16,
      'weight_decay' : 0.005,
      'learning_rate' : 0.01,
      'activationFuncs' : 'relu',
      'dropout' : 0.2,
      'optimizer' : 'adam',
      'loss' : 'mape',
      'init_method' : 'random',
      'weight_decay' : 0.5
      }
  wandb.init(config=config_defaults)
  config = wandb.config

  model = Sequential()
  model.add(LSTM(config.nFilters, activation=config.activationFuncs, input_shape=(trainX.shape[1], trainX.shape[2]), return_sequences=True))
  model.add(LSTM(config.nFilters, activation=config.activationFuncs, return_sequences=False))
  model.add(Dropout(config.dropout))
  #model.add(Dense(trainY.shape[2]), regularizers.l2(0.001), activation='relu')
  model.add(Dense(trainY.shape[2]))

  model.compile(optimizer=config.optimizer, loss=config.loss, metrics = 'accuracy')
  model.summary()
  # fit the model
  history = model.fit(trainX, trainY, epochs=config.epochs, batch_size=config.batch_size, validation_split=0.1, verbose=1, callbacks=[WandbCallback()])
sweep_id = wandb.sweep(sweep_config, entity="cs20m040", project="MTP_Project")
wandb.agent(sweep_id, function=train)

#GRU
def train1():
  config_defaults = {
      'nFilters' : 32,
      'epochs' : 5,
      'batch_size' : 16,
      'weight_decay' : 0.0005,
      'learning_rate' : 0.01,
      'activationFuncs' : 'relu',
      'dropout' : 0.2,
      'optimizer' : 'adam',
      'loss' : 'mse',
      'init_method' : 'random',
      'weight_decay' : 0.5
      }
  wandb.init(config=config_defaults)
  config = wandb.config

  model = Sequential()
  model.add(GRU(config.nFilters, activation=config.activationFuncs, input_shape=(trainX.shape[1], trainX.shape[2]), return_sequences=True))
  model.add(GRU(config.nFilters, activation=config.activationFuncs, return_sequences=False))
  model.add(Dropout(config.dropout))
  model.add(Dense(trainY.shape[2]))

  model.compile(optimizer=config.optimizer, loss=config.loss, metrics=['accuracy'])
  model.summary()
  # fit the model
  history = model.fit(trainX, trainY, epochs=config.epochs, batch_size=config.batch_size, validation_split=0.1, verbose=1, callbacks=[WandbCallback()])


sweep_id = wandb.sweep(sweep_config, entity="cs20m040", project="MTP_Project")
wandb.agent(sweep_id, function=train1)



#CNN-LSTM
historyGlobal = None
CNN_LSTM_Model = None
def train2():
  global historyGlobal
  global CNN_LSTM_Model
  config_defaults = {
      'nFilters' : 32,
      'epochs' : 5,
      'batch_size' : 16,
      'weight_decay' : 0.0005,
      'learning_rate' : 0.01,
      'activationFuncs' : 'relu',
      'dropout' : 0.2,
      'optimizer' : 'adam',
      'loss' : 'mse',
      'init_method' : 'random',
      'weight_decay' : 0.5
      }
  wandb.init(config=config_defaults)
  config = wandb.config

  CNN_LSTM_Model = Sequential()
  CNN_LSTM_Model.add(Conv1D(config.nFilters, kernel_size=5, strides=1, padding="valid", input_shape=(trainX.shape[1], trainX.shape[2]), return_sequences=True))
  CNN_LSTM_Model.add(LSTM(config.nFilters, activation=config.activationFuncs, return_sequences=True))
  CNN_LSTM_Model.add(LSTM(config.nFilters, activation=config.activationFuncs, return_sequences=False))
  CNN_LSTM_Model.add(Dropout(config.dropout))
  CNN_LSTM_Model.add(Dense(trainY.shape[2]))

  CNN_LSTM_Model.compile(optimizer=config.optimizer, loss=config.loss, metrics=['accuracy'])
  CNN_LSTM_Model.summary()
  # fit the model
  historyGlobal = CNN_LSTM_Model.fit(trainX, trainY, epochs=config.epochs, batch_size=config.batch_size, validation_split=0.1, verbose=1, callbacks=[WandbCallback()])


sweep_id = wandb.sweep(sweep_config, entity="cs20m040", project="MTP_Project")
wandb.agent(sweep_id, function=train2)



plt.plot(train.history.history['loss'], label='Training loss')
plt.plot(train.history.history['val_loss'], label='Validation loss')
plt.legend()

n_future = 90
forecast_period_dates = pd.date_range(list(train_dates)[-1], periods = n_future, freq = '1d').tolist()
print(forecast_period_dates)

#Make prediction
forecast = model.predict(trainX[-n_future:]) #shape = (n, 1) where n is the n_days_for_prediction

#Perform inverse transformation to rescale back to original range
#Since we used 5 variables for transform, the inverse expects same dimensions
#Therefore, let us copy our values 5 times and discard them after inverse transform
forecast_copies = np.repeat(forecast, df_for_training.shape[1], axis=-1)
y_pred_future = scaler.inverse_transform(forecast_copies)[:,0]
print(y_pred_future)

# Convert timestamp to date
forecast_dates = []
for time_i in forecast_period_dates:
    forecast_dates.append(time_i.date())
    
df_forecast = pd.DataFrame({'Date':np.array(forecast_dates), 'Open':y_pred_future})
df_forecast['Date']=pd.to_datetime(df_forecast['Date'])
df_forecast['Date']

original = df[['Timestamp [ms]', 'Network transmitted throughput [KB/s]']]
original['Timestamp [ms]']=pd.to_datetime(original['Timestamp [ms]'])
original = original.loc[original['Timestamp [ms]'] >= '1970-01-01']

sns.lineplot(original['Timestamp [ms]'], original['Network transmitted throughput [KB/s]'], label='Original Data')
sns.lineplot(df_forecast['Date'], df_forecast['Open'], label='Forecast Data')
