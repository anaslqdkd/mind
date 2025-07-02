import os
import random

from typing import List, Dict
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import pairwise_distances_argmin_min
from scipy.spatial.distance import cdist
import pandas as pd
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt
# import numpy as np2
# from sklearn.preprocessing import MinMaxScaler
# from mpl_toolkits.mplot3d import Axes3D

from mind.util import generate_absolute_path


def count_word_file(file, my_text):
    with open(file) as my_file:
        text_as_list = my_file.read().split()
        count = text_as_list.count(my_text)
        # print(count)
        return count


# generate kmeans csv file
def generate_datafiles(my_solver):
    model = my_solver.modelisation.instance
    parameter = my_solver.modelisation.parameter
    nb_membrane = len(model.states)
    splitFEED_frac = [i for i in range(nb_membrane)]
    splitFEED = [i for i in range(nb_membrane)]
    splitRET_frac = [[i] * nb_membrane for i in range(nb_membrane)]
    splitRET = [[i] * nb_membrane for i in range(nb_membrane)]
    splitPERM_frac = [[i] * nb_membrane for i in range(nb_membrane)]
    splitPERM = [[i] * nb_membrane for i in range(nb_membrane)]

    kmeans_input = my_solver.log_dir + 'kmeans_input.csv'
    filename = my_solver.log_dir + 'stationarypoints.txt'
    #filename = my_solver.log_dir + 'stationarypoints_2_obj.txt'
    # filename = my_solver.log_dir + 'stationarypoints_3_obj.txt'

    nb_sol = count_word_file(filename, "Multistart")

    outfile = open(kmeans_input, 'w')
    outfile.write("solutions;")
    for stage1 in model.states:
        outfile.write("splitFEED_frac_" + str(stage1) + ";")
        for stage2 in model.states:
            outfile.write("splitRET_frac_" + str(stage1) + "_" + str(stage2) +
                          ";")

        for stage2 in model.states:
            outfile.write("splitPERM_frac_" + str(stage1) + "_" + str(stage2) +
                          ";")

    for stage1 in model.states:
        outfile.write("feed_cmpr_" + str(stage1) + str(";"))

        #for stage1 in model.states:
        for stage2 in model.states:
            outfile.write("RET_cmpr_" + str(stage1) + "_" + str(stage2) +
                          str(";"))

    #for stage1 in model.states:
        for stage2 in model.states:
            outfile.write("PERM_cmpr_" + str(stage1) + "_" + str(stage2) +
                          str(";"))

    for stage1 in model.states:
        outfile.write("VP_cmpr_" + str(stage1))

        if stage1 == model.states.last():
            outfile.write(" \n")
        else:
            outfile.write(";")

    with open(filename, 'r') as file:
        # for sol in range(my_solver.nb_point):
        for sol in range(nb_sol):
            # save pressures values
            pressure_up = []
            pressure_down = []

            line = file.readline()  # Multistart 1 obj
            print(line)
            for stage in model.states:
                line = file.readline()  # splitFEED_frac
                line = line.split()
                splitFEED_frac[stage - 1] = float(line[-1])
            for stage1 in model.states:
                for stage2 in model.states:
                    line = file.readline()
                    line = line.split()
                    splitRET_frac[stage1 - 1][stage2 - 1] = float(line[-1])

                # read splitRETOut
                line = file.readline()

                for stage2 in model.states:
                    line = file.readline()
                    # print(line)
                    line = line.split()
                    splitPERM_frac[stage1 - 1][stage2 - 1] = float(line[-1])

                # read splitPEMOut
                line = file.readline()

            # area
            for stage1 in model.states:
                line = file.readline()

            # pressure_up
            if parameter.uniform_pup:
                line = file.readline()
                line = line.split()
                pressure_up.append(float(line[-1]))
            else:
                for stage in model.states:
                    line = file.readline()
                    line = line.split()
                    pressure_up.append(float(line[-1]))

            # pressure_down
            for stage1 in model.states:
                line = file.readline()
                line = line.split()
                pressure_down.append(float(line[-1]))

            # permeability line
            if parameter.variable_perm:
                # (components + 1) * states
                for stage in model.states:
                    file.readline()
                    for type_mem in model.components:
                        file.readline()
            else:
                file.readline()

            # output prod lines
            file.readline()
            file.readline()
            file.readline()
            file.readline()
            file.readline()
            line = file.readline()
            print('amalia', line)
            for stage in model.states:
                line = file.readline()  # splitFEED_frac
                line = line.split()
                splitFEED[stage - 1] = float(line[-1])

            for stage1 in model.states:
                # read splitRETOut
                line = file.readline()
                print('tolgo', line)

                for stage2 in model.states:
                    line = file.readline()
                    line = line.split()
                    splitRET[stage1 - 1][stage2 - 1] = float(line[-1])

                # read splitRETOut
                line = file.readline()
                print('tolgo1', line)

                for stage2 in model.states:
                    line = file.readline()
                    # print(line)
                    line = line.split()
                    splitPERM[stage1 - 1][stage2 - 1] = float(line[-1])

            # Write in outfile
            outfile.write("solution " + str(sol + 1) + ";")
            for stage1 in model.states:
                value = float(str(splitFEED_frac[stage1 - 1]))
                print('questo è il valore', value)
                rounding = np.round(value * 100) / 100
                print(rounding)
                outfile.write(str(rounding) + ";")
                #outfile.write(
                #    str(splitFEED_frac[stage1-1] )
                #    + ";"
                #)

                for stage2 in model.states:
                    value = float(str(splitRET_frac[stage1 - 1][stage2 - 1]))
                    rounding = np.round(value * 100) / 100
                    outfile.write(str(rounding) + ";")
                    #outfile.write(
                    #    str(splitRET_frac[stage1-1][stage2-1] * value)
                    #    + ";"
                    #)

                for stage2 in model.states:
                    value = float(str(splitRET_frac[stage1 - 1][stage2 - 1]))
                    rounding = np.round(value * 100) / 100
                    outfile.write(str(rounding) + ";")
                    #outfile.write(
                    #    str(splitPERM_frac[stage1-1][stage2-1])
                    #    + ";"
                    #)

            # write pressure parts (using compressors)
            # print(pressure_up)
            # print(pressure_down)
            # using compressors on feed flows
            for stage in model.states:
                if parameter['uniform_pup']:
                    ratio = pressure_up[0] / model.pressure_in
                else:
                    ratio = pressure_up[stage - 1] / model.pressure_in

                if ratio <= 1:
                    ratio = 0

                outfile.write(str(splitFEED[stage - 1] * ratio) + str(";"))

            # using compressors on RET flows
            for stage1 in model.states:
                for stage2 in model.states:
                    if parameter.uniform_pup:
                        ratio = pressure_up[0] / pressure_up[0]
                    else:
                        ratio = pressure_up[stage1 - 1] / pressure_up[stage2 -
                                                                      1]

                    if ratio <= 1:
                        ratio = 0

                    outfile.write(
                        str(splitRET[stage1 - 1][stage2 - 1] * ratio) +
                        str(";"))

            # using compressors on PERM flows
            for stage1 in model.states:
                for stage2 in model.states:
                    if parameter.vp:
                        press_down = 1
                    else:
                        press_down = pressure_down[stage1 - 1]

                    if parameter.uniform_pup:
                        ratio = pressure_up[0] / press_down
                    else:
                        ratio = pressure_up[stage1 - 1] / press_down

                    if ratio <= 1:
                        ratio = 0

                    outfile.write(
                        str(splitPERM[stage1 - 1][stage2 - 1] * ratio) +
                        str(";"))

            # using Vacuum pump
            for stage in model.states:
                splifrac_flow = sum(splitPERM_frac[stage - 1][stage2 - 1]
                                    for stage2 in model.states)
                if parameter.vp:
                    ratio = 1 / pressure_down[stage - 1]
                else:
                    ratio = 0

                if ratio <= 1:
                    ratio = 0

                outfile.write(str(splifrac_flow * ratio))

                if stage == model.states.last():
                    outfile.write(" \n")
                else:
                    outfile.write(";")

    outfile.flush()


def print_standard_elbow(k_rng, sse):
    # Elbow plot
    plt.xlabel('K')
    plt.ylabel('Sum of squared error')
    plt.plot(k_rng, sse)


def pca(dataset):
    """principal component analysis."""
    # Standardize the data to have a mean of ~0 and a variance of 1

    X_std = StandardScaler().fit_transform(dataset)

    # Create a PCA instance: pca

    pca = PCA(n_components=9)
    principalComponents = pca.fit_transform(X_std)
    #principalComponents = pca.fit_transform(dataset)

    # Plot the explained variances
    features = range(pca.n_components)
    plt.bar(features, pca.explained_variance_ratio_, color='black')
    plt.show()
    plt.xlabel('PCA features')
    plt.ylabel('variance %')
    plt.xticks(features)

    # Save components to a DataFrame
    PCA_components = pd.DataFrame(principalComponents)
    print(PCA_components)
    #plt.scatter(PCA_components[0], PCA_components[1], alpha=.1, color='black')
    #plt.xlabel('PCA 1')
    #plt.ylabel('PCA 2')
    #plt.show()

    # Asking user to read number of Components
    #PCA_components = PCA_components.iloc[:, :2]
    nb_component = int(input('Insert optimal number of components ='))
    pca_for_reduction = PCA(n_components=nb_component)
    principalComponents_2 = pca_for_reduction.fit_transform(X_std)
    #principalComponents_2 = pca_for_reduction.fit_transform(dataset)
    PCA_components_2 = pd.DataFrame(principalComponents_2)

    #PCA_components = PCA_components.iloc[:, :nb_component]

    return PCA_components_2, pca_for_reduction


def drop_unnecessary_col(data,
                         min_num_clusters,
                         opt_cluster,
                         num_clusters,
                         compressor=False):
    """Delete columns added in kmeans loops step but don't needed."""
    # Delete column added (not optimal cluster case)
    for k in range(min_num_clusters, num_clusters):
        if k != opt_cluster:
            if compressor:
                col_name = 'cmpr_cluster_' + str(k)
            else:
                col_name = 'cluster_' + str(k)
            data = data.drop(columns=[col_name])

    #  rename optimal cluster column
    col = list(data.columns)
    if compressor:
        col[-1] = 'cmpr_cluster'
    else:
        col[-1] = 'cluster'
    data.columns = col

    return data


def pressure_kmeans(all_clusters, optimal_size, limit_variables,
                    min_num_clusters, max_num_clusters, iter_init, out_dir):
    """Second part of kmeans algorithm on pressure part."""
    print("---------------------------------------------------------2---------")
    optimal_cluster = [value for value in range(optimal_size)]

    for each_cluster in range(optimal_size):
        sse = []
        k_rng = range(min_num_clusters, max_num_clusters + 1)

        print("cluster = ", each_cluster)
        my_df = all_clusters[optimal_size][each_cluster]
        # print(my_data)
        # get the dataframe
        my_data = my_df.iloc[:, limit_variables + 1:-1]
        # print(my_data)
        my_pca_components = pca(my_data)
        nb_observations, nb_component = my_pca_components.shape

        for k in k_rng:
            print("second zone cluster = ", k)
            n, m = my_data.shape
            try:
                assert n >= k
            except Exception:
                print("Number of observations lower than number of cluster [" +
                      str(n) + " < " + str(k) + "]")
            else:
                # every thing is okay
                km = KMeans(n_clusters=k, init='k-means++', n_init=iter_init)
                # km.fit(my_data)
                km.fit(my_pca_components.iloc[:, :nb_component])
                sse.append(km.inertia_)
                center_pressure = km.cluster_centers_
                print('center pressure', center_pressure)
                center_pressure_ = pd.DataFrame(center_pressure)

                col_name = 'cmpr_cluster_' + str(k)

                # my_df[col_name] = km.labels_
                # insert column in dataframes when number of cluster equal k
                position = len(my_df.columns)
                my_df.insert(position, col_name, km.labels_, True)

                position = len(my_pca_components.columns)
                my_pca_components.insert(position, col_name, km.labels_, True)

                # print("---------------------------------------------")
                # print(my_df)
                # print("---------------------------------------------")
                center = out_dir + 'center' + str(k) + '_pressure' + '.xlsx'
                center_pressure_.to_excel(center, index=False)
        # print(my_data)
        print_standard_elbow(range(min_num_clusters, len(sse) + 1), sse)

        plt.show()

        opt_cluster = int(input("Insert the optimal cluster size = "))
        print("optimal size ", opt_cluster)
        optimal_cluster.append(opt_cluster)

        my_df = drop_unnecessary_col(my_df,
                                     min_num_clusters,
                                     opt_cluster,
                                     len(sse) + 1,
                                     compressor=True)

        my_pca_components = drop_unnecessary_col(my_pca_components,
                                                 min_num_clusters,
                                                 optimal_size,
                                                 len(sse) + 1,
                                                 compressor=True)

        # print(my_pca_components)
        visualise_cluster_components(my_pca_components, opt_cluster,
                                     'cmpr_cluster')

        print("\n--------------------")

        # save final dataframe in to csv
        clusteroutfile = out_dir + 'out' + 'final_' + str(
            each_cluster) + '.xlsx'
        my_df.to_excel(clusteroutfile, index=False)

    print("\nResults saved in ", out_dir + 'out' + 'final_')


def save_clustering(k: int, myclusters: List, df, out_dir):
    for clus in range(k):
        myclusters.append(df[df['cluster'] == clus])
        clusteroutfile = out_dir + 'out' + str(k) + "_" + str(clus) + '.xlsx'
        myclusters[clus].to_excel(clusteroutfile, index=False)


def visualise_cluster_components(PCA_components, optimal_size, key_cluster):
    print("opt = ", optimal_size)
    PCA_components['cluster_segment'] = PCA_components[key_cluster].map({
        0: 'first',
        1: 'second',
        2: 'third',
        3: 'fourth',
        4: 'fifth',
        5: 'sixth',
        6: 'seventh',
        7: 'eighth',
        8: 'ninth',
        9: 'tenth',
        10: 'eleventh',
        11: 'twelfth',
        12: 'Thirteenth',
        13: 'Fourteenth',
        14: 'Fifteenth',
        15: 'Sixteenth',
        16: 'Seventeenth',
        17: 'Eighteenth',
        18: 'Nineteenth',
        19: 'Twentieth'
    })

    colors = [
        'g', 'r', 'b', 'c', 'm', 'y', 'k', 'orange', 'purple', 'pink', 'gray',
        'indigo', 'lime', 'aquamarine', 'teal', 'dodgerblue', 'gold',
        'chocolate'
    ]

    nb_color = len(PCA_components['cluster_segment'].unique())
    nb_color = min(nb_color, optimal_size)
    my_colors = random.sample(colors, nb_color)
    # print(len(colors))
    #print(my_colors)
    print(PCA_components)
    nb_color = len(PCA_components['cluster_segment'].unique())
    nb_color = min(nb_color, optimal_size)
    my_colors = random.sample(colors, nb_color)

    x_axis = PCA_components[0]
    y_axis = PCA_components[1]
    plt.figure(figsize=(10, 8))
    sns.scatterplot(x_axis,
                    y_axis,
                    hue=PCA_components['cluster_segment'],
                    palette=my_colors
                    # palette=sns.color_palette('coolwarm', n_colors=5)
                   )
    plt.title('clusters observations')
    plt.show()


def kmeans_clustering(file,
                      output_file,
                      nb_membrane,
                      min_num_observations=6,
                      max_num_clusters=10,
                      min_num_clusters=1,
                      iter_init=300):
    """Grouping observations using kmeans clustering."""
    df = pd.read_csv(file, sep=";")
    # print(df)
    limit_variables = nb_membrane * (2 * nb_membrane + 1)
    # extract data without first column
    data = df.iloc[:, 1:limit_variables + 1]
    print('dataset iniziale', data)
    #print("data :")
    #print(data)
    n, m = df.shape

    PCA_components, pca_model = pca(data)
    nb_observations, nb_component = PCA_components.shape
    #print('amalia',PCA_components)

    log_dir = generate_absolute_path() + "log" + os.path.sep
    out_dir = log_dir + "kmeans_cluster" + os.path.sep

    sse = []
    k_rng = range(min_num_clusters, max_num_clusters + 1)
    list_of_all_centers = []
    list_of_all_labels = []

    all_clusters: Dict[int, List] = {}

    for k in k_rng:
        print("cluster principale = ", k)

        try:
            assert n >= k
        except Exception:
            print("Number of observations lower than number of cluster [" +
                  str(n) + " < " + str(k) + "]")
        else:
            # Create a KMeans instance with k clusters: km
            km_pca = KMeans(n_clusters=k, init='k-means++', n_init=iter_init)
            # Fit model to samples
            km_pca.fit(PCA_components.iloc[:, :nb_component])
            #sse.append(km_pca.inertia_)

            # Create a KMeans instance with k clusters: km
            km = KMeans(n_clusters=k, init='k-means++', n_init=iter_init)
            # Fit model to samples
            km.fit(data)
            sse.append(km.inertia_)
            # Getting the cluster centers(
            center = km.cluster_centers_
            print('questi sono i centri', center)
            list_of_all_centers.append(center)
            center_ = pd.DataFrame(center)
            closest, _ = pairwise_distances_argmin_min(center, data)
            print('più vicini', closest, _)
            # Writing clusters on csv file for number of cluster equal to k
            # number of clusters, cardinality of clusters
            # which solutions are in the clusters

            df['cluster'] = km.labels_
            #print('df: ',df)
            list_of_all_labels.append(km.labels_)

            # PCA_components['cluster'] = km.labels_
            col_name = 'cluster_' + str(k)
            position = len(PCA_components.columns)
            PCA_components.insert(position, col_name, km_pca.labels_, True)

            all_clusters[k] = []
            save_clustering(k, all_clusters[k], df, out_dir)
            #print('ciao',all_clusters[k[optimal_size]])

            center = out_dir + 'center' + str(k) + '.xlsx'
            center_.to_excel(center, index=False)

    print_standard_elbow(range(min_num_clusters, len(sse) + 1), sse)

    plt.show()

    optimal_size = int(input("Insert the optimal cluster size = "))

    #data frame in which the elements are ordered for clusters
    data_ordered = pd.concat(all_clusters[optimal_size][:])
    print('dataframe concatenato', data_ordered)

    matrix_different = np.zeros((len(data_ordered), len(data_ordered)))

    for row in range(0, len(data_ordered)):
        for row1 in range(row + 1, len(data_ordered)):
            y = data_ordered.iloc[row, 1:limit_variables + 1]
            list_ = np.array(y.values.tolist())
            #print('prova',list_)
            #print('questo è y',y)
            #print('questa è la lunghezza di list',len(list_))
            z = data_ordered.iloc[row1, 1:limit_variables + 1]
            list_1 = np.array(z.values.tolist())
            #print('prova 1',list_1)
            #print('questo è z', z)
            #print('questa è la lunghezza di list_1',len(list_1))
            diff = np.abs(list_ - list_1)
            #check condition
            count_elements_different = np.sum(diff >= 0.1)
            #print("Amalia: ", count_elements_different)
            matrix_different[row, row1] = count_elements_different
            matrix_different[row1, row] = count_elements_different
    print(matrix_different)

    headers = data_ordered['solutions']
    #print(headers)

    df_matrix = pd.DataFrame(matrix_different, columns=headers, index=headers)
    df_matrix.to_csv('test.csv')

    print('dimensione', matrix_different.shape)

    #print("optimal size ", optimal_size)

    PCA_components = drop_unnecessary_col(PCA_components, min_num_clusters,
                                          optimal_size,
                                          len(sse) + 1)

    # print(df.reset_index(drop=True))
    # index_col = 0
    visualise_cluster_components(PCA_components, optimal_size, 'cluster')

    center_for_minMax_calculation = list_of_all_centers[optimal_size - 1]
    labels_for_minMax = list_of_all_labels[optimal_size - 1]

    plt.scatter(PCA_components[0], PCA_components[1], c='y', label='solutions')

    for cluster_index in range(optimal_size):
        index_min_distance = 0
        index_max_distance = 0
        min_distance = 10.0
        max_distance = 0.0
        center_of_interest = center_for_minMax_calculation[cluster_index]
        #plt.scatter(center_of_interest[0], center_of_interest[1] , c='b', label='centers')
        #print('center_of interest: ', center_of_interest)
        #print(PCA_components.keys())
        for index, ob in pd.DataFrame(data).iterrows():
            #print(ob[0], ob[1], ob['cluster'])
            observation_i = np.array(ob)
            cluster_i = labels_for_minMax[index]  #ob['cluster']
            if cluster_i == cluster_index:
                #print(index, cluster_i)
                dist = np.linalg.norm(observation_i - center_of_interest)
                if dist > max_distance:
                    max_distance = dist
                    index_max_distance = index
                if dist < min_distance:
                    min_distance = dist
                    index_min_distance = index

        print('for cluster ', cluster_index)
        print('The solution with max distance from the center is:')
        print(df.iloc[index_max_distance, 0], ' with distance: ', max_distance)

        #x, y= PCA_components.iloc[index_max_distance,0:2]
        #plt.scatter(x,y, c='r', label='far solutions')

        print('The solution with min distance from the center is:')
        print(df.iloc[index_min_distance, 0], ' with distance: ', min_distance)
        #x, y= PCA_components.iloc[index_min_distance,0:2]
        #plt.scatter(x,y, c='g', label='close solutions')

    #plt.axis('equal')
    #plt.legend()
    #plt.show()

    # Here use the value of the optimal size to cluster with pressures
    # Save details of the solution or whatever...
    #print('adoro',all_clusters[optimal_size])

    pressure_kmeans(all_clusters, optimal_size, limit_variables,
                    min_num_clusters, max_num_clusters, iter_init, out_dir)



if __name__ == '__main__':
    BASE_DIR = generate_absolute_path()
    sys.path.append(BASE_DIR)
    log_dir = generate_absolute_path() + "log" + os.path.sep
    #name = log_dir + "matrix_count.csv"
    fname = log_dir + "kmeans_input.csv"
    output_file = log_dir + "cluster.xlsx"
    nb_membrane = 2
    # output_file=pd.ExcelWriter(r'cluster.xlsx')
    kmeans_clustering(fname, output_file, nb_membrane)
    # kmeans_cluster(fname, nb_membrane)
