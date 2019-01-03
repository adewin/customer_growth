
# coding: utf-8

# In[156]:


import pandas as pd
import warnings
warnings.filterwarnings('ignore')
from datetime import timedelta


# In[159]:


def prep_for_rfm(dataframe,cust_id='CustomerID', quantity='Quantity',price='UnitPrice', total_price = 'TotalPrice'):
    '''
    Prepares a customer database for an RFM Analysis
    
    Takes in a dataset with a format similar to those found in by UCI
    library in this link:
    http://archive.ics.uci.edu/ml/machine-learning-databases/00352/
    '''
    
    dataframe = dataframe[pd.notnull(dataframe[cust_id])]
    for var in [quantity,price]:
        dataframe = dataframe[(dataframe[var]>0)]
    dataframe[total_price] = dataframe[quantity] * dataframe[price]
    return dataframe


# In[160]:


def create_rfm_table(dataframe, cust_id='CustomerID', invoice_date='InvoiceDate', total_price = 'TotalPrice'):
    NOW = dataframe[invoice_date].max().to_datetime() + timedelta(days=1)
    dataframe[invoice_date] = pd.to_datetime(dataframe[invoice_date])
    #Creating an RFM Table
    rfmTable = dataframe.groupby(cust_id).agg(
    {
        'InvoiceDate': lambda x: (NOW - x.max()).days, 
        'InvoiceNo': lambda x: len(x), total_price: lambda x: x.sum()
     }
    )
    rfmTable['InvoiceDate'] = rfmTable['InvoiceDate'].astype(int)
    rfmTable.rename(
    columns={
        'InvoiceDate': 'recency', 
        'InvoiceNo': 'frequency', 
        'TotalPrice': 'monetary_value'}, 
    inplace=True
    )
    return rfmTable


# In[161]:


def segment_rfm_table(rfm_table):
    
    segments = {}
    
    quantiles = rfm_table.quantile(q=[0.25,0.5,0.75])
    quantiles = quantiles.to_dict()
    
    def RScore(x,p,d):
        if x <= d[p][0.25]:
            return 1
        elif x <= d[p][0.50]:
            return 2
        elif x <= d[p][0.75]: 
            return 3
        else:
            return 4
    def FMScore(x,p,d):
        if x <= d[p][0.25]:
            return 4
        elif x <= d[p][0.50]:
            return 3
        elif x <= d[p][0.75]: 
            return 2
        else:
            return 1
    
    segmented_rfm = rfm_table 
    segmented_rfm['r_quartile'] = segmented_rfm['recency'].apply(RScore, args=('recency',quantiles,))
    segmented_rfm['f_quartile'] = segmented_rfm['frequency'].apply(FMScore, args=('frequency',quantiles,))
    segmented_rfm['m_quartile'] = segmented_rfm['monetary_value'].apply(FMScore, args=('monetary_value',quantiles,))
    segmented_rfm['RFMScore'] = segmented_rfm.r_quartile.map(str) + segmented_rfm.f_quartile.map(str) + segmented_rfm.m_quartile.map(str)
    
    def create_segment(segmented_rfm,r_quartile=1,f_quartile=1,m_quartile=1):
        step1 = segmented_rfm[segmented_rfm['r_quartile']==r_quartile].sort_values('monetary_value', ascending=False)
        step2 = step1[step1['f_quartile']==f_quartile].sort_values('monetary_value', ascending=False)
        step3 = step2[step2['m_quartile']==m_quartile].sort_values('monetary_value', ascending=False)
        step3
        return step3
    
    segments['best'] = create_segment(segmented_rfm=segmented_rfm,
                                      r_quartile=1,
                                      f_quartile=1,
                                      m_quartile=1
    )
    segments['almost_lost'] = create_segment(segmented_rfm=segmented_rfm,
                                      r_quartile=3,
                                      f_quartile=1,
                                      m_quartile=1
    )
    segments['lost'] = create_segment(segmented_rfm=segmented_rfm,
                                      r_quartile=4,
                                      f_quartile=1,
                                      m_quartile=1
    )
    segments['lost_cheap'] = create_segment(segmented_rfm=segmented_rfm,
                                      r_quartile=4,
                                      f_quartile=4,
                                      m_quartile=4
    )
    segments['loyal'] = segmented_rfm[segmented_rfm['f_quartile']==1].sort_values('monetary_value', ascending=False)
    segments['big_spender'] = segmented_rfm[segmented_rfm['m_quartile']==1].sort_values('monetary_value', ascending=False)
    

    return segments


# In[162]:


def main(raw_data):
    df_clean = prep_for_rfm(dataframe=raw_data)
    rfm_table = create_rfm_table(dataframe=df_clean)
    segmented_rfm = segment_rfm_table(rfm_table=rfm_table)
    return segmented_rfm


# In[166]:


if __name__=="__main__":
    df = pd.read_excel('Online Retail.xlsx')
    segmented_rfm = main(raw_data=df1)
    
    print("""
    **************************************
    RFM MARKETING STRATEGY
    **************************************
    
    The following strategies are recommended for RFM:
    
    BEST CUSTOMERS: no price incentives, new products, and loyalty programs
    LOYAL CUSTOMERS: Use frequency and monetary metrics to segment further
    BIG SPENDERS: Market the most expensive products
    ALMOST LOST & LOST: Aggresive price incentives
    LOST CHEAP CUSTOMERS: Don't spend too many resources trying to acquire
    
    
    
    """)

