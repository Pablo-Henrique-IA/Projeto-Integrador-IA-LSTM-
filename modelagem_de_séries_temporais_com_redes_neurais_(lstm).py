# -*- coding: utf-8 -*-
"""Modelagem de séries temporais com Redes Neurais (LSTM).ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/10l8OZ3iwLT6H_hKPKBItLYDhvX3W4n5S

# **Modelagem preços de ações com Redes Neurais Recorrentes - LSTM**

Nesse pequeno projeto iremos aplicar uma rede neural artificial para modelar e gerar previsões com séries temporais. A rede neural que usaremos se chama LSTM (ou *Long short-term memory*) e é uma rede neural recorrente, ou seja, ela é uma estrutura de processamento que consegue representar grandes variedades de comportamentos dinâmicos.

As redes neurais recorrentes possuem mecanismos de *loops*, permitindo que haja realimentação de informação e a criação de representações internas e mecanismos de **memória** que permitem armazenar infomações temporais (principalmente de séries temporais). O fato de possuir muitos *loops*, mesmo com um número reduzido de parâmetros, a rede neural pode gerar um comportamento complexo.

A maioria das redes neurais recorrentes possuem problemas de dependência de longo prazo. Problema de denpendência de longo prazo é quando uma rede neural precisa de um contexto maior (mais informações anteriores à atual) para poder gerar uma previsão acurada. As LSTM's não possuem esse problema, pois foram projetadas para evitar esse problema de dependência.

A LSTM é bastante usada para previsões de séries temporais e usaremos ela aqui para modelar dados de preços de ações.

## Dados

Os dados foram extraídos da plataforma *Yahoo* e são os preços das ações da Petróleo Brasileiro S/A (Petrobras) na Bolsa de valores americana. A peoridicidade é diária e vai do dia 1 de janeiro de 2014 até 11 de Novembro de 2024. Aqui, iremos modelar os preços de fechamento das ações *PBR*.

## **yfinance**

O yfinance é uma biblioteca do Python que permite a extração de dados financeiros de várias fontes, como Yahoo Finance, de forma rápida e fácil. Com o yfinance, é possível obter informações atualizadas sobre ações, índices, moedas e muito mais, facilitando a análise e tomada de decisão no mercado financeiro.
"""

!pip install yfinance
!pip install yfinance --upgrade --no-cache-dir

"""## Importação das bibliotecas"""

import math
import numpy as np
import pandas as pd
import seaborn as sns
from pandas_datareader import data as pdr
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense,LSTM
import matplotlib.pyplot as plt
import plotly.graph_objects as go
plt.style.use('fivethirtyeight')

from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score
from sklearn.metrics import mean_squared_log_error

"""## Importa dos dados

Vamos usar o *DataReader* para extrair os dados da plataforma *Yahoo* com a periodicidade e intervalo que queremos.
"""

# Fetch data using yfinance
df = yf.download("PBR", start="2014-01-01", end="2024-11-11")

# Print some data to check if it worked
print(df.head())

"""## Análise Exploratória dos dados

Podemos ver as 5 primeiras observações dos 5 preços que foram extraídos (de alta, de baixa, de abertura, de fechamento e o de fechamento ajustado) e o volume de ações que foram negociadas no dia.
"""

df.head()

"""Temos 2733 observações no nosso conjunto de dados.


"""

df.shape

"""A colunas não possuem nenhum valor faltante."""

df.isna().sum()

"""Temos  5 dados do tipo *float* e 1 dado do tipo *int*."""

df.info()

"""Abaixo podemos ver a tabela estatística de todas as variáveis."""

df.describe()

"""Visualizando as séries de preços e volume de ações."""

df.corr()

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
plt.figure(figsize=(20,5))
correlacao=df.corr()
sns.heatmap(correlacao, annot = True, cmap = "Set3");

plt.figure(figsize=(20,10))
df['Open'].plot(color='red')
plt.title('Preço de abertura das ações em US$', size=15)
plt.xlabel('Período',size=15)
plt.ylabel('Valores')
plt.legend(['Preço de abertura ADR'])
plt.show()

plt.figure(figsize=(20,10))
df['High'].plot(color='green')
df['Low'].plot(color='yellow')
plt.title('Preços de alta e baixa das ações PBR em US$', size=15)
plt.xlabel('Período',size=15)
plt.ylabel('Valores')
plt.legend(['Preço de alta PBR','Preço de baixa PBR'])
plt.show()

plt.figure(figsize=(20,10))
df['Adj Close'].plot(color='orange')
plt.title('Preços de fechamento ajustado das ações PBR em US$', size=15)
plt.xlabel('Período',size=15)
plt.ylabel('Valores')
plt.legend(['Preço de fechamento PBR'])
plt.show()

plt.figure(figsize=(20,10))
df['Close'].plot()
plt.title('Preços de fechamento das ações PBR em US$', size=15)
plt.xlabel('Período',size=15)
plt.ylabel('Valores')
plt.legend(['Preço de fechamento PBR'])
plt.show()

plt.figure(figsize=(20,10))
df['Volume'].plot(color='purple')
plt.title('Volume de ações negociadas diariamente', size=15)
plt.xlabel('Período',size=15)
plt.ylabel('')
plt.legend(['Volume de ações'])
plt.show()

"""## Dados de treino

Vamos agora separar os dados de treino. Vamos escolher para os dados de treino 80% da série temporal. Para o treino teremos 2187 observações.
"""

#Da série vamos extrair apenas os dados de fechamento
data=df.filter(['Close'])
#selecionar seus valores
dataset=data.values
#separa 80% desses dados
training_data_len=math.ceil(len(dataset)*.8)
#e vamos visualizar quantas observações temos
training_data_len

"""## Transformação dos dados

Precisaremos alterar a escala dos dados para o futuro procedimento de treino e geração de previsões do modelo. Usaremos o método *MinMaxScaler* que colocará os dados em uma escala entre 0 e 1.
"""

#escalando para o intervalo entre 0 e 1
scaler=MinMaxScaler(feature_range=(0,1))

data = df[['Close']]  # Use double brackets to select 'Close' as a DataFrame, not a Series
dataset = data.values

# Continue with scaling:
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(dataset)
scaled_data

"""Agora vamos separar os dados em *x* e *y* de treino."""

#criando um dataset de treino
train_data = scaled_data[0:training_data_len,:]
#separando dados de treino e teste
x_train=[]
y_train=[]

for i in range(60,len(train_data)):
  x_train.append(train_data[i-60:i,0])
  y_train.append(train_data[i,0])
  if i<=61:
    print(x_train)
    print(y_train)
    print()

"""Vamos converter *x_train* e *y_train* para *array numpy*."""

x_train,y_train = np.array(x_train), np.array(y_train)

"""Em *x_train* temos um *array* com dimensões 2127 x 60."""

x_train.shape

"""Agora vamos redimensionar os dados."""

x_train=np.reshape(x_train, (x_train.shape[0], x_train.shape[1],1))
x_train.shape

"""## Modelagem dos dados

Agora vamos criar o nosso modelo. Como é uma rede neural teremos camadas de entradas, camadas intermediárias e camadas de saída. Temos o nosso modelo *Sequential* e vamos adicionando as camadas (*LSTM* e *Dense*). As duas primeiras camadas possuem 50 neurônios, a penúltima camada densa (*Dense*) 25 e a última camada tem apenas 1 neurônio que é de onde serão geradas as saídas do modelo, que serão as nossas previsões.
"""

model=Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(x_train.shape[1],1)))
model.add(LSTM(50, return_sequences=False))
model.add(Dense(25))
model.add(Dense(1))

"""Agora que o nosso modelo foi criado, podemos configurá-lo com a função perda e com as métricas. Aqui usaremos o *adam* que é o método *stochastic gradient descent* ou gradiente estocástico descendente que é um dos métodos de minimização. A métrica de avaliação que usaremos será o *mean_squared_error* ou média dos erros quadrados."""

model.compile(optimizer='adam', loss='mean_squared_error')

"""Vamos treinar o modelo e usaremos um período de treino ou *epoch*."""

model.fit(x_train,y_train,batch_size=1,epochs=1)

"""## Dados de teste

Aqui vamos criar dois conjuntos de dados de teste *x_test* e *y_test*, uma para aplicar ao modelo treinado e o outro para comparar o resultados das previsões. Faremos, praticamente, a mesma coisa que na seleção dos dados de treino. Vamos separar os dados, mas apenas ao *x_test* transformaremos em um *array numpy*.
"""

#criando os dados de teste
test_data=scaled_data[training_data_len-60:,:]

#criando x_test e y_test
x_test=[]
y_test=dataset[training_data_len:,:]

for i in range(60,len(test_data)):
  x_test.append(test_data[i-60:i,0])

"""Convertendo em um *array numpy*."""

x_test=np.array(x_test)

"""Redimensionando os dados de teste que serão aplicado no modelo para previsão."""

x_test=np.reshape(x_test, (x_test.shape[0],x_test.shape[1],1))

"""Gerando as previsões com o modelo LSTM e logo em seguida iremos inverter a transformação que fizemos para que os resultados tenham a escala correta."""

predictions=model.predict(x_test)
predictions = scaler.inverse_transform(predictions)

"""## Avaliação do modelo

Agora teremos que avaliar o desempenho do modelo comparando com os valores reais, para isso usaremos a métrica *RMSE* (*root mean squared error* ) que nos trará a raiz da média do quadrado dos erros. Essa métrica é a mais usada para avaliar modelos de séries temporais.

O nosso resultado de um valor menor que 1. Em alguns trabalhos, para avaliar o desempenho do modelo, comparamos o resultado do *RMSE* com o desvio padrão. No nosso caso o desvio padrão da série de preços de fechamento foi de 3.78 e nosso *RMSE* de 0.48. Logo temos um bom resultado gerado pelo modelo.
"""

#RMSE
rmse=np.sqrt(np.mean(predictions-y_test)**2)
rmse

"""Vamos uma coluna com os dados de validação e as previsões e comparar os resultados."""

train=data[:training_data_len]

valid=data[training_data_len:]

valid['Predictions'] = predictions

"""Avaliando graficamente, vemos que o resultado das previsões foi muito próximo, para não dizer quase idêntico."""

plt.figure(figsize=(20,5))
plt.title('MODELO LSTM',size=15)
plt.xlabel('Datas',size=15)
plt.ylabel('Preços de fechamento em US$',size=15)
plt.plot(train['Close'])
plt.plot(valid[['Close','Predictions']])
plt.legend(['Train','Valid','Predictions'])
plt.show()

"""Podemos comparar as médias dos valores de validação e das previsões. Vemos que as médias são bem próximas uma das outras."""

print('Média dos valores reais:',valid['Close'].mean())
print('Média das previsões da LSTM:',valid['Predictions'].mean())

"""Abaixo podemos ver as estatísticas descritivas completas das previsões e dos dados de validação. As médias, desvios-pradrão e quantis possuem os valores próximos."""

valid.describe()

"""## Conclusão

Esse pequeno projeto vimos as etapas para o tratamento e modeloagem de dados com essa poderosa rede neural recorrente chamada LSTM. A LSTM possui uma capacidade formidável de gerar resultados acurados, pelo seu mecanismo de memória de longo prazo; resultados esses que podem até ter um desempenho melhor do que outros métodos de modelagem de séries temporais (como algoritmos determinísticos ou a modelagem Box-Jenkins).
"""