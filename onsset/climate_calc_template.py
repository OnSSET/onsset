# BELOW IS THE HEATWAVE CALCULATION METHOD FROM A DIFFERENT WORKSPACE CALLED CLIMATEDATA:

import os
from collections import defaultdict
from typing import Dict, Tuple, List

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


# ---------- CONFIG ----------

HW_START_YEAR = 1950
HW_END_YEAR   = 2024

# Heatwave threshold (°C) for "heatwave day" (map 1 & risk)
HEATWAVE_THRESHOLD_C = 32.0

# Paths
T2M_DIR = "../download_code/download_mdg_era5land"
ADMIN3_SHP = "boundary_files/gadm41_MDG_3/gadm41_MDG_3.shp"
POP_GRID_CSV = "boundary_files/MadagascarFinal.csv"

OUT_DIR = "risk_population_maps"
os.makedirs(OUT_DIR, exist_ok=True)

OUT_STATS_CSV   = os.path.join(OUT_DIR, "admin3_heatwave_stats.csv")
OUT_MAP_HW_DAYS = os.path.join(OUT_DIR, "map_heatwave_days_per_year.png")
OUT_MAP_MAX3DAY = os.path.join(OUT_DIR, "map_mean_max3day_T.png")
OUT_MAP_RISK    = os.path.join(OUT_DIR, "map_heatwave_intensity.png")
OUT_MAP_FREQ    = os.path.join(OUT_DIR, "map_heatwave_frequency_3day_categories.png")
OUT_MAP_FREQ    = os.path.join(OUT_DIR, "map_heatwave_frequency_3day_categories.png")
OUT_MAP_FREQ_POP = os.path.join(OUT_DIR, "map_heatwave_frequency_pop_3day_categories.png")


# 3-day rolling-mean categories (low, high, label)
THREEDAY_CATEGORIES = [
    (32.0, 35.0, "32–35 °C"),
    (35.0, 38.0, "35–38 °C"),
    (38.0, 42.0, "38–42 °C"),
    (42.0, np.inf, "42+ °C"),
]

# ----------------------------


def t2m_csv_path(year: int) -> str:
    return os.path.join(T2M_DIR, f"madagascar_t2m_dailymax_{year}.csv")


def build_cell_region_lookup(gdf_admin3: gpd.GeoDataFrame) -> pd.DataFrame:
    """
    Build a lookup table mapping (lat, lon) grid cells to admin-3 regions,
    using one available t2m CSV as a template.

    Returns columns: latitude, longitude, GID_3, NAME_3
    """
    print("[INFO] Building cell -> admin3 lookup from first available t2m CSV...")
    first_df = None
    for year in range(HW_START_YEAR, HW_END_YEAR + 1):
        path = t2m_csv_path(year)
        if os.path.exists(path):
            first_df = pd.read_csv(path)
            break

    if first_df is None:
        raise RuntimeError("No t2m CSV found to build cell-region lookup.")

    cells = (
        first_df[["latitude", "longitude"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    gdf_cells = gpd.GeoDataFrame(
        cells,
        geometry=gpd.points_from_xy(cells["longitude"], cells["latitude"]),
        crs="EPSG:4326",
    )

    gdf_join = gpd.sjoin(
        gdf_cells,
        gdf_admin3[["GID_3", "NAME_3", "geometry"]],
        how="inner",
        predicate="within",
    )

    lookup = gdf_join[["latitude", "longitude", "GID_3", "NAME_3"]].copy()
    print(f"[INFO] Cell-region lookup rows: {len(lookup)}")
    return lookup


def load_population_by_region(gdf_admin3: gpd.GeoDataFrame) -> pd.DataFrame:
    """
    Load population grid file and aggregate Pop to admin-3 regions.
    Expects columns: Pop, X_deg, Y_deg, (optional Country)
    """
    if not os.path.exists(POP_GRID_CSV):
        print(f"[WARN] Population CSV not found: {POP_GRID_CSV}. "
              f"Population-based map will be NA.")
        return pd.DataFrame(columns=["GID_3", "NAME_3", "region_pop"])

    df_pop = pd.read_csv(POP_GRID_CSV)
    required_cols = {"Pop", "X_deg", "Y_deg"}
    missing = required_cols - set(df_pop.columns)
    if missing:
        raise ValueError(
            f"Population CSV {POP_GRID_CSV} missing columns: {missing}"
        )

    if "Country" in df_pop.columns:
        df_pop = df_pop[df_pop["Country"].str.contains("Madagascar", na=False)]

    gdf_pop = gpd.GeoDataFrame(
        df_pop,
        geometry=gpd.points_from_xy(df_pop["X_deg"], df_pop["Y_deg"]),
        crs="EPSG:4326",
    )

    gdf_join = gpd.sjoin(
        gdf_pop,
        gdf_admin3[["GID_3", "NAME_3", "geometry"]],
        how="inner",
        predicate="within",
    )

    region_pop = (
        gdf_join.groupby(["GID_3", "NAME_3"], as_index=False)["Pop"]
        .sum()
        .rename(columns={"Pop": "region_pop"})
    )

    print(f"[INFO] Aggregated population for {len(region_pop)} regions.")
    return region_pop


def main():
    # 1) Admin-3 boundaries
    gdf_admin3 = gpd.read_file(ADMIN3_SHP)
    print("Admin3 CRS:", gdf_admin3.crs)
    if gdf_admin3.crs is None or gdf_admin3.crs.to_epsg() != 4326:
        gdf_admin3 = gdf_admin3.to_crs(epsg=4326)

    # 2) Cell -> region lookup
    cell_region_lookup = build_cell_region_lookup(gdf_admin3)

    # Region accumulators
    region_stats: Dict[Tuple[str, str], Dict] = defaultdict(
        lambda: {
            "heatwave_days_total": 0,
            "years_with_data": 0,
            "max3day_list": [],
            # 3-day category counts (total over all years)
            "count_32_35_total": 0,
            "count_35_38_total": 0,
            "count_38_42_total": 0,
            "count_42p_total": 0,
        }
    )

    # 3) Loop over years
    for year in range(HW_START_YEAR, HW_END_YEAR + 1):
        csv_path = t2m_csv_path(year)
        if not os.path.exists(csv_path):
            print(f"[WARN] Missing t2m CSV for year {year}: {csv_path} – skipping.")
            continue

        print(f"[INFO] Processing year {year}...")
        df = pd.read_csv(csv_path)

        if "date" not in df.columns or "t2m_max_C" not in df.columns:
            raise ValueError(f"{csv_path} must contain 'date' and 't2m_max_C'.")

        df["date"] = pd.to_datetime(df["date"])
        df = df.merge(cell_region_lookup, on=["latitude", "longitude"], how="left")
        df = df.dropna(subset=["GID_3"])
        if df.empty:
            print(f"[WARN] No land cells after join for year {year}, skipping.")
            continue

        # Region-mean daily max temperature
        reg_day = (
            df.groupby(["GID_3", "NAME_3", "date"], as_index=False)["t2m_max_C"]
            .mean()
            .rename(columns={"t2m_max_C": "tmax_reg_C"})
        )
        reg_day["year"] = reg_day["date"].dt.year

        # Heatwave days per region
        hw_mask = reg_day["tmax_reg_C"] > HEATWAVE_THRESHOLD_C
        hw_days = (
            reg_day[hw_mask]
            .groupby(["GID_3", "NAME_3"], as_index=False)["date"]
            .nunique()
            .rename(columns={"date": "heatwave_days_year"})
        )
        hw_days_dict = {
            (row["GID_3"], row["NAME_3"]): int(row["heatwave_days_year"])
            for _, row in hw_days.iterrows()
        }

                # 3.2) Max 3-day mean T per region per year
        # (still based on *region-mean* daily Tmax, for the magnitude map)
        max3day_this_year: Dict[Tuple[str, str], float] = {}

        for (gid, name), df_reg in reg_day.groupby(["GID_3", "NAME_3"], sort=False):
            s = (
                df_reg.sort_values("date")
                .set_index("date")["tmax_reg_C"]
            )
            if len(s) < 3:
                continue
            roll3 = s.rolling(window=3, min_periods=3).mean()
            max_val = float(roll3.max())
            if np.isfinite(max_val):
                max3day_this_year[(gid, name)] = max_val

        # 3.3) Daily category counts per region, using the
        #      *maximum cell temperature in the region* each day
        reg_day_max = (
            df.groupby(["GID_3", "NAME_3", "date"], as_index=False)["t2m_max_C"]
              .max()
              .rename(columns={"t2m_max_C": "tmax_reg_max_C"})
        )

        freq_days_this_year: Dict[Tuple[str, str], Dict[str, int]] = {}
        for (gid, name), df_reg_max in reg_day_max.groupby(
            ["GID_3", "NAME_3"], sort=False
        ):
            smax = df_reg_max["tmax_reg_max_C"]

            c32_35 = int(((smax >= 32.0) & (smax < 35.0)).sum())
            c35_38 = int(((smax >= 35.0) & (smax < 38.0)).sum())
            c38_42 = int(((smax >= 38.0) & (smax < 42.0)).sum())
            c42p   = int((smax >= 42.0).sum())

            freq_days_this_year[(gid, name)] = dict(
                c32_35=c32_35,
                c35_38=c35_38,
                c38_42=c38_42,
                c42p=c42p,
            )


        # Update accumulators
        regions_in_year = set(
            tuple(x) for x in reg_day[["GID_3", "NAME_3"]].drop_duplicates().values
        )

        for key in regions_in_year:
            gid, name = key
            stats = region_stats[key]

            # heatwave days
            stats["heatwave_days_total"] += hw_days_dict.get(key, 0)
            stats["years_with_data"] += 1

            # max 3-day mean
            if key in max3day_this_year:
                stats["max3day_list"].append(max3day_this_year[key])

            # 3-day category counts
            if key in freq_days_this_year:
                f = freq_days_this_year[key]
                stats["count_32_35_total"] += f["c32_35"]
                stats["count_35_38_total"] += f["c35_38"]
                stats["count_38_42_total"] += f["c38_42"]
                stats["count_42p_total"]   += f["c42p"]


    # 4) Build stats DataFrame
    rows: List[Dict] = []
    for (gid, name), stats in region_stats.items():
        years = stats["years_with_data"]
        if years == 0:
            mean_hw_days = np.nan
            mean_max3day = np.nan
            m32_35 = m35_38 = m38_42 = m42p = np.nan
        else:
            mean_hw_days = stats["heatwave_days_total"] / years
            mean_max3day = (
                float(np.mean(stats["max3day_list"]))
                if stats["max3day_list"] else np.nan
            )
            m32_35 = stats["count_32_35_total"] / years
            m35_38 = stats["count_35_38_total"] / years
            m38_42 = stats["count_38_42_total"] / years
            m42p   = stats["count_42p_total"]   / years

        rows.append(
            dict(
                GID_3=gid,
                NAME_3=name,
                years_with_data=years,
                mean_heatwave_days_per_year=mean_hw_days,
                mean_max_3day_T_C=mean_max3day,
                mean_3day_events_32_35_per_year=m32_35,
                mean_3day_events_35_38_per_year=m35_38,
                mean_3day_events_38_42_per_year=m38_42,
                mean_3day_events_42p_per_year=m42p,
            )
        )

    df_heat = pd.DataFrame(rows)
    print(f"[INFO] Computed heatwave stats for {len(df_heat)} regions.")

    # 5) Population & risk
    region_pop = load_population_by_region(gdf_admin3)
    df_all = df_heat.merge(region_pop, on=["GID_3", "NAME_3"], how="left")
    df_all["heatwave_risk_person_days"] = (
        df_all["region_pop"] * df_all["mean_heatwave_days_per_year"]
    )

        # Population-weighted heatwave frequency (person-days per year in each category)
    df_all["freq_32_35_person_days"] = (
        df_all["region_pop"] * df_all["mean_3day_events_32_35_per_year"]
    )
    df_all["freq_35_38_person_days"] = (
        df_all["region_pop"] * df_all["mean_3day_events_35_38_per_year"]
    )
    df_all["freq_38_42_person_days"] = (
        df_all["region_pop"] * df_all["mean_3day_events_38_42_per_year"]
    )
    df_all["freq_42p_person_days"] = (
        df_all["region_pop"] * df_all["mean_3day_events_42p_per_year"]
    )


    df_all.to_csv(OUT_STATS_CSV, index=False)
    print(f"[INFO] Saved admin-3 heatwave stats to {OUT_STATS_CSV}")
    print(df_all.head())






# BELOW IS THE SPI CALCULATION METHOD FROM A DIFFERENT WORKSPACE CALLED CLIMATEDATA:

import os
from typing import List, Dict

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from scipy.stats import gamma, norm

# ---------- CONFIG ----------

DATA_START_YEAR = 1950
DATA_END_YEAR   = 2024    # last year to include in drought stats

# Baseline period for SPI fitting (gamma distribution)
BASELINE_START = 1950
BASELINE_END   = 2000

SPI_SCALE = 3  # SPI-3

# Threshold for a "drought year" (any drought)
DROUGHT_THRESHOLD_YEAR = -1.0

# Intensity-class thresholds for yearly minimum SPI
MILD_LOW      = -1.5
MODERATE_LOW  = -2.0
SEVERE_LOW    = -2.5
# Interpretation:
#   mild:     (MILD_LOW, DROUGHT_THRESHOLD_YEAR]
#   moderate: (MODERATE_LOW, MILD_LOW]
#   severe:   (SEVERE_LOW, MODERATE_LOW]
#   extreme:  <= SEVERE_LOW

# Paths
TP_DIR = "../download_code/download_mdg_era5land"
ADMIN3_SHP = "boundary_files/gadm41_MDG_3/gadm41_MDG_3.shp"
POP_GRID_CSV = "boundary_files/MadagascarFinal.csv"

OUT_DIR = "spi3_drought_years_maps"
os.makedirs(OUT_DIR, exist_ok=True)

OUT_STATS_CSV   = os.path.join(OUT_DIR, "admin3_spi3_drought_years_stats.csv")
OUT_MAP_YEARS   = os.path.join(OUT_DIR, "map_spi3_drought_years_1950_2024.png")
OUT_MAP_INT     = os.path.join(OUT_DIR, "map_spi3_drought_intensity_classes_1950_2024.png")
OUT_MAP_INT_POP = os.path.join(OUT_DIR, "map_spi3_drought_intensity_classes_pop_1950_2024.png")

# ----------------------------


def tp_csv_path(year: int) -> str:
    return os.path.join(TP_DIR, f"madagascar_tp_monthlytotal_{year}.csv")


def load_population_by_region(gdf_admin3: gpd.GeoDataFrame) -> pd.DataFrame:
    """Load population grid file and aggregate Pop to admin-3 regions.

    Expects columns in the CSV: Pop, X_deg, Y_deg, (optional Country).
    Returns a DataFrame with columns: GID_3, NAME_3, region_pop.
    """
    if not os.path.exists(POP_GRID_CSV):
        print(
            f"[WARN] Population CSV not found: {POP_GRID_CSV}. "
            f"Population-weighted drought maps will be NA."
        )
        return pd.DataFrame(columns=["GID_3", "NAME_3", "region_pop"])

    df_pop = pd.read_csv(POP_GRID_CSV)
    required_cols = {"Pop", "X_deg", "Y_deg"}
    missing = required_cols - set(df_pop.columns)
    if missing:
        raise ValueError(
            f"Population CSV {POP_GRID_CSV} missing columns: {missing}"
        )

    if "Country" in df_pop.columns:
        df_pop = df_pop[df_pop["Country"].str.contains("Madagascar", na=False)]

    gdf_pop = gpd.GeoDataFrame(
        df_pop,
        geometry=gpd.points_from_xy(df_pop["X_deg"], df_pop["Y_deg"]),
        crs="EPSG:4326",
    )

    gdf_join = gpd.sjoin(
        gdf_pop,
        gdf_admin3[["GID_3", "NAME_3", "geometry"]],
        how="inner",
        predicate="within",
    )

    region_pop = (
        gdf_join.groupby(["GID_3", "NAME_3"], as_index=False)["Pop"]
        .sum()
        .rename(columns={"Pop": "region_pop"})
    )

    print(f"[INFO] Aggregated population for {len(region_pop)} regions.")
    return region_pop


def load_all_precip(start_year: int, end_year: int) -> pd.DataFrame:
    """
    Load monthly precipitation CSVs for a year range.
    Returns columns: date, year, month, latitude, longitude, tp_mm_month
    """
    frames: List[pd.DataFrame] = []
    for year in range(start_year, end_year + 1):
        csv_path = tp_csv_path(year)
        if not os.path.exists(csv_path):
            print(f"[WARN] Missing tp CSV for year {year}: {csv_path} – skipping.")
            continue
        df = pd.read_csv(csv_path)
        if "year" not in df.columns or "month" not in df.columns:
            raise ValueError(f"{csv_path} missing 'year' or 'month' columns.")
        if "tp_mm_month" not in df.columns:
            raise ValueError(f"{csv_path} missing 'tp_mm_month' column.")

        df["date"] = pd.to_datetime(
            dict(year=df["year"], month=df["month"], day=1)
        )
        frames.append(
            df[["date", "year", "month", "latitude", "longitude", "tp_mm_month"]]
        )

    if not frames:
        raise RuntimeError("No precip data loaded – check TP_DIR and YEAR range.")
    all_df = pd.concat(frames, ignore_index=True)
    print(f"[INFO] Loaded precip data: {len(all_df):,} rows")
    return all_df


def compute_spi_for_cell(
    df_cell: pd.DataFrame,
    scale: int,
    baseline_start: int,
    baseline_end: int,
) -> pd.DataFrame:
    """
    Compute SPI_k for one grid cell.

    Input df_cell columns: date, year, month, tp_mm_month
    Returns DataFrame with: date, year, month, P_k, spi
    for months where SPI was successfully computed.
    """
    df = df_cell.sort_values("date").set_index("date")

    # Full continuous monthly index
    full_index = pd.date_range(df.index.min(), df.index.max(), freq="MS")
    df = df.reindex(full_index)

    # Fill missing precip with 0 mm
    df["tp_mm_month"] = df["tp_mm_month"].fillna(0.0)

    df["year"] = df.index.year
    df["month"] = df.index.month

    # k-month rolling accumulation
    df["P_k"] = df["tp_mm_month"].rolling(window=scale, min_periods=scale).sum()

    # Prepare SPI column
    df["spi"] = np.nan

    # Compute SPI separately for each calendar month
    for m in range(1, 13):
        mask_month = df["month"] == m
        if not mask_month.any():
            continue

        series = df.loc[mask_month, "P_k"]

        # Baseline subset for fitting
        baseline_mask = (
            mask_month &
            (df["year"] >= baseline_start) &
            (df["year"] <= baseline_end)
        )
        baseline_values = df.loc[baseline_mask, "P_k"].dropna()
        if len(baseline_values) < 10:
            # not enough data to fit gamma
            continue

        positive = baseline_values[baseline_values > 0]
        if len(positive) < 2:
            continue

        # Gamma fit: shape, loc=0, scale
        shape, loc, scale_param = gamma.fit(positive, floc=0)

        q = len(positive) / len(baseline_values)  # non-zero prob

        x = series.values
        x_clipped = np.maximum(x, 0.0001)

        G = gamma.cdf(x_clipped, shape, loc=0, scale=scale_param)

        # Mixed distribution: mass at zero
        H = (1.0 - q) + q * G
        H[x <= 0] = (1.0 - q)

        H = np.clip(H, 1e-6, 1 - 1e-6)
        spi_vals = norm.ppf(H)

        df.loc[series.index, "spi"] = spi_vals

    df = df.dropna(subset=["P_k", "spi"]).reset_index().rename(columns={"index": "date"})
    return df[["date", "year", "month", "P_k", "spi"]]


def main():
    # 1) Load admin-3 polygons
    gdf_admin3 = gpd.read_file(ADMIN3_SHP)
    print("Admin3 CRS:", gdf_admin3.crs)
    if gdf_admin3.crs is None or gdf_admin3.crs.to_epsg() != 4326:
        gdf_admin3 = gdf_admin3.to_crs(epsg=4326)

    # 1b) Population by region (for population-weighted metrics)
    region_pop = load_population_by_region(gdf_admin3)

    # 2) Load precip for full data period
    df_all = load_all_precip(DATA_START_YEAR, DATA_END_YEAR)

    # 3) Compute SPI-3 per grid cell (baseline fit = 1950–2000)
    grouped_cells = df_all.groupby(["latitude", "longitude"], sort=False)
    print(f"[INFO] Number of grid cells: {len(grouped_cells)}")

    cell_rows: List[pd.DataFrame] = []
    for (lat, lon), df_cell in grouped_cells:
        spi_df = compute_spi_for_cell(
            df_cell,
            scale=SPI_SCALE,
            baseline_start=BASELINE_START,
            baseline_end=BASELINE_END,
        )
        if spi_df.empty:
            continue
        spi_df["latitude"] = lat
        spi_df["longitude"] = lon
        cell_rows.append(spi_df)

    if not cell_rows:
        raise RuntimeError("No SPI-3 computed for any cell.")

    cell_spi = pd.concat(cell_rows, ignore_index=True)
    print(f"[INFO] Total SPI-3 records (cell-level): {len(cell_spi):,}")

    # 4) Aggregate to admin-3 region-month (mean over cells)
    gdf_cells = gpd.GeoDataFrame(
        cell_spi,
        geometry=gpd.points_from_xy(cell_spi["longitude"], cell_spi["latitude"]),
        crs="EPSG:4326",
    )

    gdf_join = gpd.sjoin(
        gdf_cells,
        gdf_admin3[["GID_3", "NAME_3", "geometry"]],
        how="inner",
        predicate="within",
    )
    print(f"[INFO] Joined cell SPI-3 to admin-3 rows: {len(gdf_join):,}")

    df_reg_month = (
        gdf_join
        .groupby(["GID_3", "NAME_3", "date"], as_index=False)["spi"]
        .mean()
        .rename(columns={"spi": "spi3_region_mean"})
    )
    df_reg_month["year"] = df_reg_month["date"].dt.year
    df_reg_month["month"] = df_reg_month["date"].dt.month

    # 5) Drought-year stats per region (1950–2024)
    regions = (
        gdf_admin3[["GID_3", "NAME_3"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    stats_rows: List[Dict] = []
    for _, reg in regions.iterrows():
        gid = reg["GID_3"]
        name = reg["NAME_3"]

        df_r = df_reg_month[df_reg_month["GID_3"] == gid].copy()
        if df_r.empty:
            stats_rows.append(
                dict(
                    GID_3=gid,
                    NAME_3=name,
                    years_with_data=0,
                    drought_years_total=np.nan,
                    mild_years_total=np.nan,
                    moderate_years_total=np.nan,
                    severe_years_total=np.nan,
                    extreme_years_total=np.nan,
                    frac_drought_years=np.nan,
                )
            )
            continue

        years_present = sorted(df_r["year"].unique())
        drought_years = 0
        mild_years = 0
        moderate_years = 0
        severe_years = 0
        extreme_years = 0

        for year in range(DATA_START_YEAR, DATA_END_YEAR + 1):
            df_y = df_r[df_r["year"] == year]
            if df_y.empty:
                continue

            min_spi = df_y["spi3_region_mean"].min()
            if np.isnan(min_spi):
                continue

            # Any drought?
            if min_spi <= DROUGHT_THRESHOLD_YEAR:
                drought_years += 1

                # Classify by strongest intensity reached
                if (min_spi > MILD_LOW) and (min_spi <= DROUGHT_THRESHOLD_YEAR):
                    mild_years += 1
                elif (min_spi > MODERATE_LOW) and (min_spi <= MILD_LOW):
                    moderate_years += 1
                elif (min_spi > SEVERE_LOW) and (min_spi <= MODERATE_LOW):
                    severe_years += 1
                elif min_spi <= SEVERE_LOW:
                    extreme_years += 1

        years_with_data = len(years_present)
        if years_with_data > 0:
            frac_drought = drought_years / years_with_data
        else:
            frac_drought = np.nan

        stats_rows.append(
            dict(
                GID_3=gid,
                NAME_3=name,
                years_with_data=years_with_data,
                drought_years_total=drought_years,
                mild_years_total=mild_years,
                moderate_years_total=moderate_years,
                severe_years_total=severe_years,
                extreme_years_total=extreme_years,
                frac_drought_years=frac_drought,
            )
        )

    df_stats = pd.DataFrame(stats_rows)

    # Merge population and compute population-weighted intensity metrics
    df_stats = df_stats.merge(region_pop, on=["GID_3", "NAME_3"], how="left")

    # (Optional) person-weighted totals (kept for reference)
    for src_col, dst_col in [
        ("mild_years_total", "mild_years_person"),
        ("moderate_years_total", "moderate_years_person"),
        ("severe_years_total", "severe_years_person"),
        ("extreme_years_total", "extreme_years_person"),
    ]:
        df_stats[dst_col] = df_stats[src_col] * df_stats["region_pop"]

    # sqrt(population)-weighted totals used for the risk maps
    pop_sqrt = np.sqrt(df_stats["region_pop"])
    for src_col, dst_col in [
        ("mild_years_total", "mild_years_poproot"),
        ("moderate_years_total", "moderate_years_poproot"),
        ("severe_years_total", "severe_years_poproot"),
        ("extreme_years_total", "extreme_years_poproot"),
    ]:
        df_stats[dst_col] = df_stats[src_col] * pop_sqrt
    df_stats.to_csv(OUT_STATS_CSV, index=False)
    print(f"[INFO] Saved drought-year stats to {OUT_STATS_CSV}")
    print(df_stats.head())