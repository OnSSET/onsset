"""Climate risk algorithm for OnSSET prioritization.

This module processes climate data (temperature, drought, etc.) from CSV files,
aggregates it to admin-3 level (municipality), calculates risk scores, and
provides prioritization data for electrification planning.

Data flow:
    1. GUI runner prompts for climate data folder + admin-3 shapefile
    2. ClimateDataLoader reads all CSVs, detects temporal resolution
    3. ClimateAggregator averages data per admin-3 area
    4. ClimateRiskCalculator computes individual and compound risk scores
    5. Results are mapped to population clusters for use in onsset.py

Configuration:
    All thresholds and parameters are read from the 'ClimateData' sheet in the
    specs Excel file. See specs.py for column name constants.
"""

import os
import logging
from enum import Enum
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from scipy.stats import gamma, norm

# Import specs constants for climate configuration
try:
    from onsset.specs import (
        SPE_CLIM_HW_THRESHOLD, SPE_CLIM_HW_DURATION, SPE_CLIM_HW_TEMP_COL,
        SPE_CLIM_HW_CAT1_LOW, SPE_CLIM_HW_CAT1_HIGH, SPE_CLIM_HW_CAT2_LOW,
        SPE_CLIM_HW_CAT2_HIGH, SPE_CLIM_HW_CAT3_LOW, SPE_CLIM_HW_CAT3_HIGH,
        SPE_CLIM_HW_CAT4_LOW, SPE_CLIM_SPI_SCALE, SPE_CLIM_SPI_BASELINE_START,
        SPE_CLIM_SPI_BASELINE_END, SPE_CLIM_SPI_PRECIP_COL,
        SPE_CLIM_SPI_DROUGHT_THRESHOLD, SPE_CLIM_SPI_MILD_THRESHOLD,
        SPE_CLIM_SPI_MODERATE_THRESHOLD, SPE_CLIM_SPI_SEVERE_THRESHOLD,
        SPE_CLIM_LAT_COL, SPE_CLIM_LON_COL, SPE_CLIM_DATE_COL,
        SPE_CLIM_ADMIN3_ID_COL, SPE_CLIM_ADMIN3_NAME_COL,
        SPE_CLIM_HW_WEIGHT, SPE_CLIM_DROUGHT_WEIGHT
    )
except ImportError:
    from specs import (
        SPE_CLIM_HW_THRESHOLD, SPE_CLIM_HW_DURATION, SPE_CLIM_HW_TEMP_COL,
        SPE_CLIM_HW_CAT1_LOW, SPE_CLIM_HW_CAT1_HIGH, SPE_CLIM_HW_CAT2_LOW,
        SPE_CLIM_HW_CAT2_HIGH, SPE_CLIM_HW_CAT3_LOW, SPE_CLIM_HW_CAT3_HIGH,
        SPE_CLIM_HW_CAT4_LOW, SPE_CLIM_SPI_SCALE, SPE_CLIM_SPI_BASELINE_START,
        SPE_CLIM_SPI_BASELINE_END, SPE_CLIM_SPI_PRECIP_COL,
        SPE_CLIM_SPI_DROUGHT_THRESHOLD, SPE_CLIM_SPI_MILD_THRESHOLD,
        SPE_CLIM_SPI_MODERATE_THRESHOLD, SPE_CLIM_SPI_SEVERE_THRESHOLD,
        SPE_CLIM_LAT_COL, SPE_CLIM_LON_COL, SPE_CLIM_DATE_COL,
        SPE_CLIM_ADMIN3_ID_COL, SPE_CLIM_ADMIN3_NAME_COL,
        SPE_CLIM_HW_WEIGHT, SPE_CLIM_DROUGHT_WEIGHT
    )

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================

class TemporalResolution(Enum):
    """Detected temporal resolution of climate data."""
    HOURLY = 'hourly'
    DAILY = 'daily'
    MONTHLY = 'monthly'
    YEARLY = 'yearly'
    UNKNOWN = 'unknown'


# Output column names (for integration with onsset.py)
SET_CLIMATE_RISK = 'ClimateRisk'  # Compound risk score
SET_CLIMATE_RISK_HEATWAVE = 'ClimateRiskHeatwave'  # Individual risk
SET_CLIMATE_RISK_DROUGHT = 'ClimateRiskDrought'  # Individual risk
SET_ADMIN3_ID = 'Admin3ID'  # Municipality identifier

# Global variable for detected temporal resolution
_temporal_resolution: TemporalResolution = TemporalResolution.UNKNOWN


# =============================================================================
# DEFAULT CONFIGURATION VALUES
# =============================================================================

DEFAULT_CONFIG = {
    # Heatwave defaults
    'heatwave_threshold_c': 32.0,
    'heatwave_duration_days': 3,
    'temp_column': 't2m_max_C',
    'hw_cat1_low': 32.0,
    'hw_cat1_high': 35.0,
    'hw_cat2_low': 35.0,
    'hw_cat2_high': 38.0,
    'hw_cat3_low': 38.0,
    'hw_cat3_high': 42.0,
    'hw_cat4_low': 42.0,

    # SPI defaults
    'spi_scale': 3,
    'spi_baseline_start': 1950,
    'spi_baseline_end': 2000,
    'precip_column': 'tp_mm_month',
    'spi_drought_threshold': -1.0,
    'spi_mild_threshold': -1.5,
    'spi_moderate_threshold': -2.0,
    'spi_severe_threshold': -2.5,

    # Common defaults
    'lat_column': 'latitude',
    'lon_column': 'longitude',
    'date_column': 'date',
    'admin3_id_column': 'GID_3',
    'admin3_name_column': 'NAME_3',

    # Risk weights
    'heatwave_weight': 0.5,
    'drought_weight': 0.5,
}


def load_climate_config(specs_path: Optional[str] = None) -> Dict:
    """Load climate configuration from specs file or use defaults.

    Args:
        specs_path: Path to specs Excel file. If None, use defaults.

    Returns:
        Dictionary with configuration values.
    """
    config = DEFAULT_CONFIG.copy()

    if specs_path is None or not os.path.exists(specs_path):
        logger.info("Using default climate configuration values")
        return config

    try:
        climate_data = pd.read_excel(specs_path, sheet_name='ClimateData')
        if climate_data.empty:
            logger.warning("ClimateData sheet is empty, using defaults")
            return config

        row = climate_data.iloc[0]

        # Map specs columns to config keys
        mappings = {
            SPE_CLIM_HW_THRESHOLD: 'heatwave_threshold_c',
            SPE_CLIM_HW_DURATION: 'heatwave_duration_days',
            SPE_CLIM_HW_TEMP_COL: 'temp_column',
            SPE_CLIM_HW_CAT1_LOW: 'hw_cat1_low',
            SPE_CLIM_HW_CAT1_HIGH: 'hw_cat1_high',
            SPE_CLIM_HW_CAT2_LOW: 'hw_cat2_low',
            SPE_CLIM_HW_CAT2_HIGH: 'hw_cat2_high',
            SPE_CLIM_HW_CAT3_LOW: 'hw_cat3_low',
            SPE_CLIM_HW_CAT3_HIGH: 'hw_cat3_high',
            SPE_CLIM_HW_CAT4_LOW: 'hw_cat4_low',
            SPE_CLIM_SPI_SCALE: 'spi_scale',
            SPE_CLIM_SPI_BASELINE_START: 'spi_baseline_start',
            SPE_CLIM_SPI_BASELINE_END: 'spi_baseline_end',
            SPE_CLIM_SPI_PRECIP_COL: 'precip_column',
            SPE_CLIM_SPI_DROUGHT_THRESHOLD: 'spi_drought_threshold',
            SPE_CLIM_SPI_MILD_THRESHOLD: 'spi_mild_threshold',
            SPE_CLIM_SPI_MODERATE_THRESHOLD: 'spi_moderate_threshold',
            SPE_CLIM_SPI_SEVERE_THRESHOLD: 'spi_severe_threshold',
            SPE_CLIM_LAT_COL: 'lat_column',
            SPE_CLIM_LON_COL: 'lon_column',
            SPE_CLIM_DATE_COL: 'date_column',
            SPE_CLIM_ADMIN3_ID_COL: 'admin3_id_column',
            SPE_CLIM_ADMIN3_NAME_COL: 'admin3_name_column',
            SPE_CLIM_HW_WEIGHT: 'heatwave_weight',
            SPE_CLIM_DROUGHT_WEIGHT: 'drought_weight',
        }

        for spec_col, config_key in mappings.items():
            if spec_col in row.index and pd.notna(row[spec_col]):
                config[config_key] = row[spec_col]

        logger.info("Loaded climate configuration from specs file")

    except Exception as e:
        logger.warning(f"Failed to load ClimateData sheet: {e}. Using defaults.")

    return config


# =============================================================================
# DATA LOADING
# =============================================================================

class ClimateDataLoader:
    """Loads and validates climate data from a folder of CSV files.

    Memory-efficient: classifies files by type and loads them separately
    to avoid memory issues with large datasets.
    """

    def __init__(self, folder_path: str, config: Dict):
        """
        Args:
            folder_path: Path to folder containing climate CSV files.
            config: Configuration dictionary from load_climate_config().
        """
        self.folder_path = folder_path
        self.config = config
        self.dataframes: List[pd.DataFrame] = []
        self.temporal_resolution: TemporalResolution = TemporalResolution.UNKNOWN
        self.detected_columns: Dict[str, str] = {}

        # Classified file lists
        self.daily_temp_files: List[str] = []
        self.monthly_precip_files: List[str] = []
        self.monthly_pev_files: List[str] = []
        self.other_files: List[str] = []

    def _classify_files(self) -> None:
        """Classify files by type based on filename patterns."""
        if not os.path.isdir(self.folder_path):
            raise ValueError(f"Climate data folder not found: {self.folder_path}")

        csv_files = [f for f in os.listdir(self.folder_path) if f.endswith('.csv')]
        excel_files = [f for f in os.listdir(self.folder_path)
                       if f.endswith(('.xlsx', '.xls'))]
        all_files = csv_files + excel_files

        if not all_files:
            raise ValueError(f"No CSV or Excel files found in {self.folder_path}")

        for filename in all_files:
            fname_lower = filename.lower()
            # Classify by known patterns
            if 't2m' in fname_lower and ('daily' in fname_lower or 'max' in fname_lower):
                self.daily_temp_files.append(filename)
            elif 'tp_' in fname_lower and 'monthly' in fname_lower:
                self.monthly_precip_files.append(filename)
            elif 'pev' in fname_lower and 'monthly' in fname_lower:
                self.monthly_pev_files.append(filename)
            else:
                self.other_files.append(filename)

        # Sort files for consistent processing order
        self.daily_temp_files.sort()
        self.monthly_precip_files.sort()
        self.monthly_pev_files.sort()
        self.other_files.sort()

        logger.info(f"Classified files: {len(self.daily_temp_files)} daily temp, "
                   f"{len(self.monthly_precip_files)} monthly precip, "
                   f"{len(self.monthly_pev_files)} monthly PEV, "
                   f"{len(self.other_files)} other")

    def load_all_files(self) -> pd.DataFrame:
        """Load all CSV/Excel files from the folder and combine into single DataFrame.

        WARNING: This method loads ALL files at once. For large datasets with
        mixed temporal resolutions, use load_daily_temp_files() and
        load_monthly_precip_files() separately instead.

        Returns:
            Combined DataFrame with all climate data.
        """
        if not os.path.isdir(self.folder_path):
            raise ValueError(f"Climate data folder not found: {self.folder_path}")

        csv_files = [f for f in os.listdir(self.folder_path) if f.endswith('.csv')]
        excel_files = [f for f in os.listdir(self.folder_path)
                       if f.endswith(('.xlsx', '.xls'))]

        if not csv_files and not excel_files:
            raise ValueError(f"No CSV or Excel files found in {self.folder_path}")

        logger.info(f"Found {len(csv_files)} CSV files and {len(excel_files)} Excel files")

        for filename in csv_files:
            filepath = os.path.join(self.folder_path, filename)
            try:
                df = pd.read_csv(filepath)
                self.dataframes.append(df)
                logger.info(f"Loaded {filename}: {len(df)} rows")
            except Exception as e:
                logger.warning(f"Failed to load {filename}: {e}")

        for filename in excel_files:
            filepath = os.path.join(self.folder_path, filename)
            try:
                df = pd.read_excel(filepath)
                self.dataframes.append(df)
                logger.info(f"Loaded {filename}: {len(df)} rows")
            except Exception as e:
                logger.warning(f"Failed to load {filename}: {e}")

        if not self.dataframes:
            raise ValueError("No climate data files could be loaded")

        combined_df = pd.concat(self.dataframes, ignore_index=True)
        logger.info(f"Combined climate data: {len(combined_df)} total rows")

        self._detect_columns(combined_df)
        self.temporal_resolution = self.detect_temporal_resolution(combined_df)

        return combined_df

    def _load_file(self, filename: str) -> Optional[pd.DataFrame]:
        """Load a single file (CSV or Excel)."""
        filepath = os.path.join(self.folder_path, filename)
        try:
            if filename.endswith('.csv'):
                return pd.read_csv(filepath)
            else:
                return pd.read_excel(filepath)
        except Exception as e:
            logger.warning(f"Failed to load {filename}: {e}")
            return None

    def load_monthly_precip_files(self) -> pd.DataFrame:
        """Load only monthly precipitation files (memory-efficient for drought analysis).

        Returns:
            Combined DataFrame with monthly precipitation data.
        """
        if not self.monthly_precip_files:
            self._classify_files()

        if not self.monthly_precip_files:
            logger.warning("No monthly precipitation files found")
            return pd.DataFrame()

        dfs = []
        for filename in self.monthly_precip_files:
            df = self._load_file(filename)
            if df is not None:
                dfs.append(df)
                logger.info(f"Loaded {filename}: {len(df)} rows")

        if not dfs:
            return pd.DataFrame()

        combined = pd.concat(dfs, ignore_index=True)
        logger.info(f"Combined monthly precip data: {len(combined)} total rows")

        self._detect_columns(combined)
        return combined

    def iter_daily_temp_files(self):
        """Iterate over daily temperature files one at a time (memory-efficient).

        Yields:
            Tuple of (filename, DataFrame) for each daily temperature file.
        """
        if not self.daily_temp_files:
            self._classify_files()

        for filename in self.daily_temp_files:
            df = self._load_file(filename)
            if df is not None:
                logger.info(f"Loaded {filename}: {len(df)} rows")
                yield filename, df

    def get_sample_for_column_detection(self) -> pd.DataFrame:
        """Load a small sample to detect column names without loading all data.

        Returns:
            Sample DataFrame for column detection.
        """
        self._classify_files()

        # Try to get a sample from each type
        sample_files = []
        if self.daily_temp_files:
            sample_files.append(self.daily_temp_files[0])
        if self.monthly_precip_files:
            sample_files.append(self.monthly_precip_files[0])
        if not sample_files and self.other_files:
            sample_files.append(self.other_files[0])

        dfs = []
        for filename in sample_files:
            df = self._load_file(filename)
            if df is not None:
                dfs.append(df.head(1000))  # Only take first 1000 rows

        if not dfs:
            raise ValueError("Could not load any sample files for column detection")

        sample_df = pd.concat(dfs, ignore_index=True)
        self._detect_columns(sample_df)
        return sample_df

    def has_daily_temp_data(self) -> bool:
        """Check if daily temperature data is available."""
        if not self.daily_temp_files:
            self._classify_files()
        return len(self.daily_temp_files) > 0

    def has_monthly_precip_data(self) -> bool:
        """Check if monthly precipitation data is available."""
        if not self.monthly_precip_files:
            self._classify_files()
        return len(self.monthly_precip_files) > 0

    def _detect_columns(self, df: pd.DataFrame):
        """Auto-detect column names for lat, lon, date, temp, precip."""
        columns = df.columns.tolist()
        columns_lower = [c.lower() for c in columns]

        # Latitude detection
        lat_options = [self.config['lat_column'], 'latitude', 'lat', 'y', 'y_deg']
        for opt in lat_options:
            if opt.lower() in columns_lower:
                idx = columns_lower.index(opt.lower())
                self.detected_columns['latitude'] = columns[idx]
                break

        # Longitude detection
        lon_options = [self.config['lon_column'], 'longitude', 'lon', 'x', 'x_deg']
        for opt in lon_options:
            if opt.lower() in columns_lower:
                idx = columns_lower.index(opt.lower())
                self.detected_columns['longitude'] = columns[idx]
                break

        # Date detection
        date_options = [self.config['date_column'], 'date', 'timestamp', 'time', 'datetime']
        for opt in date_options:
            if opt.lower() in columns_lower:
                idx = columns_lower.index(opt.lower())
                self.detected_columns['date'] = columns[idx]
                break

        # Temperature detection
        temp_options = [self.config['temp_column'], 't2m_max_c', 'temperature', 'temp', 'tmax']
        for opt in temp_options:
            if opt.lower() in columns_lower:
                idx = columns_lower.index(opt.lower())
                self.detected_columns['temperature'] = columns[idx]
                break

        # Precipitation detection
        precip_options = [self.config['precip_column'], 'tp_mm_month', 'precipitation', 'precip', 'rainfall']
        for opt in precip_options:
            if opt.lower() in columns_lower:
                idx = columns_lower.index(opt.lower())
                self.detected_columns['precipitation'] = columns[idx]
                break

        logger.info(f"Detected columns: {self.detected_columns}")

    def detect_temporal_resolution(self, df: pd.DataFrame) -> TemporalResolution:
        """Analyze date column to determine data resolution.

        Args:
            df: DataFrame with date column.

        Returns:
            Detected TemporalResolution enum value.
        """
        global _temporal_resolution

        date_col = self.detected_columns.get('date')
        if date_col is None or date_col not in df.columns:
            logger.warning("No date column found, defaulting to UNKNOWN resolution")
            _temporal_resolution = TemporalResolution.UNKNOWN
            return _temporal_resolution

        try:
            timestamps = pd.to_datetime(df[date_col])
        except Exception as e:
            logger.warning(f"Failed to parse timestamps: {e}")
            _temporal_resolution = TemporalResolution.UNKNOWN
            return _temporal_resolution

        timestamps_sorted = timestamps.sort_values().reset_index(drop=True)
        if len(timestamps_sorted) < 2:
            logger.warning("Not enough timestamps to detect resolution")
            _temporal_resolution = TemporalResolution.UNKNOWN
            return _temporal_resolution

        time_diffs = timestamps_sorted.diff().dropna()
        median_diff_hours = time_diffs.median().total_seconds() / 3600

        if median_diff_hours < 2:
            _temporal_resolution = TemporalResolution.HOURLY
        elif median_diff_hours < 48:
            _temporal_resolution = TemporalResolution.DAILY
        elif median_diff_hours < 45 * 24:
            _temporal_resolution = TemporalResolution.MONTHLY
        else:
            _temporal_resolution = TemporalResolution.YEARLY

        logger.info(f"Detected temporal resolution: {_temporal_resolution.value} "
                   f"(median diff: {median_diff_hours:.1f} hours)")
        return _temporal_resolution


# =============================================================================
# HEATWAVE RISK CALCULATION
# =============================================================================

def calculate_heatwave_risk(
    climate_df: pd.DataFrame,
    admin3_gdf: gpd.GeoDataFrame,
    config: Dict,
    detected_columns: Dict[str, str]
) -> pd.DataFrame:
    """Calculate heatwave risk scores per admin-3 region.

    This function:
    1. Assigns climate data points to admin-3 regions via spatial join
    2. Calculates region-mean daily max temperatures
    3. Counts heatwave days (temp > threshold)
    4. Calculates 3-day rolling mean temperatures and categorizes
    5. Produces normalized risk score (0-1)

    Args:
        climate_df: DataFrame with daily temperature data.
        admin3_gdf: GeoDataFrame with admin-3 boundaries.
        config: Configuration dictionary.
        detected_columns: Dict mapping standard names to actual column names.

    Returns:
        DataFrame with columns: admin3_id, admin3_name, heatwave_risk (0-1)
    """
    logger.info("Calculating heatwave risk...")

    lat_col = detected_columns.get('latitude')
    lon_col = detected_columns.get('longitude')
    date_col = detected_columns.get('date')
    temp_col = detected_columns.get('temperature')
    admin3_id_col = config['admin3_id_column']
    admin3_name_col = config['admin3_name_column']

    if temp_col is None or temp_col not in climate_df.columns:
        logger.warning("No temperature column found, skipping heatwave calculation")
        return pd.DataFrame(columns=[admin3_id_col, admin3_name_col, 'heatwave_risk'])

    # Build cell-to-region lookup
    cells = climate_df[[lat_col, lon_col]].drop_duplicates().reset_index(drop=True)
    gdf_cells = gpd.GeoDataFrame(
        cells,
        geometry=gpd.points_from_xy(cells[lon_col], cells[lat_col]),
        crs="EPSG:4326"
    )

    # Ensure admin3 is in correct CRS
    if admin3_gdf.crs is None or admin3_gdf.crs.to_epsg() != 4326:
        admin3_gdf = admin3_gdf.to_crs(epsg=4326)

    gdf_join = gpd.sjoin(
        gdf_cells,
        admin3_gdf[[admin3_id_col, admin3_name_col, 'geometry']],
        how="inner",
        predicate="within"
    )

    cell_region_lookup = gdf_join[[lat_col, lon_col, admin3_id_col, admin3_name_col]].copy()
    logger.info(f"Cell-region lookup rows: {len(cell_region_lookup)}")

    # Parse dates and merge with region lookup
    df = climate_df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.merge(cell_region_lookup, on=[lat_col, lon_col], how='left')
    df = df.dropna(subset=[admin3_id_col])

    if df.empty:
        logger.warning("No data after spatial join, returning empty heatwave risk")
        return pd.DataFrame(columns=[admin3_id_col, admin3_name_col, 'heatwave_risk'])

    df['year'] = df[date_col].dt.year
    years = sorted(df['year'].unique())

    # Region accumulators
    region_stats = defaultdict(lambda: {
        'heatwave_days_total': 0,
        'years_with_data': 0,
        'max3day_list': [],
    })

    hw_threshold = config['heatwave_threshold_c']

    for year in years:
        df_year = df[df['year'] == year].copy()
        if df_year.empty:
            continue

        # Region-mean daily max temperature
        reg_day = (
            df_year.groupby([admin3_id_col, admin3_name_col, date_col], as_index=False)[temp_col]
            .mean()
            .rename(columns={temp_col: 'tmax_reg_C'})
        )

        # Count heatwave days (temp > threshold)
        hw_mask = reg_day['tmax_reg_C'] > hw_threshold
        hw_days = (
            reg_day[hw_mask]
            .groupby([admin3_id_col, admin3_name_col], as_index=False)[date_col]
            .nunique()
            .rename(columns={date_col: 'heatwave_days_year'})
        )
        hw_days_dict = {
            (row[admin3_id_col], row[admin3_name_col]): int(row['heatwave_days_year'])
            for _, row in hw_days.iterrows()
        }

        # Max 3-day rolling mean per region
        max3day_this_year = {}
        for (gid, name), df_reg in reg_day.groupby([admin3_id_col, admin3_name_col], sort=False):
            s = df_reg.sort_values(date_col).set_index(date_col)['tmax_reg_C']
            if len(s) < 3:
                continue
            roll3 = s.rolling(window=3, min_periods=3).mean()
            max_val = float(roll3.max())
            if np.isfinite(max_val):
                max3day_this_year[(gid, name)] = max_val

        # Update accumulators
        regions_in_year = set(
            tuple(x) for x in reg_day[[admin3_id_col, admin3_name_col]].drop_duplicates().values
        )

        for key in regions_in_year:
            gid, name = key
            stats = region_stats[key]
            stats['heatwave_days_total'] += hw_days_dict.get(key, 0)
            stats['years_with_data'] += 1
            if key in max3day_this_year:
                stats['max3day_list'].append(max3day_this_year[key])

    # Build stats DataFrame
    rows = []
    for (gid, name), stats in region_stats.items():
        years_count = stats['years_with_data']
        if years_count == 0:
            mean_hw_days = 0
            mean_max3day = 0
        else:
            mean_hw_days = stats['heatwave_days_total'] / years_count
            mean_max3day = (
                float(np.mean(stats['max3day_list']))
                if stats['max3day_list'] else 0
            )

        rows.append({
            admin3_id_col: gid,
            admin3_name_col: name,
            'mean_heatwave_days_per_year': mean_hw_days,
            'mean_max_3day_T_C': mean_max3day,
            'years_with_data': years_count,
        })

    df_heat = pd.DataFrame(rows)

    if df_heat.empty:
        logger.warning("No heatwave stats computed")
        return pd.DataFrame(columns=[admin3_id_col, admin3_name_col, 'heatwave_risk'])

    # Normalize to 0-1 risk score using min-max normalization
    # NOTE: Using min-max normalization. Consider revisiting for percentile-based approach.
    hw_days_col = 'mean_heatwave_days_per_year'
    min_val = df_heat[hw_days_col].min()
    max_val = df_heat[hw_days_col].max()

    if max_val > min_val:
        df_heat['heatwave_risk'] = (df_heat[hw_days_col] - min_val) / (max_val - min_val)
    else:
        df_heat['heatwave_risk'] = 0.0

    logger.info(f"Computed heatwave risk for {len(df_heat)} regions")

    return df_heat[[admin3_id_col, admin3_name_col, 'heatwave_risk',
                    'mean_heatwave_days_per_year', 'mean_max_3day_T_C']]


def calculate_heatwave_risk_incremental(
    loader: 'ClimateDataLoader',
    admin3_gdf: gpd.GeoDataFrame,
    config: Dict,
    detected_columns: Dict[str, str]
) -> pd.DataFrame:
    """Memory-efficient heatwave risk calculation processing files one at a time.

    This function processes daily temperature files incrementally to avoid
    loading all data into memory at once.

    Args:
        loader: ClimateDataLoader instance with classified files.
        admin3_gdf: GeoDataFrame with admin-3 boundaries.
        config: Configuration dictionary.
        detected_columns: Dict mapping standard names to actual column names.

    Returns:
        DataFrame with columns: admin3_id, admin3_name, heatwave_risk (0-1)
    """
    logger.info("Calculating heatwave risk (incremental mode)...")

    lat_col = detected_columns.get('latitude')
    lon_col = detected_columns.get('longitude')
    date_col = detected_columns.get('date')
    temp_col = detected_columns.get('temperature')
    admin3_id_col = config['admin3_id_column']
    admin3_name_col = config['admin3_name_column']
    hw_threshold = config['heatwave_threshold_c']

    # Ensure admin3 is in correct CRS
    if admin3_gdf.crs is None or admin3_gdf.crs.to_epsg() != 4326:
        admin3_gdf = admin3_gdf.to_crs(epsg=4326)

    # Build cell-to-region lookup from first file
    cell_region_lookup = None

    # Region accumulators (persist across all files)
    region_stats = defaultdict(lambda: {
        'heatwave_days_total': 0,
        'years_with_data': set(),  # Use set to track unique years
        'max3day_list': [],
    })

    files_processed = 0

    for filename, df in loader.iter_daily_temp_files():
        if temp_col is None:
            # Auto-detect from first file
            for col in df.columns:
                if 't2m' in col.lower() or 'temp' in col.lower():
                    temp_col = col
                    detected_columns['temperature'] = temp_col
                    break

        if temp_col is None or temp_col not in df.columns:
            logger.warning(f"No temperature column found in {filename}, skipping")
            continue

        # Build cell-region lookup once from first file's coordinates
        if cell_region_lookup is None:
            cells = df[[lat_col, lon_col]].drop_duplicates().reset_index(drop=True)
            gdf_cells = gpd.GeoDataFrame(
                cells,
                geometry=gpd.points_from_xy(cells[lon_col], cells[lat_col]),
                crs="EPSG:4326"
            )

            gdf_join = gpd.sjoin(
                gdf_cells,
                admin3_gdf[[admin3_id_col, admin3_name_col, 'geometry']],
                how="inner",
                predicate="within"
            )

            cell_region_lookup = gdf_join[[lat_col, lon_col, admin3_id_col, admin3_name_col]].copy()
            logger.info(f"Built cell-region lookup: {len(cell_region_lookup)} cells mapped to regions")

        # Parse dates and merge with region lookup
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.merge(cell_region_lookup, on=[lat_col, lon_col], how='inner')

        if df.empty:
            continue

        df['year'] = df[date_col].dt.year
        years = sorted(df['year'].unique())

        # Process each year in this file
        for year in years:
            df_year = df[df['year'] == year].copy()
            if df_year.empty:
                continue

            # Region-mean daily max temperature
            reg_day = (
                df_year.groupby([admin3_id_col, admin3_name_col, date_col], as_index=False)[temp_col]
                .mean()
                .rename(columns={temp_col: 'tmax_reg_C'})
            )

            # Count heatwave days (temp > threshold)
            hw_mask = reg_day['tmax_reg_C'] > hw_threshold
            hw_days = (
                reg_day[hw_mask]
                .groupby([admin3_id_col, admin3_name_col], as_index=False)[date_col]
                .nunique()
                .rename(columns={date_col: 'heatwave_days_year'})
            )
            hw_days_dict = {
                (row[admin3_id_col], row[admin3_name_col]): int(row['heatwave_days_year'])
                for _, row in hw_days.iterrows()
            }

            # Max 3-day rolling mean per region
            max3day_this_year = {}
            for (gid, name), df_reg in reg_day.groupby([admin3_id_col, admin3_name_col], sort=False):
                s = df_reg.sort_values(date_col).set_index(date_col)['tmax_reg_C']
                if len(s) < 3:
                    continue
                roll3 = s.rolling(window=3, min_periods=3).mean()
                max_val = float(roll3.max())
                if np.isfinite(max_val):
                    max3day_this_year[(gid, name)] = max_val

            # Update accumulators
            regions_in_year = set(
                tuple(x) for x in reg_day[[admin3_id_col, admin3_name_col]].drop_duplicates().values
            )

            for key in regions_in_year:
                gid, name = key
                stats = region_stats[key]
                stats['heatwave_days_total'] += hw_days_dict.get(key, 0)
                stats['years_with_data'].add(year)
                if key in max3day_this_year:
                    stats['max3day_list'].append(max3day_this_year[key])

        files_processed += 1
        # Free memory after processing each file
        del df

    logger.info(f"Processed {files_processed} daily temperature files")

    if not region_stats:
        logger.warning("No heatwave stats computed")
        return pd.DataFrame(columns=[admin3_id_col, admin3_name_col, 'heatwave_risk'])

    # Build stats DataFrame
    rows = []
    for (gid, name), stats in region_stats.items():
        years_count = len(stats['years_with_data'])
        if years_count == 0:
            mean_hw_days = 0
            mean_max3day = 0
        else:
            mean_hw_days = stats['heatwave_days_total'] / years_count
            mean_max3day = (
                float(np.mean(stats['max3day_list']))
                if stats['max3day_list'] else 0
            )

        rows.append({
            admin3_id_col: gid,
            admin3_name_col: name,
            'mean_heatwave_days_per_year': mean_hw_days,
            'mean_max_3day_T_C': mean_max3day,
            'years_with_data': years_count,
        })

    df_heat = pd.DataFrame(rows)

    if df_heat.empty:
        logger.warning("No heatwave stats computed")
        return pd.DataFrame(columns=[admin3_id_col, admin3_name_col, 'heatwave_risk'])

    # Normalize to 0-1 risk score
    hw_days_col = 'mean_heatwave_days_per_year'
    min_val = df_heat[hw_days_col].min()
    max_val = df_heat[hw_days_col].max()

    if max_val > min_val:
        df_heat['heatwave_risk'] = (df_heat[hw_days_col] - min_val) / (max_val - min_val)
    else:
        df_heat['heatwave_risk'] = 0.0

    logger.info(f"Computed heatwave risk for {len(df_heat)} regions")

    return df_heat[[admin3_id_col, admin3_name_col, 'heatwave_risk',
                    'mean_heatwave_days_per_year', 'mean_max_3day_T_C']]


# =============================================================================
# SPI DROUGHT RISK CALCULATION
# =============================================================================

def _compute_spi_for_cell(
    df_cell: pd.DataFrame,
    date_col: str,
    precip_col: str,
    scale: int,
    baseline_start: int,
    baseline_end: int,
) -> pd.DataFrame:
    """Compute SPI-k for one grid cell.

    Args:
        df_cell: DataFrame for one cell with date and precipitation columns.
        date_col: Name of date column.
        precip_col: Name of precipitation column.
        scale: SPI accumulation period in months.
        baseline_start: Start year for gamma distribution fitting.
        baseline_end: End year for gamma distribution fitting.

    Returns:
        DataFrame with: date, year, month, P_k, spi
    """
    df = df_cell.sort_values(date_col).set_index(date_col)

    # Full continuous monthly index
    full_index = pd.date_range(df.index.min(), df.index.max(), freq='MS')
    df = df.reindex(full_index)

    # Fill missing precip with 0 mm
    df[precip_col] = df[precip_col].fillna(0.0)
    df['year'] = df.index.year
    df['month'] = df.index.month

    # k-month rolling accumulation
    df['P_k'] = df[precip_col].rolling(window=scale, min_periods=scale).sum()
    df['spi'] = np.nan

    # Compute SPI separately for each calendar month
    for m in range(1, 13):
        mask_month = df['month'] == m
        if not mask_month.any():
            continue

        series = df.loc[mask_month, 'P_k']

        # Baseline subset for fitting
        baseline_mask = (
            mask_month &
            (df['year'] >= baseline_start) &
            (df['year'] <= baseline_end)
        )
        baseline_values = df.loc[baseline_mask, 'P_k'].dropna()

        if len(baseline_values) < 10:
            continue

        positive = baseline_values[baseline_values > 0]
        if len(positive) < 2:
            continue

        # Gamma fit: shape, loc=0, scale
        try:
            shape, loc, scale_param = gamma.fit(positive, floc=0)
        except Exception:
            continue

        q = len(positive) / len(baseline_values)  # non-zero probability

        x = series.values
        x_clipped = np.maximum(x, 0.0001)

        G = gamma.cdf(x_clipped, shape, loc=0, scale=scale_param)

        # Mixed distribution: mass at zero
        H = (1.0 - q) + q * G
        H[x <= 0] = (1.0 - q)

        H = np.clip(H, 1e-6, 1 - 1e-6)
        spi_vals = norm.ppf(H)

        df.loc[series.index, 'spi'] = spi_vals

    df = df.dropna(subset=['P_k', 'spi']).reset_index().rename(columns={'index': 'date'})
    return df[['date', 'year', 'month', 'P_k', 'spi']]


def calculate_spi_drought_risk(
    climate_df: pd.DataFrame,
    admin3_gdf: gpd.GeoDataFrame,
    config: Dict,
    detected_columns: Dict[str, str]
) -> pd.DataFrame:
    """Calculate SPI-based drought risk scores per admin-3 region.

    This function:
    1. Computes SPI-k (Standardized Precipitation Index) per grid cell
    2. Aggregates to admin-3 regions
    3. Counts drought years by intensity category
    4. Produces normalized risk score (0-1)

    Args:
        climate_df: DataFrame with monthly precipitation data.
        admin3_gdf: GeoDataFrame with admin-3 boundaries.
        config: Configuration dictionary.
        detected_columns: Dict mapping standard names to actual column names.

    Returns:
        DataFrame with columns: admin3_id, admin3_name, drought_risk (0-1)
    """
    logger.info("Calculating SPI drought risk...")

    lat_col = detected_columns.get('latitude')
    lon_col = detected_columns.get('longitude')
    date_col = detected_columns.get('date')
    precip_col = detected_columns.get('precipitation')
    admin3_id_col = config['admin3_id_column']
    admin3_name_col = config['admin3_name_column']

    if precip_col is None or precip_col not in climate_df.columns:
        logger.warning("No precipitation column found, skipping drought calculation")
        return pd.DataFrame(columns=[admin3_id_col, admin3_name_col, 'drought_risk'])

    # Parse dates
    df = climate_df.copy()

    # Check if date column exists; if not, try to construct from year/month columns
    if date_col is not None and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
        if 'year' not in df.columns:
            df['year'] = df[date_col].dt.year
        if 'month' not in df.columns:
            df['month'] = df[date_col].dt.month
    elif 'year' in df.columns and 'month' in df.columns:
        # Construct date from year and month columns
        logger.info("No date column found, constructing from year/month columns")
        df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
        date_col = 'date'
        detected_columns['date'] = 'date'
    else:
        logger.warning("No date column and no year/month columns found, skipping drought calculation")
        return pd.DataFrame(columns=[admin3_id_col, admin3_name_col, 'drought_risk'])

    # Compute SPI per grid cell
    spi_scale = int(config['spi_scale'])
    baseline_start = int(config['spi_baseline_start'])
    baseline_end = int(config['spi_baseline_end'])

    grouped_cells = df.groupby([lat_col, lon_col], sort=False)
    logger.info(f"Computing SPI-{spi_scale} for {len(grouped_cells)} grid cells...")

    cell_rows = []
    for (lat, lon), df_cell in grouped_cells:
        spi_df = _compute_spi_for_cell(
            df_cell, date_col, precip_col,
            spi_scale, baseline_start, baseline_end
        )
        if spi_df.empty:
            continue
        spi_df[lat_col] = lat
        spi_df[lon_col] = lon
        cell_rows.append(spi_df)

    if not cell_rows:
        logger.warning("No SPI computed for any cell")
        return pd.DataFrame(columns=[admin3_id_col, admin3_name_col, 'drought_risk'])

    cell_spi = pd.concat(cell_rows, ignore_index=True)
    logger.info(f"Total SPI records (cell-level): {len(cell_spi):,}")

    # Spatial join to admin-3
    gdf_cells = gpd.GeoDataFrame(
        cell_spi,
        geometry=gpd.points_from_xy(cell_spi[lon_col], cell_spi[lat_col]),
        crs="EPSG:4326"
    )

    if admin3_gdf.crs is None or admin3_gdf.crs.to_epsg() != 4326:
        admin3_gdf = admin3_gdf.to_crs(epsg=4326)

    gdf_join = gpd.sjoin(
        gdf_cells,
        admin3_gdf[[admin3_id_col, admin3_name_col, 'geometry']],
        how="inner",
        predicate="within"
    )

    # Aggregate to region-month (mean over cells)
    df_reg_month = (
        gdf_join
        .groupby([admin3_id_col, admin3_name_col, 'date'], as_index=False)['spi']
        .mean()
        .rename(columns={'spi': 'spi_region_mean'})
    )
    df_reg_month['year'] = df_reg_month['date'].dt.year

    # Get thresholds
    drought_threshold = config['spi_drought_threshold']
    mild_threshold = config['spi_mild_threshold']
    moderate_threshold = config['spi_moderate_threshold']
    severe_threshold = config['spi_severe_threshold']

    # Calculate drought stats per region
    regions = admin3_gdf[[admin3_id_col, admin3_name_col]].drop_duplicates().reset_index(drop=True)

    stats_rows = []
    for _, reg in regions.iterrows():
        gid = reg[admin3_id_col]
        name = reg[admin3_name_col]

        df_r = df_reg_month[df_reg_month[admin3_id_col] == gid].copy()
        if df_r.empty:
            stats_rows.append({
                admin3_id_col: gid,
                admin3_name_col: name,
                'years_with_data': 0,
                'drought_years_total': 0,
                'frac_drought_years': 0,
            })
            continue

        years_present = sorted(df_r['year'].unique())
        drought_years = 0

        for year in years_present:
            df_y = df_r[df_r['year'] == year]
            if df_y.empty:
                continue

            min_spi = df_y['spi_region_mean'].min()
            if np.isnan(min_spi):
                continue

            if min_spi <= drought_threshold:
                drought_years += 1

        years_with_data = len(years_present)
        frac_drought = drought_years / years_with_data if years_with_data > 0 else 0

        stats_rows.append({
            admin3_id_col: gid,
            admin3_name_col: name,
            'years_with_data': years_with_data,
            'drought_years_total': drought_years,
            'frac_drought_years': frac_drought,
        })

    df_stats = pd.DataFrame(stats_rows)

    if df_stats.empty:
        logger.warning("No drought stats computed")
        return pd.DataFrame(columns=[admin3_id_col, admin3_name_col, 'drought_risk'])

    # Normalize to 0-1 risk score using min-max normalization
    # NOTE: Using min-max normalization. Consider revisiting for percentile-based approach.
    min_val = df_stats['frac_drought_years'].min()
    max_val = df_stats['frac_drought_years'].max()

    if max_val > min_val:
        df_stats['drought_risk'] = (df_stats['frac_drought_years'] - min_val) / (max_val - min_val)
    else:
        df_stats['drought_risk'] = 0.0

    logger.info(f"Computed drought risk for {len(df_stats)} regions")

    return df_stats[[admin3_id_col, admin3_name_col, 'drought_risk',
                     'drought_years_total', 'frac_drought_years']]


# =============================================================================
# COMPOUND RISK & SETTLEMENT MAPPING
# =============================================================================

def calculate_compound_risk(
    heatwave_risk_df: pd.DataFrame,
    drought_risk_df: pd.DataFrame,
    config: Dict
) -> pd.DataFrame:
    """Combine heatwave and drought risks into compound risk score.

    Args:
        heatwave_risk_df: DataFrame with heatwave_risk column.
        drought_risk_df: DataFrame with drought_risk column.
        config: Configuration dictionary with risk weights.

    Returns:
        DataFrame with compound_risk column.
    """
    admin3_id_col = config['admin3_id_column']
    admin3_name_col = config['admin3_name_column']
    hw_weight = config['heatwave_weight']
    drought_weight = config['drought_weight']

    # Handle empty DataFrames
    if heatwave_risk_df.empty and drought_risk_df.empty:
        return pd.DataFrame(columns=[admin3_id_col, admin3_name_col, 'compound_risk'])

    if heatwave_risk_df.empty:
        df = drought_risk_df.copy()
        df['compound_risk'] = df['drought_risk']
        return df[[admin3_id_col, admin3_name_col, 'compound_risk', 'drought_risk']]

    if drought_risk_df.empty:
        df = heatwave_risk_df.copy()
        df['compound_risk'] = df['heatwave_risk']
        return df[[admin3_id_col, admin3_name_col, 'compound_risk', 'heatwave_risk']]

    # Merge on admin3 ID
    df = heatwave_risk_df[[admin3_id_col, admin3_name_col, 'heatwave_risk']].merge(
        drought_risk_df[[admin3_id_col, 'drought_risk']],
        on=admin3_id_col,
        how='outer'
    )

    # Fill missing values with 0
    df['heatwave_risk'] = df['heatwave_risk'].fillna(0)
    df['drought_risk'] = df['drought_risk'].fillna(0)

    # Weighted combination
    total_weight = hw_weight + drought_weight
    df['compound_risk'] = (
        (df['heatwave_risk'] * hw_weight + df['drought_risk'] * drought_weight)
        / total_weight
    )

    return df


def map_risk_to_settlements(
    settlements_df: pd.DataFrame,
    risk_df: pd.DataFrame,
    admin3_gdf: gpd.GeoDataFrame,
    config: Dict,
    lat_col: str = 'Y_deg',
    lon_col: str = 'X_deg'
) -> pd.DataFrame:
    """Map climate risk from admin-3 regions to settlements.

    Args:
        settlements_df: OnSSET settlements DataFrame.
        risk_df: DataFrame with risk scores per admin3.
        admin3_gdf: GeoDataFrame with admin-3 boundaries.
        config: Configuration dictionary.
        lat_col: Name of latitude column in settlements.
        lon_col: Name of longitude column in settlements.

    Returns:
        Settlements DataFrame with risk columns added.
    """
    admin3_id_col = config['admin3_id_column']

    # Convert settlements to GeoDataFrame
    gdf_settlements = gpd.GeoDataFrame(
        settlements_df,
        geometry=gpd.points_from_xy(settlements_df[lon_col], settlements_df[lat_col]),
        crs="EPSG:4326"
    )

    # Ensure admin3 is in correct CRS
    if admin3_gdf.crs is None or admin3_gdf.crs.to_epsg() != 4326:
        admin3_gdf = admin3_gdf.to_crs(epsg=4326)

    # Spatial join
    gdf_join = gpd.sjoin(
        gdf_settlements,
        admin3_gdf[[admin3_id_col, 'geometry']],
        how='left',
        predicate='within'
    )

    # Add admin3 ID to settlements
    settlements_df[SET_ADMIN3_ID] = gdf_join[admin3_id_col].values

    # Merge risk scores
    risk_cols = [c for c in risk_df.columns if 'risk' in c.lower()]
    merge_cols = [admin3_id_col] + risk_cols

    settlements_df = settlements_df.merge(
        risk_df[merge_cols],
        left_on=SET_ADMIN3_ID,
        right_on=admin3_id_col,
        how='left'
    )

    # Rename columns for OnSSET integration
    if 'compound_risk' in settlements_df.columns:
        settlements_df[SET_CLIMATE_RISK] = settlements_df['compound_risk']
    if 'heatwave_risk' in settlements_df.columns:
        settlements_df[SET_CLIMATE_RISK_HEATWAVE] = settlements_df['heatwave_risk']
    if 'drought_risk' in settlements_df.columns:
        settlements_df[SET_CLIMATE_RISK_DROUGHT] = settlements_df['drought_risk']

    # Fill NaN with 0 (settlements outside coverage)
    for col in [SET_CLIMATE_RISK, SET_CLIMATE_RISK_HEATWAVE, SET_CLIMATE_RISK_DROUGHT]:
        if col in settlements_df.columns:
            settlements_df[col] = settlements_df[col].fillna(0)

    logger.info(f"Mapped climate risk to {len(settlements_df)} settlements")

    return settlements_df


# =============================================================================
# MAIN PROCESSING FUNCTION
# =============================================================================

def process_climate_data(
    climate_folder: str,
    admin3_shapefile: str,
    settlements_df: pd.DataFrame,
    specs_path: Optional[str] = None
) -> pd.DataFrame:
    """Main entry point: process climate data and add risk to settlements.

    This function orchestrates the full pipeline:
    1. Load climate configuration from specs file
    2. Classify and load climate data files by type (memory-efficient)
    3. Run appropriate analysis for each data type
    4. Calculate risk scores
    5. Map to settlements

    Args:
        climate_folder: Path to folder with climate CSV files.
        admin3_shapefile: Path to admin-3 level shapefile.
        settlements_df: OnSSET settlements DataFrame.
        specs_path: Optional path to specs Excel file for configuration.

    Returns:
        Settlements DataFrame with climate risk columns added:
        - ClimateRisk (compound)
        - ClimateRiskHeatwave (individual)
        - ClimateRiskDrought (individual)
        - Admin3ID
    """
    logger.info("=" * 60)
    logger.info("Starting climate data processing...")
    logger.info("=" * 60)

    # Step 1: Load configuration
    config = load_climate_config(specs_path)

    # Step 2: Load admin-3 boundaries
    logger.info(f"Loading admin-3 shapefile: {admin3_shapefile}")
    admin3_gdf = gpd.read_file(admin3_shapefile)
    if admin3_gdf.crs is None or admin3_gdf.crs.to_epsg() != 4326:
        admin3_gdf = admin3_gdf.to_crs(epsg=4326)
    logger.info(f"Loaded {len(admin3_gdf)} admin-3 regions")

    # Step 3: Initialize loader and classify files
    loader = ClimateDataLoader(climate_folder, config)

    # Get a sample to detect column names
    sample_df = loader.get_sample_for_column_detection()
    detected_columns = loader.detected_columns

    heatwave_risk_df = pd.DataFrame()
    drought_risk_df = pd.DataFrame()

    # Step 4: Process daily temperature data for heatwave analysis (memory-efficient)
    if loader.has_daily_temp_data():
        logger.info("Daily temperature data detected - running incremental heatwave analysis")
        heatwave_risk_df = calculate_heatwave_risk_incremental(
            loader, admin3_gdf, config, detected_columns
        )

    # Step 5: Process monthly precipitation data for drought analysis
    if loader.has_monthly_precip_data():
        logger.info("Monthly precipitation data detected - running SPI drought analysis")
        monthly_precip_df = loader.load_monthly_precip_files()
        if not monthly_precip_df.empty:
            # Detect columns from the precip data if not already set
            loader._detect_columns(monthly_precip_df)
            detected_columns.update(loader.detected_columns)
            drought_risk_df = calculate_spi_drought_risk(
                monthly_precip_df, admin3_gdf, config, detected_columns
            )
            # Free memory
            del monthly_precip_df

    # Step 6: If no classified files, fall back to legacy loading (for small datasets)
    if heatwave_risk_df.empty and drought_risk_df.empty:
        if not loader.has_daily_temp_data() and not loader.has_monthly_precip_data():
            logger.warning("No classified climate files found. Attempting legacy load...")
            # Only for small datasets - this may fail for large datasets
            if len(loader.other_files) < 20:  # Safety threshold
                try:
                    climate_df = loader.load_all_files()
                    temporal_res = loader.temporal_resolution
                    detected_columns = loader.detected_columns

                    if temporal_res == TemporalResolution.DAILY:
                        heatwave_risk_df = calculate_heatwave_risk(
                            climate_df, admin3_gdf, config, detected_columns
                        )
                    elif temporal_res == TemporalResolution.MONTHLY:
                        drought_risk_df = calculate_spi_drought_risk(
                            climate_df, admin3_gdf, config, detected_columns
                        )
                except MemoryError:
                    logger.error("Memory error during legacy loading. Dataset too large.")
                    logger.error("Please ensure files follow naming conventions: "
                               "*t2m*daily*.csv for temperature, *tp*monthly*.csv for precipitation")

    # Step 7: Calculate compound risk
    compound_risk_df = calculate_compound_risk(
        heatwave_risk_df, drought_risk_df, config
    )

    # Step 8: Map to settlements
    settlements_df = map_risk_to_settlements(
        settlements_df, compound_risk_df, admin3_gdf, config
    )

    logger.info("=" * 60)
    logger.info("Climate data processing complete.")
    logger.info("=" * 60)

    return settlements_df


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_temporal_resolution() -> TemporalResolution:
    """Get the detected temporal resolution (global state)."""
    return _temporal_resolution


def get_risk_column_names() -> Dict[str, str]:
    """Get dictionary of risk column names for use in onsset.py."""
    return {
        'compound': SET_CLIMATE_RISK,
        'heatwave': SET_CLIMATE_RISK_HEATWAVE,
        'drought': SET_CLIMATE_RISK_DROUGHT,
        'admin3_id': SET_ADMIN3_ID,
    }
