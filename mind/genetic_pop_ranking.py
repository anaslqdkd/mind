"""Callable routines to mimic genetic resolution method."""

import logging

from sklearn.cluster import KMeans
import pandas as pd
# from matplotlib import pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# logging variable
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
# handler = logging.FileHandler('log.txt')
logger.addHandler(handler)
formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s : %(message)s',
                              datefmt='%a, %d %b %Y %H:%M:%S')
handler.setFormatter(formatter)


def generate_splitFeed_table(pop, data_construction, new_population, split_feed,
                             num_mem):
    """Generate column `splitFEED` in `data_construction` 's `DataFrame`.
    Args:

        pop (`List[mind.genetic.Individual]`) : pupulation list of individual

        data_construction (`DataFrame`) : dataFrame to be constructed before classifing elements

        new_population (`List[mind.genetic.Individual]`) : generated `childs` population list

        split_feed (`List`) : temporary table of split_feed's values

        num_mem (`Int`) : identifier of the membrane
    """
    for mem in range(num_mem):
        for individu in range(pop.fixed_pop_size):
            index = 'splitFEED_frac[{}]'.format(mem + 1)
            split_feed[mem].append(pop.population[individu].model[index])

        for individu in range(pop.fixed_pop_size):
            if new_population[individu].active:
                index = 'splitFEED_frac[{}]'.format(mem + 1)
                split_feed[mem].append(new_population[individu].model[index])

        # delete it's first index
        split_feed[mem].pop(0)
        # Insert it in dictionary
        index = 'splitFEED_{}'.format(mem + 1)
        data_construction[index] = split_feed[mem]


def generate_split_ret_perm_table(pop, data_construction, new_population,
                                  split_ret, split_perm, num_mem):
    """Generate column `splitRET` and column `splitPERM` in `data_construction`
    's `DataFrame`.
    Args:

        pop (`List[mind.genetic.Individual]`) : pupulation list of individual

        data_construction (`DataFrame`) : dataFrame to be constructed before classifing elements

        new_population (`List[mind.genetic.Individual]`) : generated `childs` population list

        split_ret (`List`) : temporary table of split_feed's values

        split_perm (`List`) : temporary table of split_feed's values

        num_mem (`Int`) : identifier of the membrane
    """
    for mem_1 in range(num_mem):
        for mem_2 in range(num_mem):
            for individu in range(pop.fixed_pop_size):
                index_ret = 'splitRET_frac[{},{}]'.format(mem_1 + 1, mem_2 + 1)
                index_perm = 'splitPERM_frac[{},{}]'.format(
                    mem_1 + 1, mem_2 + 1)

                split_ret[mem_1][mem_2].append(
                    pop.population[individu].model[index_ret])

                split_perm[mem_1][mem_2].append(
                    pop.population[individu].model[index_perm])

            for individu in range(pop.fixed_pop_size):
                if new_population[individu].active:
                    index_ret = 'splitRET_frac[{},{}]'.format(
                        mem_1 + 1, mem_2 + 1)
                    index_perm = 'splitPERM_frac[{},{}]'.format(
                        mem_1 + 1, mem_2 + 1)

                    split_ret[mem_1][mem_2].append(
                        new_population[individu].model[index_ret])

                    split_perm[mem_1][mem_2].append(
                        new_population[individu].model[index_perm])

            # Insert it in dictionary
            index_ret = 'splitRET_{}_{}'.format(mem_1 + 1, mem_2 + 1)
            index_perm = 'splitPERM_{}_{}'.format(mem_1 + 1, mem_2 + 1)

            data_construction[index_ret] = split_ret[mem_1][mem_2]
            data_construction[index_perm] = split_perm[mem_1][mem_2]


def generates_dataframe(pop, new_population):
    """Generate `DataFrame` for classifing individual.
    Args:

        pop (`List[mind.genetic.Individual]`) : pupulation list of individual

        new_population (`List[mind.genetic.Individual]`) : generated `childs` population list

    """
    num_mem = pop.modelisation.parameter.num_membranes
    individual_identifier = []
    split_feed = [[nb] for nb in range(num_mem)]
    split_ret = []
    split_perm = []

    def dimensional_tab_creation(tab):
        for mem_1 in range(num_mem):
            tab.append([])
            for mem_2 in range(num_mem):
                tab[mem_1].append([])

    dimensional_tab_creation(split_ret)
    dimensional_tab_creation(split_perm)

    try:
        assert pop.fixed_pop_size is not None
    except Exception:
        logger.exception("Error : No candidates selected")
        raise

    for individu in range(pop.fixed_pop_size):
        # individuals are active in population 1
        individual_identifier.append('pop_1_ind_{}'.format(individu))

    for individu in range(pop.fixed_pop_size):
        # must test if individual is active in population 2
        if new_population[individu].active:
            individual_identifier.append('pop_2_ind_{}'.format(individu))

    print(individual_identifier)
    data_construction = {
        'identifier': individual_identifier,
    }

    # splitFeed
    generate_splitFeed_table(pop, data_construction, new_population, split_feed,
                             num_mem)

    # splitRET and splitPERM
    generate_split_ret_perm_table(pop, data_construction, new_population,
                                  split_ret, split_perm, num_mem)

    df = pd.DataFrame(data=data_construction)
    return df


def pca(dataset):
    """principal component analysis.
    Args:

        dataset (`DataFrame`) : dataFrame containing list of individuals and some values in columns.

    """
    # Standardize the data to have a mean of ~0 and a variance of 1
    X_std = StandardScaler().fit_transform(dataset)
    n, m = X_std.shape
    # Create a PCA instance: pca
    pca = PCA(n_components=min(n, m))
    principalComponents = pca.fit_transform(X_std)

    # Plot the explained variances
    # features = range(pca.n_components)
    # plt.bar(features, pca.explained_variance_ratio_, color='black')
    # plt.show()
    # plt.xlabel('PCA features')
    # plt.ylabel('variance %')
    # plt.xticks(features)

    # Save components to a DataFrame
    PCA_components = pd.DataFrame(principalComponents)
    # print(PCA_components)

    # Asking user to read number of Components
    # nb_component = int(input('Insert optimal number of components = '))
    nb_component = 2
    PCA_components = PCA_components.iloc[:, :nb_component]

    # Printing two components plot
    # plt.scatter(PCA_components[0], PCA_components[1], alpha=.1, color='black')
    # plt.xlabel('PCA 1')
    # plt.ylabel('PCA 2')
    # plt.show()
    return PCA_components


def ranking_element(dataset, nb_cluster=2, iter_init=100):
    """Rank individuals by using `Kmeans`'s algorithm.

    Args:

        dataset (`DataFrame`) : dataFrame containing list of individuals and some values in columns

        nb_cluster (`Int`) : number of cluster (`default = 2`)

        iter_init (`Int`) : number of iteration of Kmeans (`default = 100`).

    """
    # dataset = pd.read_csv(file)
    # extract data without first column
    nb_colums = len(dataset.columns) - 1
    data = dataset.iloc[:, 1:nb_colums + 1]
    # print(data)
    PCA_components = pca(data)
    nb_observations, nb_component = PCA_components.shape

    sse = []
    # clustering number
    k_rng = range(1, min(10, nb_observations))

    for k in k_rng:
        # Create a KMeans instance with k clusters: km
        km = KMeans(n_clusters=k, init='k-means++', n_init=iter_init)
        km.fit(PCA_components.iloc[:, :nb_component])
        sse.append(km.inertia_)

    # plt.xlabel('K')
    # plt.ylabel('Sum of squared error')
    # plt.plot(k_rng, sse)
    # plt.show()

    # After choice of nb_cluster
    # nb_cluster = int(input("Insert the optimal cluster size = "))
    km = KMeans(n_clusters=nb_cluster, init='k-means++', n_init=iter_init)
    km.fit(PCA_components.iloc[:, :nb_component])
    # Getting the cluster centers
    # center = km.cluster_centers_
    dataset['cluster'] = km.labels_
    return dataset


def setting_population_rank(pop, new_population, data):
    """Extract individuals rank from `DataFrame`.

    Args:

        pop (`mind.genetic.Individual`) : list of individuals population

        new_population (``mind.genetic.Individual``) : generated `childs` population list

        data (`DataFrame`) : dataFrame containing list of individuals and some values in columns such as rank

    """
    for i in data.index:
        identifier = data["identifier"][i]
        # get the value index of identifier (for example 1 in pop_1_ind_0)
        index = int(identifier[4:identifier.find("_ind_")])
        individu = int(identifier[identifier.find("_ind_") + len("_ind_"):])

        if index == 1:
            # population 1
            pop.population[individu].rank = data["cluster"][i]
        elif index == 2:
            # population 2
            new_population[individu].rank = data["cluster"][i]
        else:
            logger.exception("ERROR : Unkown population asked")
            raise ValueError("ERROR : Unkown population asked")


# KMeans traitement
def population_ranking(pop, new_population):
    """Ranking individuals elements in population and new_population list.

    Args:

        pop (`mind.genetic.Individual`) : list of individuals population

        new_population (``mind.genetic.Individual``) : generated `childs` population list

    """
    data = generates_dataframe(pop, new_population)
    data = ranking_element(data)
    print(data)
    # Recovery individual ranking
    setting_population_rank(pop, new_population, data)
