import rasterio
from rasterio.features import rasterize
from pyproj import CRS

try:
    from onsset.pathfinder import *
except ModuleNotFoundError:
    from pathfinder import *
import pandas as pd

import geopandas as gpd
from shapely.geometry import Point



def create_geodataframe(df):
    geometry = [Point(xy) for xy in zip(df.X_deg, df.Y_deg)]
    crs = CRS('epsg:4326')
    df = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)

    return df


def find_grid_path(df, year, time_step, start_year, max_connections, max_capacity, gis_costs_path, power_cost_path,
                   mv_line_max_length, results_folder, full=True):

    name = 'extension_distance_' + '{}'.format(year)
    if name not in df.columns:
        df[name] = 99

    final_cost_path = os.path.join(gis_costs_path)

    if year - time_step == start_year:
        power_lines_raster = os.path.join(power_cost_path)
    else:
        power_lines_raster = os.path.join(results_folder, '{}_origins_{}.tif'.format(grid, year - time_step))

    with rasterio.open(final_cost_path) as cost:
        weights = cost.read(1) / 20
        weights_meta = cost.meta

    with rasterio.open(power_lines_raster) as power:
        power_lines = power.read(1)
        power_lines_meta = power.meta

    shape = weights.shape
    affine = weights_meta['transform']

    if year - time_step == start_year:
        origins = np.where(power_lines == 0, 1, 0)
    else:
        origins = power_lines

    targets = df.loc[(df['FinalElecCode' + '{}'.format(year - time_step)] != 1) & (df['MaxDist'] > 0) &
                     (df['PlannedHVLineDist'] < mv_line_max_length) & (df['PreScreening' + "{}".format(year)] == 1)]

    targets = targets.to_crs('EPSG:3395')

    targets_for_raster = [(row.geometry, row.MaxDist) for _, row in targets.iterrows()]

    targets_raster = rasterize(
        targets_for_raster,
        out_shape=shape,
        fill=0,
        default_value=0,
        all_touched=True,
        transform=affine,
    )

    a = np.where(targets_raster > 1, 1, 0)
    #print(a.sum())

    targets['new_connections'] = targets['NewConnections' + '{}'.format(year)] / targets['NumPeoplePerHH']

    new_connections_for_raster = [(row.geometry, row.new_connections) for _, row in targets.iterrows()]

    new_connections_raster = rasterize(
        new_connections_for_raster,
        out_shape=shape,
        fill=0,
        default_value=0,
        all_touched=True,
        transform=affine,
    )

    new_capacity_for_raster = [(row.geometry, row.GridCapacityRequired) for _, row in targets.iterrows()]

    new_capacity_raster = rasterize(
        new_capacity_for_raster,
        out_shape=shape,
        fill=0,
        default_value=0,
        all_touched=True,
        transform=affine,
    )

    ids_for_raster = [(row.geometry, row.id) for _, row in targets.iterrows()]

    id_raster = rasterize(
        ids_for_raster,
        out_shape=shape,
        fill=0,
        default_value=0,
        all_touched=True,
        transform=affine,
    )

    new_lines = np.zeros_like(origins)

    if year - time_step == start_year:
        mv_distance = targets_raster * 0
    else:
        previous_distance = os.path.join(results_folder, '{}_extension_distance_{}.tif'.format(grid, year - time_step))
        with rasterio.open(previous_distance) as prev_dist:
            mv_distance = prev_dist.read(1)
            mv_distance_meta = prev_dist.meta

    mv_distance_new = targets_raster * 0

    pathfinder = seek(origins, mv_distance, new_connections_raster, max_connections,
                      new_capacity_raster, max_capacity, mv_distance_new,
                      targets=targets_raster, weights=weights, path_handling='link', debug=False, film=False)

    origins = origins + pathfinder['paths']
    origins = np.where(origins > 1, 1, origins)
    weights = weights - weights * origins
    new_lines += pathfinder['paths']
    mv_distance = pathfinder['mv_dist']
    max_capacity = pathfinder['new_capacity_remaining']
    max_connections = pathfinder['new_connections_remaining']
    mv_distance_new = pathfinder['mv_distance_new']

    distance = pathfinder['mv_distance_new']

    a = np.extract(distance > 0, distance).tolist()

    b = np.extract(distance > 0, id_raster).tolist()

    ext_distances = pd.DataFrame()
    ext_distances['id'] = b
    ext_distances['distance'] = a

    df = df.merge(ext_distances, on='id', how='left')

    df['extension_distance_' + '{}'.format(year)] = np.where(df['distance'] > 0, df['distance'], df['extension_distance_' + '{}'.format(year)])
    del df['distance']

    i = 0
    while pathfinder['paths'].sum() > 0:
        targets = df.loc[(df['FinalElecCode' + '{}'.format(year - time_step)] != 1) & (df['MaxDist'] > 0) &
                         (df['PlannedHVLineDist'] < mv_line_max_length) & (df['PreScreening' + "{}".format(year)] == 1)]
        targets = targets.to_crs('EPSG:3395')
        targets_for_raster = [(row.geometry, row.MaxDist) for _, row in targets.iterrows()]

        targets_raster = rasterize(
            targets_for_raster,
            out_shape=shape,
            fill=0,
            default_value=0,
            all_touched=True,
            transform=affine,
        )

        targets_raster = targets_raster - targets_raster * origins

        a = np.where(targets_raster > 1, 1, 0)
        #print(a.sum())

        pathfinder = seek(origins, mv_distance,
                          new_connections_raster, max_connections,
                          new_capacity_raster, max_capacity,
                          mv_distance_new,
                          targets_raster, weights,
                          path_handling='link', debug=False, film=False)

        origins = origins + pathfinder['paths']
        origins = np.where(origins > 1, 1, origins)
        weights = weights - weights * origins
        new_lines += pathfinder['paths']
        mv_distance = pathfinder['mv_dist']
        max_capacity = pathfinder['new_capacity_remaining']
        max_connections = pathfinder['new_connections_remaining']
        mv_distance_new = pathfinder['mv_distance_new']

        distance = pathfinder['mv_distance_new']

        a = np.extract(distance > 0, distance).tolist()

        b = np.extract(distance > 0, id_raster).tolist()

        ext_distances = pd.DataFrame()
        ext_distances['id'] = b
        ext_distances['distance'] = a

        df = df.merge(ext_distances, on='id', how='left')

        df['extension_distance_' + '{}'.format(year)] = np.where(df['distance'] > 0, df['distance'], df['extension_distance_' + '{}'.format(year)])
        del df['distance']

        i += 1
        if i > 4:
            break

    new_origins = os.path.join(results_folder, 'origins_{}.tif'.format(year))
    raster_grid_name = os.path.join(results_folder, 'grid_{}.tif'.format(year))
    total_ext_dist = os.path.join(results_folder, 'extension_distance_{}.tif'.format(year))

    with rasterio.open(raster_grid_name, 'w', **weights_meta) as dst:
        dst.write(new_lines, indexes=1)

    if full:
        #from gridfinder import thin, raster_to_lines
        # ToDo
        import shapely.wkt
        from rasterio.transform import xy
        from shapely.geometry import Point, LineString
        def raster_to_lines(guess_skel_in):
            """
            Convert thinned raster to linestring geometry.
            Parameters
            ----------
            guess_skel_in : path-like
                Output from thin().
            Returns
            -------
            guess_gdf : GeoDataFrame
                Converted to geometry.
            """

            rast = rasterio.open(guess_skel_in)
            arr = rast.read(1)
            affine = rast.transform

            max_row = arr.shape[0]
            max_col = arr.shape[1]
            lines = []

            for row in range(0, max_row):
                for col in range(0, max_col):
                    loc = (row, col)
                    if arr[loc] == 1:
                        for i in range(-1, 2):
                            for j in range(-1, 2):
                                next_row = row + i
                                next_col = col + j
                                next_loc = (next_row, next_col)

                                # ensure we're within bounds
                                # ensure we're not looking at the same spot
                                if (
                                        next_row < 0
                                        or next_col < 0
                                        or next_row >= max_row
                                        or next_col >= max_col
                                        or next_loc == loc
                                ):
                                    continue

                                if arr[next_loc] == 1:
                                    line = (loc, next_loc)
                                    rev = (line[1], line[0])
                                    if line not in lines and rev not in lines:
                                        lines.append(line)

            real_lines = []
            for line in lines:
                real = (xy(affine, line[0][0], line[0][1]), xy(affine, line[1][0], line[1][1]))
                real_lines.append(real)

            shapes = []
            for line in real_lines:
                shapes.append(LineString([Point(line[0]), Point(line[1])]).wkt)

            guess_gdf = pd.DataFrame(shapes)
            geometry = guess_gdf[0].map(shapely.wkt.loads)
            guess_gdf = guess_gdf.drop(0, axis=1)
            guess_gdf = gpd.GeoDataFrame(guess_gdf, crs=rast.crs, geometry=geometry)

            guess_gdf["same"] = 0
            guess_gdf = guess_gdf.dissolve(by="same")
            #guess_gdf = guess_gdf.to_crs('epsg:4326')

            return guess_gdf

        shapefile_grid_name = os.path.join(results_folder, 'grid_{}.gpkg'.format(year))
        if new_lines.sum() > 0:
            guess_gdf = raster_to_lines(raster_grid_name)
            guess_gdf.to_file(shapefile_grid_name, driver='GPKG')

    if year - time_step != start_year:
        os.remove(power_lines_raster)
        os.remove(previous_distance)
    else:
        with rasterio.open(new_origins, 'w', **weights_meta) as dst:
            dst.write(origins, indexes=1)

        with rasterio.open(total_ext_dist, 'w', **weights_meta) as dst:
            dst.write(pathfinder['mv_dist'], indexes=1)

    return df
