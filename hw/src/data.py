from Utility import Utility
from ROW import ROW
from COLS import Cols as COLS
from node import NODE
import math
import random
import numpy as np
from sklearn.cluster import KMeans
from sklearn.cluster import SpectralClustering
from sklearn.cluster import AgglomerativeClustering
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
# ----------------------------------------------------------------------------
# Data Class

is_debug = False

class DATA:
    def __init__(self, the, src, fun=None):
        self.rows = []
        self.cols = None
        self.the = the
        self.util = Utility(the)
        self.adds(src, fun)
        # print("Construting..")

    def adds(self, src, fun=None):
        if isinstance(src, str):
            # Here the _ is just because pairs returns two values.
            for x in self.util.l_csv(file=src):
                # print(x)
                self.add(x, fun)
        else:
            # for attr in dir(src):
            #     print("obj.%s = %r" % (attr, getattr(src, attr)))
            ## also did some debugging here.
            for x in (src or []):
                self.add(x, fun)
            # self.add(src, fun)
        return self

    def add(self, t, fun=None):
        # Made changes to the following block of code
        # print("Before", t)
        # if t is None:
        #     return 0
        if hasattr(t, 'cells'):
            row = t
        else:
            row = ROW(self.the, t)
        # print("After", row)
        # row = ROW(t) if type(t) is list else t.cells
        # row = t if t.cells else ROW(t)  Check line 182 might be different.
        # print(self.cols)
        if self.cols:
            if fun:
                fun(self, row)
            self.rows.append(self.cols.add(row))
            # print(self.rows)
        else:
            self.cols = COLS(self.the, row)

    def mid(self, cols=None):
        u = []
        for col in cols or self.cols.all:
            u.append(col.mid())
        return ROW(self.the, u)

    def div(self, cols=None):
        u = []
        for col in cols or self.cols.all:
            u.append(col.div())
        return ROW(self.the, u)
    
    def small(self):
        u = []
        for col in self.cols.all:
            u.append(col.small())
        return ROW(self.the, u)
    
    def stats(self, cols=None, fun=None, ndivs=None):
        u = {".N": len(self.rows)}
        # print(self.rows)
        columns_to_iterate = getattr(self.cols, cols or "y", [])
        for col in columns_to_iterate:
            value = getattr(type(col), fun or "mid")(col)
            #print("Value = " , value)
            u[col.txt] = self.util.rnd(value, ndivs)
            # print(value)
            # u[col.txt] = round(value,2)
        return u
    
    def clone(self, rows=None):
        new = DATA(self.the, [self.cols.names])
        new.cols.names = self.cols.names
        for row in rows or []:
            new.add(row)
        return new
    
    def gate(self, budget0, budget, some, clustering_method=None):
        random.seed(self.the.seed)
        stats = []
        bests = []
        rows = self.util.shuffle(self.rows)
        # print(self.rows)
        lite = rows[:budget0]
        dark = rows[budget0:]
        for i in range(budget):

            if not clustering_method:
                # Do SMO by default
                best, rest = self.bestRest(lite, len(lite)**some)
            elif clustering_method == "kmeans":
                pass
            
            todo, selected = self.split(best, rest, lite, dark)

            stats.append(selected.mid())
            bests.append(best.rows[0])
            lite.append(dark.pop(todo))
        return stats, bests
    
    def gate2(self, budget0, budget, some, clustering_method=None):
        random.seed(self.the.seed)
        stats = []
        bests = []
        rows = self.util.shuffle(self.rows)
        # print(self.rows)
        lite = rows[:budget0]
        dark = rows[budget0:]
        for i in range(budget):

            if not clustering_method:
                # Do SMO by default
                best, rest = self.bestRest(lite, len(lite)**some)
            elif clustering_method == "kmeans":
                pass
            
            todo, selected = self.split_by_b_over_r(best, rest, lite, dark)

            stats.append(selected.mid())
            bests.append(best.rows[0])
            lite.append(dark.pop(todo))
        return stats, bests
    
    def split(self, best, rest, lite_rows, dark_rows):
        selected = DATA(self.the, [self.cols.names])
        max_val = 1E30
        out = 1
        # print(dark_rows)
        for i, row in enumerate(dark_rows):
            b = row.like(best, len(lite_rows), 2)
            r = row.like(rest, len(lite_rows), 2)
            if b > r:
                selected.add(row)
            tmp = abs(b + r) / abs(b - r + 1E-300)
            if tmp > max_val:
                out, max_val = i, tmp
        return out, selected

    def split_by_b_over_r(self, best, rest, lite_rows, dark_rows):
        selected = DATA(self.the, [self.cols.names])
        max_val = 1E30
        out = 1
        # print(dark_rows)
        for i, row in enumerate(dark_rows):
            b = row.like(best, len(lite_rows), 2)
            r = row.like(rest, len(lite_rows), 2)
            if b > r:
                selected.add(row)
            tmp = abs(b) / abs(r + 1E-300)
            if tmp > max_val:
                out, max_val = i, tmp
        return out, selected
    
    def bestRest(self, rows, want):
        rows.sort(key=lambda a: a.d2h(self))
        # rows.sort(key=lambda a: a.d2h(self))
        # best = [self.cols['names']]
        # rest = [self.cols['names']]
        best = [self.cols.names]
        rest = [self.cols.names]
        for i, row in enumerate(rows):
            if i <= want:
                best.append(row)
            else:
                rest.append(row)
        return DATA(self.the, best), DATA(self.the, rest)


    def split_row_with_kmeans(self, rows, init='k-means++', max_iter=100, need_standardlize=False):
        x_data_rows = []
        for row in rows:
            new_x_data = []
            for x_field in self.cols.x:
                new_x_data.append(row.cells[x_field.at])
            x_data_rows.append(new_x_data)

        data_array = np.array(x_data_rows)

        if need_standardlize:
            scaler = StandardScaler()
            data_array = scaler.fit_transform(data_array)

        kmeans = KMeans(n_clusters=2, init=init, max_iter=max_iter, random_state=self.the.seed, n_init=1)
        kmeans.fit(data_array)

        labels = kmeans.labels_

        a = [self.cols.names]
        b = [self.cols.names]

        for index, row in enumerate(rows):
            if labels[index] == 0:
                a.append(row)
            else:
                b.append(row)

        a_data = DATA(self.the, a)
        b_data = DATA(self.the, b)

        a_mid_row = a_data.mid()
        b_mid_row = b_data.mid()

        a_mid_row_cells = [round(a_mid_row.cells[field.at], 2) for field in self.cols.all]
        b_mid_row_cells = [round(b_mid_row.cells[field.at], 2) for field in self.cols.all]

        a_d2h = a_data.mid().d2h(self)
        b_d2h = b_data.mid().d2h(self)

        if a_d2h <= b_d2h:
            best = a_data
            rest = b_data
        else:
            best = b_data
            rest = a_data

        return best.rows, rest.rows, best.mid(), rest.mid()

    def split_row_with_spectral_clustering(self, rows, affinity='nearest_neighbors', n_neighbors=50, need_standardlize=False):
        x_data_rows = []
        for row in rows:
            new_x_data = []
            for x_field in self.cols.x:
                new_x_data.append(row.cells[x_field.at])
            x_data_rows.append(new_x_data)

        data_array = np.array(x_data_rows)

        if need_standardlize:
            scaler = StandardScaler()
            data_array = scaler.fit_transform(data_array)

        if len(data_array) < n_neighbors:
            n_neighbors = int(len(data_array) ** 0.5)

        model = SpectralClustering(n_clusters=2, affinity=affinity, n_neighbors=n_neighbors, random_state=self.the.seed)

        labels = model.fit_predict(data_array)

        a = [self.cols.names]
        b = [self.cols.names]

        for index, row in enumerate(rows):
            if labels[index] == 0:
                a.append(row)
            else:
                b.append(row)

        a_data = DATA(self.the, a)
        b_data = DATA(self.the, b)

        a_mid_row = a_data.mid()
        b_mid_row = b_data.mid()

        a_mid_row_cells = [round(a_mid_row.cells[field.at], 2) for field in self.cols.all]
        b_mid_row_cells = [round(b_mid_row.cells[field.at], 2) for field in self.cols.all]

        a_d2h = a_data.mid().d2h(self)
        b_d2h = b_data.mid().d2h(self)

        if a_d2h <= b_d2h:
            best = a_data
            rest = b_data
        else:
            best = b_data
            rest = a_data

        return best.rows, rest.rows, best.mid(), rest.mid()

    def split_row_with_gaussian_mixtures(self, rows, covariance_type='full', max_iter=100, need_standardlize=False):
        x_data_rows = []
        for row in rows:
            new_x_data = []
            for x_field in self.cols.x:
                new_x_data.append(row.cells[x_field.at])
            x_data_rows.append(new_x_data)

        data_array = np.array(x_data_rows)

        if need_standardlize:
            scaler = StandardScaler()
            data_array = scaler.fit_transform(data_array)

        model = GaussianMixture(n_components=2, covariance_type=covariance_type, max_iter=max_iter, random_state=self.the.seed)

        model.fit(data_array)

        labels = model.predict(data_array)

        a = [self.cols.names]
        b = [self.cols.names]

        for index, row in enumerate(rows):
            if labels[index] == 0:
                a.append(row)
            else:
                b.append(row)

        a_data = DATA(self.the, a)
        b_data = DATA(self.the, b)

        a_mid_row = a_data.mid()
        b_mid_row = b_data.mid()

        a_mid_row_cells = [round(a_mid_row.cells[field.at], 2) for field in self.cols.all]
        b_mid_row_cells = [round(b_mid_row.cells[field.at], 2) for field in self.cols.all]

        a_d2h = a_data.mid().d2h(self)
        b_d2h = b_data.mid().d2h(self)

        if a_d2h <= b_d2h:
            best = a_data
            rest = b_data
        else:
            best = b_data
            rest = a_data

        return best.rows, rest.rows, best.mid(), rest.mid()

    def split_row_with_DBSCAN(self, rows, epsilon=0.3, min_samples=2, need_standardlize=False):
        x_data_rows = []
        for row in rows:
            new_x_data = []
            for x_field in self.cols.x:
                new_x_data.append(row.cells[x_field.at])
            x_data_rows.append(new_x_data)

        data_array = np.array(x_data_rows)

        if need_standardlize:
            scaler = StandardScaler()
            data_array = scaler.fit_transform(data_array)


        dbscan = DBSCAN(eps=epsilon, min_samples=min_samples)
        dbscan_clusters = dbscan.fit_predict(X)

        n_clusters_dbscan = len(set(dbscan_clusters)) - (1 if -1 in dbscan_clusters else 0)

        if n_clusters_dbscan > 2:
            # 'DBSCAN followed by K-Means'
            kmeans = KMeans(n_clusters=2, random_state=self.the.seed)
            kmeans_clusters = kmeans.fit_predict(X)
            labels = kmeans_clusters
        else:
            # 'DBSCAN only'
            labels = dbscan_clusters

        a = [self.cols.names]
        b = [self.cols.names]

        for index, row in enumerate(rows):
            if labels[index] == 0:
                a.append(row)
            else:
                b.append(row)

        a_data = DATA(self.the, a)
        b_data = DATA(self.the, b)

        a_mid_row = a_data.mid()
        b_mid_row = b_data.mid()

        a_mid_row_cells = [round(a_mid_row.cells[field.at], 2) for field in self.cols.all]
        b_mid_row_cells = [round(b_mid_row.cells[field.at], 2) for field in self.cols.all]

        a_d2h = a_data.mid().d2h(self)
        b_d2h = b_data.mid().d2h(self)

        if a_d2h <= b_d2h:
            best = a_data
            rest = b_data
        else:
            best = b_data
            rest = a_data

        return best.rows, rest.rows, best.mid(), rest.mid()

    def farapart(self, rows, sortp=None, before=None):
        far = int(len(rows) * self.the.Far)
        evals = 1 if before else 2
        left = before or random.choice(rows).neighbors(self, rows)[far]
        right = left.neighbors(self, rows)[far]
        if sortp and right.d2h(self) < left.d2h(self):
            left, right = right, left
        return left, right, left.dist(right, self) + 1E-300, evals


    def half(self, rows, sortp=False, before=None):
        def dist(r1, r2): return r1.dist(r2, self)
        def proj(row)  : return (dist(row,left)**2 + C**2 - dist(row,right)**2)/(2*C)
        left, right, C, _ = self.farapart(random.choices(rows, k=min(self.the.Half, len(rows))), sortp=sortp, before=before)
        if C == 0:
            print("C = 0!!")

            for row in rows:
                print(row.cells)

            print("")
            print(left.cells)
            print(right.cells)

        lefts,rights = [],[]

        for n, row in enumerate(sorted(rows , key=proj)):
            if n < len(rows) / 2 :
                lefts.append(row)
            else:
                rights.append(row)

        return lefts, rights, left, right

    def tree(self, sortp):
        pass
        evals = 0

        def _tree(data, above=None):
            nonlocal evals
            node = NODE(data)
            if len(data.rows) > 2 * len(self.rows) ** 0.5:
                lefts, rights, node.left, node.right, node.C, node.cut, evals1 = self.half(data.rows, sortp, above)
                evals = evals + evals1
                node.lefts = _tree(self.clone(lefts), node.left)
                node.rights = _tree(self.clone(rights), node.right)
            return node

        return _tree(self), evals

    def branch(self, rows=None, stop=None, rest=None, evals=1, before=None):
        rows = rows or self.rows
        stop = stop or 2 * len(rows) ** 0.5
        rest = rest or []
        if len(rows) > stop:
            lefts, rights, left, right  = self.half(rows, True, before)
            return self.branch(lefts, stop, rest+rights, evals+1, left)
        else:
            return self.clone(rows), self.clone(rest), evals


    def rrp(self, rows=None, stop=None, rest=None, evals=1, before=None, cluserting_algo_type="projection", clustering_parameter_dict=None):
        import warnings
        warnings.filterwarnings("ignore", category=UserWarning)
        rows = rows or self.rows
        need_standardlize = False
        if not stop:
            # First time init
            random.seed(self.the.seed)
        stop = stop or 2 * len(rows) ** 0.5
        rest = rest or []
        if len(rows) > stop:
            if cluserting_algo_type == "projection":
                try:
                    lefts, rights, left, right  = self.half(rows, True, before)
                except ZeroDivisionError as e:
                    print("row size = {0}".format(len(rows)))
                    print("stop = {0}".format(stop))
                    raise e
            elif cluserting_algo_type == "kmeans":
                init = clustering_parameter_dict.get("init")
                max_iter = clustering_parameter_dict.get("max_iter")

                kwargs = {}
                if init:
                    kwargs['init'] = init
                if max_iter:
                    kwargs['max_iter'] = max_iter

                kwargs["need_standardlize"] = need_standardlize
                lefts, rights, left, right  = self.split_row_with_kmeans(rows, **kwargs)
            elif cluserting_algo_type == "spectral_clustering":
                affinity = clustering_parameter_dict.get("affinity")
                n_neighbors = clustering_parameter_dict.get("n_neighbors")

                kwargs = {}
                if affinity:
                    kwargs['affinity'] = affinity
                if n_neighbors:
                    kwargs['n_neighbors'] = n_neighbors

                kwargs["need_standardlize"] = need_standardlize
                lefts, rights, left, right  = self.split_row_with_spectral_clustering(rows, **kwargs)
            elif cluserting_algo_type == "gaussian_mixtures":
                covariance_type = clustering_parameter_dict.get("covariance_type")
                max_iter = clustering_parameter_dict.get("max_iter")
                kwargs = {}
                if covariance_type:
                    kwargs['covariance_type'] = covariance_type
                if max_iter:
                    kwargs['max_iter'] = max_iter

                kwargs["need_standardlize"] = need_standardlize
                lefts, rights, left, right  = self.split_row_with_gaussian_mixtures(rows, **kwargs)
            elif cluserting_algo_type == "agglomerative_clustering":
                linkage = clustering_parameter_dict.get("linkage")
                affinity = clustering_parameter_dict.get("affinity")
                kwargs = {}
                if linkage:
                    kwargs['linkage'] = linkage
                if affinity:
                    kwargs['affinity'] = affinity

                kwargs["need_standardlize"] = need_standardlize
                lefts, rights, left, right  = self.split_row_with_agglomerative_clustering(rows, **kwargs)
            elif cluserting_algo_type == "DBSCAN_clustering":
                epsilon = clustering_parameter_dict.get("epsilon")
                min_samples = clustering_parameter_dict.get("min_samples")
                kwargs = {}
                if epsilon:
                    kwargs['epsilon'] = epsilon
                if min_samples:
                    kwargs['min_samples'] = min_samples

                kwargs["need_standardlize"] = need_standardlize
                lefts, rights, left, right  = self.split_row_with_DBSCAN(rows, **kwargs)
            else:
                raise RuntimeError("Unsupported Clustering Algorithm: {0}".format(cluserting_algo_type))
            return self.rrp(lefts, stop, rest+rights, evals+1, left, cluserting_algo_type=cluserting_algo_type, clustering_parameter_dict=clustering_parameter_dict)
        else:
            if is_debug:
                print("[{0}] [stop = {1}] Result is done, seed = {2}, final row count = {3}".format(cluserting_algo_type, math.ceil(stop), self.the.seed, len(rows)))
            return self.clone(rows), self.clone(rest), evals


    def rrp_with_depth(self, rows=None, stopping_eval=None, rest=None, evals=1, before=None, cluserting_algo_type="projection", clustering_parameter_dict=None):
        import warnings
        warnings.filterwarnings("ignore", category=UserWarning)
        rows = rows or self.rows
        rest = rest or []
        if evals <= stopping_eval and len(rows) >= 2:
            if cluserting_algo_type == "projection":
                try:
                    lefts, rights, left, right  = self.half(rows, True, before)
                except ZeroDivisionError as e:
                    print("row size = {0}".format(len(rows)))
                    raise e
            elif cluserting_algo_type == "kmeans":
                init = clustering_parameter_dict.get("init")
                max_iter = clustering_parameter_dict.get("max_iter")

                kwargs = {}
                if init:
                    kwargs['init'] = init
                if max_iter:
                    kwargs['max_iter'] = max_iter

                lefts, rights, left, right  = self.split_row_with_kmeans(rows, **kwargs)
                print("-----------------")
                print("[k-means] [evals = {0}] Size of bests: {1}".format(evals, len(lefts)))
                print("[k-means] [evals = {0}] Size of rests: {1}".format(evals, len(rights)))
                print("-----------------\n")
            elif cluserting_algo_type == "spectral_clustering":
                affinity = clustering_parameter_dict.get("affinity")
                n_neighbors = clustering_parameter_dict.get("n_neighbors")

                kwargs = {}
                if affinity:
                    kwargs['affinity'] = affinity
                if n_neighbors:
                    kwargs['n_neighbors'] = n_neighbors

                lefts, rights, left, right  = self.split_row_with_spectral_clustering(rows, **kwargs)
                print("-----------------")
                print("[SC] [evals = {0}] Size of bests: {1}".format(evals, len(lefts)))
                print("[SC] [evals = {0}] Size of rests: {1}".format(evals, len(rights)))
                print("-----------------\n")
            elif cluserting_algo_type == "gaussian_mixtures":
                covariance_type = clustering_parameter_dict.get("covariance_type")
                max_iter = clustering_parameter_dict.get("max_iter")
                kwargs = {}
                if covariance_type:
                    kwargs['covariance_type'] = covariance_type
                if max_iter:
                    kwargs['max_iter'] = max_iter

                lefts, rights, left, right  = self.split_row_with_gaussian_mixtures(rows, **kwargs)
                print("-----------------")
                print("[GM] [evals = {0}] Size of bests: {1}".format(evals, len(lefts)))
                print("[GM] [evals = {0}] Size of rests: {1}".format(evals, len(rights)))
                print("-----------------\n")
            else:
                raise RuntimeError("Unsupported Clustering Algorithm: {0}".format(cluserting_algo_type))

            return self.rrp_with_depth(lefts, stopping_eval, rest+rights, evals+1, left, cluserting_algo_type=cluserting_algo_type, clustering_parameter_dict=clustering_parameter_dict)
        else:
            print("[{0}] [evals = {1}] Result is done, seed = {2}, final row count = {3}".format(cluserting_algo_type, stopping_eval, self.the.seed, len(rows)))
            return self.clone(rows), self.clone(rest), evals
    
    def recursive_kmeans(self, arg_eval, data=None, evals=1):
        random.seed(self.the.seed)
        data = data or self
        # stop = stop or 2 * len(data.rows) ** 0.5
        best = data

        if evals <= arg_eval:
            if len(data.rows) < 2:
                raise ValueError("Rows : {0}\n".format(data.rows), "Eval : {0}".format(evals))
            x_data_rows = []
            for row in data.rows:
                new_x_data = []
                for x_field in data.cols.x:
                    new_x_data.append(row.cells[x_field.at])
                x_data_rows.append(new_x_data)

            data_array = np.array(x_data_rows)

            kmeans = KMeans(n_clusters=2, random_state=self.the.seed, n_init=1)

            kmeans.fit(data_array)

            labels = kmeans.labels_

            a = [data.cols.names]
            b = [data.cols.names]

            for index, row in enumerate(data.rows):
                if labels[index] == 0:
                    a.append(row)
                else:
                    b.append(row)

            a_data = DATA(self.the, a)
            b_data = DATA(self.the, b)

            a_d2h = a_data.mid().d2h(self)
            b_d2h = b_data.mid().d2h(self)
            
            if a_d2h <= b_d2h:
                best = a_data
                rest = b_data
            else:
                best = b_data
                rest = a_data
            
            return self.recursive_kmeans(arg_eval, best, evals + 1)
        else:
            return self.clone(data.rows), best.mid().d2h(self), evals
        
    def recursive_spectral_clustering(self, arg_eval, data=None, affinity='nearest_neighbors', n_neighbors=50, evals=1):
        random.seed(self.the.seed)
        data = data or self
        best = data

        if evals <= arg_eval:
            if len(data.rows) < 2:
                raise ValueError("Rows : {0}\n".format(data.rows), "Eval : {0}".format(evals))

            x_data_rows = []
            for row in data.rows:
                new_x_data = []
                for x_field in data.cols.x:
                    new_x_data.append(row.cells[x_field.at])
                x_data_rows.append(new_x_data)

            data_array = np.array(x_data_rows)

            if len(data_array) < n_neighbors:
                n_neighbors = int(len(data_array) ** 0.5)

            model = SpectralClustering(n_clusters=2, affinity=affinity, n_neighbors=n_neighbors, random_state=self.the.seed)

            labels = model.fit_predict(data_array)

            a = [self.cols.names]
            b = [self.cols.names]

            for index, row in enumerate(data.rows):
                if labels[index] == 0:
                    a.append(row)
                else:
                    b.append(row)

            a_data = DATA(self.the, a)
            b_data = DATA(self.the, b)

            a_d2h = a_data.mid().d2h(self)
            b_d2h = b_data.mid().d2h(self)

            if a_d2h <= b_d2h:
                best = a_data
                rest = b_data
            else:
                best = b_data
                rest = a_data
            
            return self.recursive_spectral_clustering(arg_eval, best, affinity, n_neighbors, evals + 1)
        else:
            return self.clone(data.rows), best.mid().d2h(self), evals
        

    def recursive_gaussian_mixtures(self, arg_eval, data=None, covariance_type='full', max_iter=100, evals=1):
        random.seed(self.the.seed)
        data = data or self
        best = data

        if evals <= arg_eval:
            if len(data.rows) < 2:
                raise ValueError("Rows : {0}\n".format(data.rows), "Eval : {0}".format(evals))
            x_data_rows = []
            for row in data.rows:
                new_x_data = []
                for x_field in data.cols.x:
                    new_x_data.append(row.cells[x_field.at])
                x_data_rows.append(new_x_data)

            data_array = np.array(x_data_rows)

            model = GaussianMixture(n_components=2, covariance_type=covariance_type, max_iter=max_iter, random_state=self.the.seed)

            model.fit(data_array)

            labels = model.predict(data_array)

            a = [self.cols.names]
            b = [self.cols.names]

            for index, row in enumerate(data.rows):
                if labels[index] == 0:
                    a.append(row)
                else:
                    b.append(row)

            a_data = DATA(self.the, a)
            b_data = DATA(self.the, b)

            a_d2h = a_data.mid().d2h(self)
            b_d2h = b_data.mid().d2h(self)

            if a_d2h <= b_d2h:
                best = a_data
                rest = b_data
            else:
                best = b_data
                rest = a_data

            return self.recursive_gaussian_mixtures(arg_eval, best, covariance_type, max_iter, evals + 1)
        else:
            return self.clone(data.rows), best.mid().d2h(self), evals

#data = DATA(src='../data/auto93.csv')

#print(data.stats())
