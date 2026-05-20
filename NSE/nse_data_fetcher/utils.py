
"""
utils.py
Utility decorators for nse_data_fetcher.
Provides class-level track_time decorator.
"""
import time,os,inspect,functools
import pandas as pd
def track_time(cls):
    for name,method in inspect.getmembers(cls,inspect.isfunction):
        if name.startswith("corporate_") or name=="circulars":
            setattr(cls,name,_wrap(method))
    return cls


def _wrap(method):
    @functools.wraps(method)
    def wrapper(self,*args,**kwargs):
        start=time.strftime('%Y-%m-%d %H:%M:%S')
        result=method(self,*args,**kwargs)
        end=time.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(result,tuple) and len(result)==2:
            df,report_name=result
            if isinstance(df,pd.DataFrame) and not df.empty:
                df["Request Sent Time"]=start
                df["Data Received Time"]=end
                output_dir="json_data"
                if not os.path.exists(output_dir): os.makedirs(output_dir)
                fname=f"{report_name}_{start}.json".replace(" ","_").replace(":","-")
                df.to_json(os.path.join(output_dir,fname),orient="records",lines=True)
            return df
        return result
    return wrapper