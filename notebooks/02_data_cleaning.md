```python
import pandas as pd
import numpy as np

DATA_PATH = "../data/raw/indian_roads_dataset.csv"

df = pd.read_csv(DATA_PATH)

print("Original shape:", df.shape)
```

    Original shape: (20000, 24)
    


```python
clean_df = df.copy()

print("Working copy created.")
print("Shape:", clean_df.shape)
```

    Working copy created.
    Shape: (20000, 24)
    


```python
clean_df = clean_df.drop(columns=["festival"])

print("festival column removed.")
print("New shape:", clean_df.shape)
```

    festival column removed.
    New shape: (20000, 23)
    


```python
clean_df["date"] = pd.to_datetime(
    clean_df["date"],
    errors="coerce"
)

clean_df["time"] = pd.to_datetime(
    clean_df["time"],
    format="%H:%M",
    errors="coerce"
).dt.time
print(clean_df[["date", "time"]].dtypes)
```

    date    datetime64[us]
    time            object
    dtype: object
    


```python
missing = clean_df.isnull().sum()

print("========== MISSING VALUES AFTER CLEANING ==========")
print(missing[missing > 0])
```

    ========== MISSING VALUES AFTER CLEANING ==========
    Series([], dtype: int64)
    


```python
print("========== COORDINATE VALIDATION ==========")

invalid_lat = (
    (clean_df["latitude"] < -90) |
    (clean_df["latitude"] > 90)
).sum()

invalid_lon = (
    (clean_df["longitude"] < -180) |
    (clean_df["longitude"] > 180)
).sum()

print("Invalid latitude:", invalid_lat)
print("Invalid longitude:", invalid_lon)
```

    ========== COORDINATE VALIDATION ==========
    Invalid latitude: 0
    Invalid longitude: 0
    


```python
print("Duplicate complete rows:", clean_df.duplicated().sum())
print(
    "Duplicate accident IDs:",
    clean_df["accident_id"].duplicated().sum()
)
```

    Duplicate complete rows: 0
    Duplicate accident IDs: 0
    


```python
OUTPUT_PATH = "../data/processed/cleaned_accidents.csv"

clean_df.to_csv(
    OUTPUT_PATH,
    index=False
)

print("Cleaned dataset saved successfully!")
print("Path:", OUTPUT_PATH)
print("Final shape:", clean_df.shape)
```

    Cleaned dataset saved successfully!
    Path: ../data/processed/cleaned_accidents.csv
    Final shape: (20000, 23)
    

high-risk location + time combinations


```python
print("========== TIME WINDOW PREPARATION ==========")

# Create 2-hour time windows
clean_df["time_window"] = (clean_df["hour"] // 2) * 2

# Convert to readable format
clean_df["time_window_label"] = (
    clean_df["time_window"].astype(str).str.zfill(2)
    + ":00 - "
    + (clean_df["time_window"] + 1).astype(str).str.zfill(2)
    + ":59"
)

print("Unique time windows:")
print(sorted(clean_df["time_window"].unique()))

print("\nTime-window distribution:")
print(clean_df["time_window_label"].value_counts().sort_index())
```

    ========== TIME WINDOW PREPARATION ==========
    Unique time windows:
    [np.int64(0), np.int64(2), np.int64(4), np.int64(6), np.int64(8), np.int64(10), np.int64(12), np.int64(14), np.int64(16), np.int64(18), np.int64(20), np.int64(22)]
    
    Time-window distribution:
    time_window_label
    00:00 - 01:59    1699
    02:00 - 03:59    1712
    04:00 - 05:59    1632
    06:00 - 07:59    1642
    08:00 - 09:59    1635
    10:00 - 11:59    1630
    12:00 - 13:59    1744
    14:00 - 15:59    1649
    16:00 - 17:59    1648
    18:00 - 19:59    1663
    20:00 - 21:59    1668
    22:00 - 23:59    1678
    Name: count, dtype: int64
    


```python
print("========== COORDINATE PRECISION ==========")

print("Unique latitude:", clean_df["latitude"].nunique())
print("Unique longitude:", clean_df["longitude"].nunique())
print(
    "Unique exact coordinate pairs:",
    clean_df[["latitude", "longitude"]].drop_duplicates().shape[0]
)

print("\nSample coordinates:")
display(clean_df[["city", "latitude", "longitude"]].head(10))
```

    ========== COORDINATE PRECISION ==========
    Unique latitude: 19907
    Unique longitude: 19927
    Unique exact coordinate pairs: 20000
    
    Sample coordinates:
    


<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>city</th>
      <th>latitude</th>
      <th>longitude</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Pune</td>
      <td>18.680827</td>
      <td>73.930388</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Mumbai</td>
      <td>18.817732</td>
      <td>72.790846</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Mumbai</td>
      <td>19.096889</td>
      <td>72.819424</td>
    </tr>
    <tr>
      <th>3</th>
      <td>Chandigarh</td>
      <td>30.787805</td>
      <td>76.847507</td>
    </tr>
    <tr>
      <th>4</th>
      <td>Chennai</td>
      <td>12.965155</td>
      <td>80.283313</td>
    </tr>
    <tr>
      <th>5</th>
      <td>Delhi</td>
      <td>28.799490</td>
      <td>77.049666</td>
    </tr>
    <tr>
      <th>6</th>
      <td>Bangalore</td>
      <td>13.064327</td>
      <td>77.530941</td>
    </tr>
    <tr>
      <th>7</th>
      <td>Chandigarh</td>
      <td>30.786617</td>
      <td>76.733947</td>
    </tr>
    <tr>
      <th>8</th>
      <td>Hyderabad</td>
      <td>17.422447</td>
      <td>78.464881</td>
    </tr>
    <tr>
      <th>9</th>
      <td>Bangalore</td>
      <td>12.939033</td>
      <td>77.498966</td>
    </tr>
  </tbody>
</table>
</div>



```python
print("========== SPATIAL GRID INSPECTION ==========")

GRID_SIZE = 0.01

clean_df["lat_grid"] = (
    np.floor(clean_df["latitude"] / GRID_SIZE) * GRID_SIZE
).round(2)

clean_df["lon_grid"] = (
    np.floor(clean_df["longitude"] / GRID_SIZE) * GRID_SIZE
).round(2)

grid_counts = (
    clean_df
    .groupby(["city", "lat_grid", "lon_grid"])
    .size()
    .reset_index(name="accident_count")
    .sort_values("accident_count", ascending=False)
)

print("Number of occupied grid cells:", len(grid_counts))

print("\nTop 20 grid cells:")
display(grid_counts.head(20))
```

    ========== SPATIAL GRID INSPECTION ==========
    Number of occupied grid cells: 8105
    
    Top 20 grid cells:
    


<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>city</th>
      <th>lat_grid</th>
      <th>lon_grid</th>
      <th>accident_count</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>1585</th>
      <td>Chandigarh</td>
      <td>30.76</td>
      <td>76.88</td>
      <td>14</td>
    </tr>
    <tr>
      <th>1389</th>
      <td>Chandigarh</td>
      <td>30.67</td>
      <td>76.72</td>
      <td>14</td>
    </tr>
    <tr>
      <th>1298</th>
      <td>Chandigarh</td>
      <td>30.62</td>
      <td>76.80</td>
      <td>14</td>
    </tr>
    <tr>
      <th>1541</th>
      <td>Chandigarh</td>
      <td>30.74</td>
      <td>76.84</td>
      <td>14</td>
    </tr>
    <tr>
      <th>1268</th>
      <td>Chandigarh</td>
      <td>30.61</td>
      <td>76.70</td>
      <td>13</td>
    </tr>
    <tr>
      <th>1369</th>
      <td>Chandigarh</td>
      <td>30.66</td>
      <td>76.72</td>
      <td>13</td>
    </tr>
    <tr>
      <th>1274</th>
      <td>Chandigarh</td>
      <td>30.61</td>
      <td>76.76</td>
      <td>13</td>
    </tr>
    <tr>
      <th>1349</th>
      <td>Chandigarh</td>
      <td>30.65</td>
      <td>76.72</td>
      <td>13</td>
    </tr>
    <tr>
      <th>1293</th>
      <td>Chandigarh</td>
      <td>30.62</td>
      <td>76.75</td>
      <td>13</td>
    </tr>
    <tr>
      <th>1556</th>
      <td>Chandigarh</td>
      <td>30.75</td>
      <td>76.79</td>
      <td>12</td>
    </tr>
    <tr>
      <th>1440</th>
      <td>Chandigarh</td>
      <td>30.69</td>
      <td>76.83</td>
      <td>12</td>
    </tr>
    <tr>
      <th>1460</th>
      <td>Chandigarh</td>
      <td>30.70</td>
      <td>76.83</td>
      <td>12</td>
    </tr>
    <tr>
      <th>1644</th>
      <td>Chandigarh</td>
      <td>30.79</td>
      <td>76.87</td>
      <td>12</td>
    </tr>
    <tr>
      <th>1499</th>
      <td>Chandigarh</td>
      <td>30.72</td>
      <td>76.82</td>
      <td>11</td>
    </tr>
    <tr>
      <th>1513</th>
      <td>Chandigarh</td>
      <td>30.73</td>
      <td>76.76</td>
      <td>11</td>
    </tr>
    <tr>
      <th>1328</th>
      <td>Chandigarh</td>
      <td>30.64</td>
      <td>76.71</td>
      <td>11</td>
    </tr>
    <tr>
      <th>1526</th>
      <td>Chandigarh</td>
      <td>30.73</td>
      <td>76.89</td>
      <td>11</td>
    </tr>
    <tr>
      <th>1396</th>
      <td>Chandigarh</td>
      <td>30.67</td>
      <td>76.79</td>
      <td>11</td>
    </tr>
    <tr>
      <th>1464</th>
      <td>Chandigarh</td>
      <td>30.70</td>
      <td>76.87</td>
      <td>11</td>
    </tr>
    <tr>
      <th>1376</th>
      <td>Chandigarh</td>
      <td>30.66</td>
      <td>76.79</td>
      <td>11</td>
    </tr>
  </tbody>
</table>
</div>



```python
print("========== LOCATION + TIME DISTRIBUTION ==========")

location_time = (
    clean_df
    .groupby(
        ["city", "lat_grid", "lon_grid", "time_window"]
    )
    .size()
    .reset_index(name="accident_count")
)

print("Total location-time combinations:", len(location_time))

print("\nAccidents per location-time combination:")
display(location_time["accident_count"].describe())
```

    ========== LOCATION + TIME DISTRIBUTION ==========
    Total location-time combinations: 17988
    
    Accidents per location-time combination:
    


    count    17988.000000
    mean         1.111852
    std          0.351865
    min          1.000000
    25%          1.000000
    50%          1.000000
    75%          1.000000
    max          7.000000
    Name: accident_count, dtype: float64



```python
print("\nTop 20 location-time combinations:")
display(
    location_time
    .sort_values("accident_count", ascending=False)
    .head(20)
)
```

    
    Top 20 location-time combinations:
    


<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>city</th>
      <th>lat_grid</th>
      <th>lon_grid</th>
      <th>time_window</th>
      <th>accident_count</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>3003</th>
      <td>Chandigarh</td>
      <td>30.67</td>
      <td>76.72</td>
      <td>4</td>
      <td>7</td>
    </tr>
    <tr>
      <th>2409</th>
      <td>Chandigarh</td>
      <td>30.61</td>
      <td>76.76</td>
      <td>10</td>
      <td>4</td>
    </tr>
    <tr>
      <th>3256</th>
      <td>Chandigarh</td>
      <td>30.69</td>
      <td>76.83</td>
      <td>10</td>
      <td>4</td>
    </tr>
    <tr>
      <th>2904</th>
      <td>Chandigarh</td>
      <td>30.66</td>
      <td>76.72</td>
      <td>6</td>
      <td>4</td>
    </tr>
    <tr>
      <th>4259</th>
      <td>Chandigarh</td>
      <td>30.79</td>
      <td>76.87</td>
      <td>22</td>
      <td>4</td>
    </tr>
    <tr>
      <th>2510</th>
      <td>Chandigarh</td>
      <td>30.62</td>
      <td>76.75</td>
      <td>4</td>
      <td>4</td>
    </tr>
    <tr>
      <th>5661</th>
      <td>Chennai</td>
      <td>13.05</td>
      <td>80.10</td>
      <td>22</td>
      <td>4</td>
    </tr>
    <tr>
      <th>3998</th>
      <td>Chandigarh</td>
      <td>30.77</td>
      <td>76.71</td>
      <td>22</td>
      <td>4</td>
    </tr>
    <tr>
      <th>2408</th>
      <td>Chandigarh</td>
      <td>30.61</td>
      <td>76.76</td>
      <td>6</td>
      <td>4</td>
    </tr>
    <tr>
      <th>4328</th>
      <td>Chennai</td>
      <td>12.80</td>
      <td>80.29</td>
      <td>8</td>
      <td>4</td>
    </tr>
    <tr>
      <th>3414</th>
      <td>Chandigarh</td>
      <td>30.71</td>
      <td>76.74</td>
      <td>0</td>
      <td>4</td>
    </tr>
    <tr>
      <th>11160</th>
      <td>Kolkata</td>
      <td>22.40</td>
      <td>88.35</td>
      <td>10</td>
      <td>4</td>
    </tr>
    <tr>
      <th>12717</th>
      <td>Kolkata</td>
      <td>22.60</td>
      <td>88.48</td>
      <td>18</td>
      <td>4</td>
    </tr>
    <tr>
      <th>13137</th>
      <td>Kolkata</td>
      <td>22.66</td>
      <td>88.32</td>
      <td>20</td>
      <td>4</td>
    </tr>
    <tr>
      <th>16753</th>
      <td>Pune</td>
      <td>18.53</td>
      <td>73.81</td>
      <td>22</td>
      <td>4</td>
    </tr>
    <tr>
      <th>3895</th>
      <td>Chandigarh</td>
      <td>30.76</td>
      <td>76.70</td>
      <td>16</td>
      <td>3</td>
    </tr>
    <tr>
      <th>3155</th>
      <td>Chandigarh</td>
      <td>30.68</td>
      <td>76.80</td>
      <td>22</td>
      <td>3</td>
    </tr>
    <tr>
      <th>3593</th>
      <td>Chandigarh</td>
      <td>30.73</td>
      <td>76.71</td>
      <td>4</td>
      <td>3</td>
    </tr>
    <tr>
      <th>2501</th>
      <td>Chandigarh</td>
      <td>30.62</td>
      <td>76.72</td>
      <td>16</td>
      <td>3</td>
    </tr>
    <tr>
      <th>5757</th>
      <td>Chennai</td>
      <td>13.06</td>
      <td>80.28</td>
      <td>16</td>
      <td>3</td>
    </tr>
  </tbody>
</table>
</div>

