import kagglehub
nafisur_dataset_for_predictive_maintenance_path = kagglehub.dataset_download('nafisur/dataset-for-predictive-maintenance')

print('Data source import complete.')

"""# LSTM For Predictive Maintenance

### Loading Libraries
"""

# Commented out IPython magic to ensure Python compatibility.
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import confusion_matrix,accuracy_score

from keras.models import Sequential
from keras.layers import Dense, Dropout, LSTM, Activation
from keras.callbacks import EarlyStopping

import matplotlib.pyplot as plt
plt.style.use('ggplot')
# %matplotlib inline

"""### Loading Dataset"""

dataset_train=pd.read_csv('/content/PM_train.txt',sep=' ',header=None).drop([26,27],axis=1)
col_names = ['id','cycle','setting1','setting2','setting3','s1','s2','s3','s4','s5','s6','s7','s8','s9','s10','s11','s12','s13','s14','s15','s16','s17','s18','s19','s20','s21']
dataset_train.columns=col_names
print('Shape of Train dataset: ',dataset_train.shape)
dataset_train.head()

dataset_test=pd.read_csv('/content/PM_test.txt',sep=' ',header=None).drop([26,27],axis=1)
dataset_test.columns=col_names
#dataset_test.head()
print('Shape of Test dataset: ',dataset_train.shape)
dataset_train.head()

"""#### Loadind Truth table"""

pm_truth=pd.read_csv('/content/PM_truth.txt',sep=' ',header=None).drop([1],axis=1)
pm_truth.columns=['more']
pm_truth['id']=pm_truth.index+1
pm_truth.head()

# generate column max for test data
rul = pd.DataFrame(dataset_test.groupby('id')['cycle'].max()).reset_index()
rul.columns = ['id', 'max']
rul.head()

# run to failure
pm_truth['rtf']=pm_truth['more']+rul['max']
pm_truth.head()

pm_truth.drop('more', axis=1, inplace=True)
dataset_test=dataset_test.merge(pm_truth,on=['id'],how='left')
dataset_test['ttf']=dataset_test['rtf'] - dataset_test['cycle']
dataset_test.drop('rtf', axis=1, inplace=True)
dataset_test.head()

dataset_train['ttf'] = dataset_train.groupby(['id'])['cycle'].transform(max)-dataset_train['cycle']
dataset_train.head()

df_train=dataset_train.copy()
df_test=dataset_test.copy()
period=30
df_train['label_bc'] = df_train['ttf'].apply(lambda x: 1 if x <= period else 0)
df_test['label_bc'] = df_test['ttf'].apply(lambda x: 1 if x <= period else 0)
df_train.head()

features_col_name=['setting1', 'setting2', 'setting3', 's1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11',
                   's12', 's13', 's14', 's15', 's16', 's17', 's18', 's19', 's20', 's21']
target_col_name='label_bc'

"""## Feature Scaling"""

sc=MinMaxScaler()
df_train[features_col_name]=sc.fit_transform(df_train[features_col_name])
df_test[features_col_name]=sc.transform(df_test[features_col_name])

"""## Function to reshape dataset as required by LSTM"""

import numpy as np
import pandas as pd

# Function to generate sequences for the LSTM model
def gen_sequence(id_df, seq_length, seq_cols):
    # Create a DataFrame of zeros and concatenate with id_df
    df_zeros = pd.DataFrame(np.zeros((seq_length - 1, id_df.shape[1])), columns=id_df.columns)
    id_df = pd.concat([df_zeros, id_df], ignore_index=True)

    # Extract data array for specified columns
    data_array = id_df[seq_cols].values
    num_elements = data_array.shape[0]
    lstm_array = []

    # Generate sequences of specified length
    for start, stop in zip(range(0, num_elements - seq_length), range(seq_length, num_elements)):
        lstm_array.append(data_array[start:stop, :])

    return np.array(lstm_array)

# Function to generate labels for the sequences
def gen_label(id_df, seq_length, seq_cols, label):
    # Create a DataFrame of zeros and concatenate with id_df
    df_zeros = pd.DataFrame(np.zeros((seq_length - 1, id_df.shape[1])), columns=id_df.columns)
    id_df = pd.concat([df_zeros, id_df], ignore_index=True)

    # Extract data array for specified columns
    data_array = id_df[seq_cols].values
    num_elements = data_array.shape[0]
    y_label = []

    # Generate label values corresponding to the end of each sequence
    for start, stop in zip(range(0, num_elements - seq_length), range(seq_length, num_elements)):
        y_label.append(id_df[label].iloc[stop])

    return np.array(y_label)

# timestamp or window size
seq_length=50
seq_cols=features_col_name

# generate X_train
X_train = np.concatenate([gen_sequence(df_train[df_train['id'] == id], seq_length, seq_cols)
                          for id in df_train['id'].unique()])
print(X_train.shape)
# generate y_train
y_train = np.concatenate([gen_label(df_train[df_train['id'] == id], 50, seq_cols, 'label_bc')
                          for id in df_train['id'].unique()])
print(y_train.shape)

# Generate X_test
X_test = np.concatenate([gen_sequence(df_test[df_test['id'] == id], seq_length, seq_cols)
                         for id in df_test['id'].unique()])
print(X_test.shape)

# Generate y_test
y_test = np.concatenate([gen_label(df_test[df_test['id'] == id], 50, seq_cols, 'label_bc')
                         for id in df_test['id'].unique()])
print(y_test.shape)

"""## LSTM Network"""

nb_features =X_train.shape[2]
timestamp=seq_length

model = Sequential()

model.add(LSTM(
         input_shape=(timestamp, nb_features),
         units=100,
         return_sequences=True))
model.add(Dropout(0.2))

model.add(LSTM(
          units=50,
          return_sequences=False))
model.add(Dropout(0.2))

model.add(Dense(units=1, activation='sigmoid'))
model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

model.summary()

# fit the network
model.fit(X_train, y_train, epochs=10, batch_size=200, validation_split=0.05, verbose=1,
          callbacks = [EarlyStopping(monitor='val_loss', min_delta=0, patience=0, verbose=0, mode='auto')])

# training metrics
scores = model.evaluate(X_train, y_train, verbose=1, batch_size=200)
print('Accurracy: {}'.format(scores[1]))

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix

y_pred=model.predict(X_test)
# Convert probabilities to class labels using a threshold (e.g., 0.5)
y_pred_binary = np.where(y_pred >= 0.5, 1, 0)

print('Accuracy of model on test data: ',accuracy_score(y_test,y_pred_binary))
print('Confusion Matrix: \n',confusion_matrix(y_test,y_pred_binary))

"""### Probability of Machine failure"""

def prob_failure(machine_id):
    machine_df=df_test[df_test.id==machine_id]
    machine_test=gen_sequence(machine_df,seq_length,seq_cols)
    m_pred=model.predict(machine_test)
    failure_prob=list(m_pred[-1]*100)[0]
    return failure_prob

machine_id=16
print('Probability that machine will fail within 30 days: ',prob_failure(machine_id))
