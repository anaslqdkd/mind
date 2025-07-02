"""Describing objective function evaluation [economic formalism]."""

import logging
import os

import pyomo.environ as pe

from mind.util import generate_absolute_path

# logging variable
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
# handler = logging.FileHandler(filename)
logger.addHandler(handler)
formatter = logging.Formatter(
    fmt="[%(asctime)s] %(levelname)s : %(message)s", datefmt="%a, %d %b %Y %H:%M:%S"
)
handler.setFormatter(formatter)


class ObjFunction:
    """Objective function's expression geneator's object.

    Attributes:
        cc (`Float`): compressor base cost

        cvp (`Float`) : vacuum pump cost factor

        cexp (`Float`) : expander base cost

        km (`Float`) : unit cost of membrane module

        kmf (`Float`) : base frame cost

        kmr (`Float`) : membrane replacement cost

        k_er (`Float`) : exchange rate

        k_el (`Float`) : electricity cost factor

        mpfc (`Float`) : material and pressure factor for compressor

        mfc (`Float`) : module factor for compressor

        mdf_cc (`Float`) : compressor module factor

        uf_2000 (`Float`) : update factor

        uf_1968 (`Float`) : update factor

        uf_2011 (`Float`) : update factor

        nu (`Float`) : membrane replacement rate

        t_op (`Float`) : operation time per year

        k_gp (`Float`) : upgrated biogas sales price

        i (`Float`) : interest rate

        z (`Float`) : project lifetime

        eta_compr (`Float`) : isentropic compressor efficiency

        phi (`Float`) : mechanical efficiency

        gamma (`Float`) : gas expansion coefficient

        r (`Float`) : ideal gas constant

        t (`Float`) : temperature

        eta_vp_correction (`Float`) : isentropic vacuum pump efficiency

        eta_vp (`Float`) : isentropic vacuum pump efficiency

        icf (`Float`) : indirect cost factor

        a (`Float`) : annuity coefficient for equipement

    Notes:
        For more details, please refer to articles :
        <https://www.sciencedirect.com/science/article/pii/S0009250920303018>
        <https://www.sciencedirect.com/science/article/abs/pii/S0376738818317824>
    """

    def __init__(self, fname_eco, parameter, loading=False):
        """initialization of desing process's thermodynamic data and some
        coefficient expressions needed to formulate objective's function
        expression.
        loading (boolean) : `True` if load intermediaire economic param from file

        """
        self.parameter = parameter
        economic = self.load_coef(fname_eco)
        # Parameters data
        self.nu = economic["nu"] if "nu" in economic.keys() else None
        self.kmr = economic["K_mr"] if "K_mr" in economic.keys() else None
        self.t_op = economic["t_op"] if "t_op" in economic.keys() else None
        self.k_el = economic["K_el"] if "K_el" in economic.keys() else None
        self.k_gp = economic["K_gp"] if "K_gp" in economic.keys() else 0
        self.a = economic["a"] if "a" in economic.keys() else 0.0854

        self.icf = economic["ICF"] if "ICF" in economic.keys() else None
        self.kmf = economic["K_mf"] if "K_mf" in economic.keys() else None
        self.km = economic["K_m"] if "K_m" in economic.keys() else None
        self.k_er = economic["K_er"] if "K_er" in economic.keys() else None
        self.mpfc = economic["MPFc"] if "MPFc" in economic.keys() else None
        self.mfc = economic["MFc"] if "MFc" in economic.keys() else None
        self.mdfc = economic["MDFc"] if "MDFc" in economic.keys() else None
        self.uf_cp = economic["UF_1968"] if "UF_1968" in economic.keys() else None
        self.uf_exp = economic["UF_2000"] if "UF_2000" in economic.keys() else None
        self.phi = economic["phi"] if "phi" in economic.keys() else None
        self.gamma = economic["gamma"] if "gamma" in economic.keys() else 1.36
        self.r = economic["R"] if "R" in economic.keys() else None
        self.t = economic["T"] if "T" in economic.keys() else None

        self.eta_cp = economic["eta_cp"] if "eta_cp" in economic.keys() else 0.85
        self.eta_exp = economic["eta_exp"] if "eta_exp" in economic.keys() else 0.85
        self.eta_vp_0 = economic["eta_vp_0"] if "eta_vp_0" in economic.keys() else None
        self.eta_vp_1 = economic["eta_vp_1"] if "eta_vp_1" in economic.keys() else None

        self.cvp = economic["C_vp"] if "C_vp" in economic.keys() else None
        self.cc = economic["C_cp"] if "C_cp" in economic.keys() else None
        self.cexp = economic["C_exp"] if "C_exp" in economic.keys() else None
        # data Thermodynamic

        self.alpha_mem = 0.7
        self.alpha_press_mem = 0.875
        self.beta_exp = 0.81
        self.beta_cp = 0.77
        self.b_exp = 0.746
        self.membrane_frame_area_coef = 2000
        self.stage_compressor_area_coef = 74.6

        self.except_when_none_value()

        self.a = (
            ((1 / self.membrane_frame_area_coef) ** self.alpha_mem)
            * self.kmf
            * ((1 / 55) ** self.alpha_press_mem)
        )
        self.b_cp = (
            economic["C_cp"]
            * (1 / self.stage_compressor_area_coef) ** self.beta_cp
            * (self.mpfc + self.mfc - 1)
            * self.uf_cp
            * self.k_er
        )
        self.b_exp = (
            economic["C_exp"]
            * (1 / self.stage_compressor_area_coef) ** self.beta_exp
            * (self.mpfc + self.mfc - 1)
            * self.uf_exp
            * self.k_er
        )

        self.bp_coef = economic["bp_coef"] if "bp_coef" in economic.keys() else 1.12
        self.p_coef = economic["p_coef"] if "p_coef" in economic.keys() else 0.2
        self.cmc_coef = economic["cmc_coef"] if "cmc_coef" in economic.keys() else 0.05
        # classical
        # self.cmc_coef = economic['cmc_coef'] if 'cmc_coef' in economic.keys() else 0.03
        self.lti_coef = economic["lti_coef"] if "lti_coef" in economic.keys() else 0.15
        self.loc_coef = economic["loc_coef"] if "loc_coef" in economic.keys() else 1.15
        self.dl_coef = economic["dl_coef"] if "dl_coef" in economic.keys() else 11
        self.i = economic["i"] if "i" in economic.keys() else 0.08
        self.z = economic["z"] if "z" in economic.keys() else 15
        ###MODIFICA AMALIA
        self.annual = 0.0224 * 3600

        self.cost_coef = self.bp_coef * (1 + self.p_coef)
        self.cost_coef1 = (self.cmc_coef + self.lti_coef) * self.cost_coef
        self.cost_coef2 = self.dl_coef * (1 + self.loc_coef)
        self.stc_coef = 0.1
        self.loss_coef = self.annual * self.k_gp
        self.amm = (
            self.i * ((1 + self.i) ** (self.z - 1)) / ((1 + self.i) ** self.z - 1)
        )

        self.generate_coef_log()
        if loading:
            self.load_coef_log()

    def except_when_none_value(self):
        if self.r is None:
            raise ValueError("process's objective function parameter 'R' is missing")
        if self.t is None:
            raise ValueError("process's objective function parameter 'T' is missing")
        if self.t_op is None:
            raise ValueError("process's objective function parameter 't_op' is missing")
        if self.phi is None:
            raise ValueError("process's objective function parameter 'phi' is missing")
        if self.kmf is None:
            raise ValueError("process's objective function parameter 'kmf' is missing")
        if self.mpfc is None:
            raise ValueError("process's objective function parameter 'mpfc' is missing")
        if self.mfc is None:
            raise ValueError("process's objective function parameter 'mfc' is missing")
        if self.eta_cp is None:
            raise ValueError(
                "process's objective function parameter 'eta_cp' is missing"
            )
        if self.eta_exp is None:
            raise ValueError(
                "process's objective function parameter 'eta_exp' is missing"
            )
        if self.eta_vp_0 is None:
            raise ValueError(
                "process's objective function parameter 'eta_vp_0' is missing"
            )
        if self.eta_vp_1 is None:
            raise ValueError(
                "process's objective function parameter 'eta_vp_1' is missing"
            )
        if self.cvp is None:
            raise ValueError("process's objective function parameter 'c_vp' is missing")
        if self.cc is None:
            raise ValueError("process's objective function parameter 'c_cp' is missing")
        if self.cexp is None:
            raise ValueError(
                "process's objective function parameter 'c_exp' is missing"
            )
        if self.uf_cp is None:
            raise ValueError(
                "process's objective function parameter 'UF_1968' is missing"
            )

        if self.k_er is None:
            raise ValueError("process's objective function parameter 'K_er' is missing")
        if self.k_el is None:
            raise ValueError("process's objective function parameter 'K_el' is missing")
        if self.uf_exp is None:
            raise ValueError(
                "process's objective function parameter 'UF_2000' is missing"
            )

    def load_coef(self, filename):
        """Parser for objective function's coefficient.
        Args:
            filename (str) : filename containing economic data information

        Raises:
            Exception : if datafile format is not respected

        Returns:
            a dictionary `economic` containing essential information to send
            to objective function's object
        """

        # list of validated coef
        validated_coefficients = [
            "R",
            "T",
            "eta_cp",
            "eta_vp_0",
            "eta_vp_1",
            "C_cp",
            "C_vp",
            "C_exp",
            "K_m",
            "K_mf",
            "K_mr",
            "K_el",
            "K_gp",
            "K_er",
            "MDFc",
            "MPFc",
            "MFc",
            "UF_2000",
            "UF_2000",
            "UF_2011",
            "UF_1968",
            "ICF",
            "nu",
            "t_op",
            "gamma",
            "phi",
            "a",
            "i",
            "z",
        ]

        economic = {}

        with open(filename, "r") as file:
            for line in file:
                if line == "\n":
                    pass
                elif line[0] == "#" or line[0] == "/*":
                    logger.info("Comments are ignored : %s", line)
                else:
                    line = line.split()
                    if line[0] != "param":
                        raise ValueError(
                            "Unkown keyword ({} != param)"
                            " in economic datafile ({})".format(line[0], filename)
                        )
                    if line[1] not in validated_coefficients:
                        raise ValueError(
                            "Unkown keyword coefficient ({})"
                            " in economic datafile ({})".format(line[1], filename)
                        )

                    economic[line[1]] = float(line[-1])

        return economic

    def generate_coef_log(self):
        """Generate coefficient expression into `coef.log`."""

        log_dir = generate_absolute_path() + "log" + os.path.sep
        with open(log_dir + "coefficient.log", "w") as file:

            file.write("param km = {} \n".format(self.km))
            file.write("param t_op = {} \n".format(self.t_op))
            file.write("param k_el = {} \n".format(self.k_el))
            file.write("param nu = {} \n".format(self.nu))
            file.write("param kmr = {} \n".format(self.kmr))
            file.write("param phi = {} \n".format(self.phi))
            file.write("param a = {} \n".format(self.a))
            file.write("param b_cp = {} \n".format(self.b_cp))
            file.write("param b_exp = {} \n".format(self.b_exp))
            file.write("param cvp = {} \n".format(self.cvp))

            file.write("param alpha_mem = {} \n".format(self.alpha_mem))
            file.write("param alpha_press_mem = {} \n".format(self.alpha_press_mem))
            file.write("param beta_cp = {} \n".format(self.beta_cp))
            file.write("param b_exp = {} \n".format(self.b_exp))

            file.write("param cost_coef = {} \n".format(self.cost_coef))
            file.write("param cost_coef1 = {} \n".format(self.cost_coef1))
            file.write("param cost_coef2 = {} \n".format(self.cost_coef2))
            file.write("param stc_coef = {} \n".format(self.stc_coef))
            file.write("param loss_coef = {} \n".format(self.loss_coef))
            file.write("param amm = {} \n".format(self.amm))

            file.flush()

    def load_coef_log(self):
        """Loading coefficient expression into obj instance."""

        log_dir = generate_absolute_path() + "log" + os.path.sep
        with open(log_dir + "coefficient.log", "r") as file:
            for line in file:
                if line == "\n":
                    pass
                elif line[0] == "#" or line[0] == "/*":
                    logger.info("Comments are ignored : %s", line)
                else:
                    line = line.split()
                    try:
                        getattr(self, line[1])
                    except AttributeError as e:
                        raise AttributeError(
                            "Attributes {} not defined".format(line[0])
                        )
                    else:
                        setattr(self, line[1], float(line[3]))

    def get_membrane_cost(self, model):
        """Membrane cost's expression.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process's model instance

        Returns:
            expression of membrane's cost
        """
        # i_ms
        # return sum(self.km * model.area[s] for s in model.states)
        return [self.km * model.area[s] for s in model.states]

    def get_membrane_frame_cost(self, model):
        """Membrane frame cost's expression.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process's model instance

        Returns:
            expression of membrane frame's cost
        """
        am = sum(model.area[s] for s in model.states)
        # i_mfs
        if self.parameter.uniform_pup:
            i_mfs = [
                self.a
                * (model.area[s] ** self.alpha_mem)
                * (model.pressure_up**self.alpha_press_mem)
                for s in model.states
            ]
        else:
            i_mfs = [
                self.a
                * (model.area[s] ** self.alpha_mem)
                * (model.pressure_up[s] ** self.alpha_press_mem)
                for s in model.states
            ]

        return i_mfs

    def power_compressing_permeate(self, model):
        """Expression of the power required to compressing permeate stream.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process's model instance

        Returns:
            expression of the power required to compress permeate stream.
        """
        wcp_s = []
        power_exp = (self.gamma - 1) / self.gamma
        # one term for each permeated flow
        for s in model.states:
            # setting the output pressure of the PERM flow

            if self.parameter.vp:
                press_down = 1
            else:
                press_down = model.pressure_down[s]

            cmpr_ = 0
            for s1 in model.states:
                flow = model.splitPERM[s, s1]
                wcp_s_factor1 = (flow * 1e-3) / self.eta_cp
                wcp_s_factor2 = (self.gamma * self.r * self.t) / (self.gamma - 1)

                if self.parameter.uniform_pup:
                    pressure_ratio = model.pressure_up / press_down
                else:
                    pressure_ratio = model.pressure_up[s1] / press_down

                wcp_s_factor3 = (pressure_ratio**power_exp) - 1
                cmpr_ += wcp_s_factor1 * wcp_s_factor2 * wcp_s_factor3

            wcp_s.append(cmpr_)

        # return sum(wcp_s[index] for index in range(len(wcp_s)))
        return wcp_s

    def power_compressing_retenta(self, model):
        """Expression of the power required to compressing retenta stream.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process's model instance

        Returns:
            expression of the power required to compress retenta stream.
        """
        wcp_s = []
        power_exp = (self.gamma - 1) / self.gamma
        # one term for each rententa flow
        for s in model.states:
            # setting the output pressure of the PERM flow

            cmpr_ = 0
            for s1 in model.states:
                flow = model.splitRET[s, s1]
                wcp_s_factor1 = (flow * 10**-3) / self.eta_cp
                wcp_s_factor2 = (self.gamma * self.r * self.t) / (self.gamma - 1)

                if self.parameter.uniform_pup:
                    # not using compressor (same pression)
                    wcp_s_factor3 = 0
                else:
                    if s <= s1:
                        # skip
                        wcp_s_factor3 = 0
                    else:
                        pressure_ratio = model.pressure_up[s1] / model.pressure_up[s]
                        wcp_s_factor3 = (pressure_ratio**power_exp) - 1

                cmpr_ += wcp_s_factor1 * wcp_s_factor2 * wcp_s_factor3

            wcp_s.append(cmpr_)

        # return sum(wcp_s[index] for index in range(len(wcp_s)))
        return wcp_s

    def power_compressor_feed(self, model):
        """Expression of the power required to compressing fresh feed stream.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process's model instance

        Returns:
            expression of the power required to compress fresh feed stream.
        """
        # one term for the FEED
        wcp_f = []
        power_exp = (self.gamma - 1) / self.gamma
        for s in model.states:
            flow = model.splitFEED[s]

            wcp_f_factor1 = (flow * 1e-3) / self.eta_cp
            wcp_f_factor2 = (self.gamma * self.r * self.t) / (self.gamma - 1)

            if model.pressure_in.value <= model.lb_press_up.value:
                if self.parameter.uniform_pup:
                    pressure_ratio = model.pressure_up / model.pressure_in
                else:
                    pressure_ratio = model.pressure_up[s] / model.pressure_in

                wcp_f_factor3 = (pressure_ratio**power_exp) - 1
            else:
                wcp_f_factor3 = 0

            wcp_f.append(wcp_f_factor1 * wcp_f_factor2 * wcp_f_factor3)

        # return sum(wcp_f[index] for index in range(len(wcp_f)))
        return wcp_f

    def power_compressor_product(self, model):
        """Expression of compressor energy consumption required for the product
        stream.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process's model instance

        Returns:
            expression of the power required to compress the product stream.
        """
        power_exp = (self.gamma - 1) / self.gamma
        flow = model.OUT_prod
        if model.pressure_prod.value != -1:
            wcprod_factor1 = (flow * 1e-3) / self.eta_cp
            wcprod_factor2 = (self.gamma * self.r * self.t) / (self.gamma - 1)

            if self.parameter.uniform_pup:
                pressure_ratio = model.pressure_prod / model.pressure_up
            else:
                raise NotImplementedError(
                    "Incoherence (pressure_prod and pressure not uniform):"
                    " not implemented"
                )
                # assert False
                # final_pup = model.pressure_up[model.states.last()]
                # pressure_ratio = model.pressure_prod / final_pup

            wcprod_factor3 = (pressure_ratio**power_exp) - 1

            return wcprod_factor1 * wcprod_factor2 * wcprod_factor3
        else:
            return 0

    def power_expander_product(self, model):
        """Expression of expander energy consumption required for the product
        stream.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process's model instance

        Returns:
            expression of the power required to compress product stream.
        """
        power_exp = (self.gamma - 1) / self.gamma
        flow = model.OUT_prod
        if model.pressure_prod.value != -1:
            wcprod_factor1 = (flow * 1e-3) / self.eta_exp
            wcprod_factor2 = (self.gamma * self.r * self.t) / (self.gamma - 1)

            if self.parameter.uniform_pup:
                pressure_ratio = model.pressure_prod / model.pressure_up
            else:
                raise NotImplementedError(
                    "Incoherence (pressure_prod and pressure not uniform):"
                    " not implemented"
                )
                # assert False
                # final_pup = model.pressure_up[model.states.last()]
                # pressure_ratio = model.pressure_prod / final_pup

            wcprod_factor3 = (pressure_ratio**power_exp) - 1

            return -1 * (wcprod_factor1 * wcprod_factor2 * wcprod_factor3)
        else:
            return 0

    def power_vacuum_pump(self, model):
        """Expression of vacuum pump energy consumption.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process's model instance

        Returns:
            expression of the power required to compress vacuum pump stream.
        """
        power_exp = (self.gamma - 1) / self.gamma
        w_ivps = []
        for s in model.states:
            if self.parameter.vp:
                flow = (
                    sum(model.splitPERM[s, s1] for s1 in model.states)
                    + model.splitOutPERM[s]
                )
                pressure_ratio = 1.0 / model.pressure_down[s]

                eta_vp = (
                    self.eta_vp_1 * pe.log(model.pressure_down[s] / 1) + self.eta_vp_0
                )

                wcp_s_factor3 = (pressure_ratio**power_exp) - 1
                wcp_s_factor1 = (flow * 1e-3) / eta_vp
                wcp_s_factor2 = (self.gamma * self.r * self.t) / (self.gamma - 1)

                w_ivps.append(wcp_s_factor1 * wcp_s_factor2 * wcp_s_factor3)
            else:
                w_ivps.append(0)

        # return sum(w_ivps[index] for index in range(len(w_ivps)))
        return w_ivps

    def get_stage_compressor_cost(self, model):
        """Expression of compressor cost at membrane's stage level.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process's model instance

        Returns:
            expression compresor cost at membrane's stage level.
        """
        # i_ccs
        # wcp = self.power_compressing_permeate(model) + self.power_compressing_retenta(model)
        # iccs_ = self.b_cp * (wcp ** self.beta_cp)
        # return iccs_, wcp

        wcps_perm = self.power_compressing_permeate(model)
        wcps_ret = self.power_compressing_retenta(model)

        i_ccs = []
        for s in model.states:
            # because decalage
            mem = s - 1
            # PERM cases
            ics_perm = self.b_cp * (wcps_perm[mem] ** self.beta_cp)
            ics_ret = self.b_cp * (wcps_ret[mem] ** self.beta_cp)

            i_ccs.append(ics_perm + ics_ret)

        return i_ccs, sum(wcps_perm[s - 1] + wcps_ret[s - 1] for s in model.states)

    def get_feed_compressor_cost(self, model):
        """Expression of compressor cost at system's feed level.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process's model instance

        Returns:
            expression compresor cost at system's feed level.
        """
        # # i_ccf
        # wcp_f = self.power_compressor_feed(model)
        # i_ccf_ = self.b_cp * (wcp_f ** self.beta_cp)
        #
        # return i_ccf_, wcp_f

        wcps_feed = self.power_compressor_feed(model)

        i_ccf = []
        for s in model.states:
            # because decalage
            mem = s - 1
            i_ccf.append(self.b_cp * (wcps_feed[mem] ** self.beta_cp))

        return i_ccf, sum(wcps_feed[s - 1] for s in model.states)

    def get_product_compressor_cost(self, model):
        """Expression of compressor cost at system's product collect level.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process's model instance

        Returns:
            expression compresor cost at system's product collect level.
        """
        # i_cprod
        wcp_prod = self.power_compressor_product(model)
        icprod_ = self.b_cp * (wcp_prod**self.beta_cp)

        return (icprod_, wcp_prod)

    def get_expander_cost(self, model):
        """Expression of expander cost.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process's model instance

        Returns:
            expression expander cost.
        """
        # i_exp
        w_exp = self.power_expander_product(model)
        iexp_ = self.b_exp * (w_exp**self.beta_exp)

        return (iexp_, w_exp)

    def get_vacuum_pump_cost(self, model):
        """Expression of vacuum pump cost.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process's model instance

        Returns:
            expression of vacuum pump cost.
        """
        # # i_vps
        # w_vps = self.power_vacuum_pump(model)
        # i_vps_ = self.cvp * w_vps
        #
        # return i_vps_, w_vps

        w_vps = self.power_vacuum_pump(model)
        i_vps = []
        for s in model.states:
            mem = s - 1
            i_vps.append(self.cvp * w_vps[mem])

        return i_vps, sum(w_vps[s - 1] for s in model.states)

    def contract_maintenance(self, model):
        return self.cost_coef1 * self.i_tot

    def labor(self, model):
        return self.cost_coef2 * self.t_op

    def membrane_replacement(self, model):
        """Expression of membrance replacement cost.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process model's instance

        Returns:
            expression of membrance replacement cost.
        """
        # mrc
        ams = sum(model.area[s] for s in model.states)
        return ams * self.nu * self.kmr

    def energy_cost(self, model, wcf, wcprod, wiexp, wcs, wvps):
        """Expression of global system 's total power cost.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process's model instance

            wcf (`Float`) : power cost required to compress feed's stream

            wcprod (`Float`) : power cost required to compress the product's stream

            wiexp (`Float`) : power cost required to compress expander's stream

            wcs (`Float`) : power cost required to compress stage flow stream

            wvps (`Float`) : power cost required to compress vacuum pump's stream

        Returns:
            returns expression of the system's power cost.
        """
        wtot = 0
        # ec
        # # TODO: ask berna
        if model.pressure_prod.value != -1:
            # expander and compressor are not used (pressure_prod = False)
            # wtot = sum(
            #     wcf[s-1] +
            #     wcs[s-1] +
            #     wvps[s-1]
            #     for s in model.states) / self.phi
            wtot = (wcf + wcs + wvps) / self.phi

        else:
            if model.ub_press_up.value <= model.pressure_prod.value:
                # using compressor on RET flow
                # wtot = (
                #     sum(wcf[s-1] + wcs[s-1] + wvps[s-1] for s in model.states) +
                #     wcprod
                #     ) / self.phi

                wtot = (wcf + wcs + wvps + wcprod) / self.phi

            if model.lb_press_up.value >= model.pressure_prod.value:
                # using expander for F_prod
                # wtot = sum(
                #     wcf[s-1] + wcs[s-1] + wvps[s-1] for s in model.states
                #     ) / self.phi - (self.phi * wiexp)

                wtot = (wcf + wcs + wvps) / self.phi - (self.phi * wiexp)

        return self.t_op * wtot * self.k_el

    def total_equipement(self, model):
        """Expression of system's capital cost.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process's model instance

        Attributes:
            ims (`float`) : membrane cost

            i_mfs (`float`) : membrane frame cost

            i_ccs (`float`) : stage compresor cost

            i_ccf (`float`) : feed compresor cost

            i_vps (`float`) : vacuum pump cost

            i_cprod (`float`) : final product compresor cost

            i_exp (`float`) : final product expander cost

        Returns:
            expression of the system's total capital cost.
        """
        # if not pressure_prod
        if model.pressure_prod.value == -1:

            return sum(
                self.ims[s - 1]
                + self.i_mfs[s - 1]
                + self.i_ccs[s - 1]
                + self.i_ccf[s - 1]
                + self.i_vps[s - 1]
                for s in model.states
            )
        else:
            if model.ub_press_up.value <= model.pressure_prod.value:
                # compressor
                return (
                    sum(
                        self.ims[s - 1]
                        + self.i_mfs[s - 1]
                        + self.i_ccs[s - 1]
                        + self.i_ccf[s - 1]
                        + self.i_vps[s - 1]
                        for s in model.states
                    )
                    + self.i_cprod
                )

            if model.lb_press_up.value >= model.pressure_prod.value:
                # expander
                return (
                    sum(
                        self.ims[s - 1]
                        + self.i_mfs[s - 1]
                        + self.i_ccs[s - 1]
                        + self.i_ccf[s - 1]
                        + self.i_vps[s - 1]
                        for s in model.states
                    )
                    + self.i_exp
                )

        logger.exception(
            "Incoherence between feed pressure and pressure up's bounds"
            "pressure_in > lb_press_up and pressure_in < ub_press_up"
        )
        raise ValueError(
            "Incoherence between feed pressure and bounds on pressure up"
            "pressure_in > lb_press_up and pressure_in < ub_press_up"
        )

    def operational_expenditure(self):
        """Expression of the operational cost of the desing process System.

        Attributes:
            cmc (`Float`) : contract and material maintenance cost

            cmc (`Float`) : contract and material maintenance cost

            cmc (`Float`) : contract and material maintenance cost

            ec (`Float`) : energy cost

        Returns:
            expression of operational cost
        """
        return self.cli + self.dlc + self.ec + self.mrc

    def total_facility_invest(self):
        """Expression of total facility invest cost.

        Args:
            i_tot (`Float`) : contingency cost

        Returns:
            expression of total facility invest cost.
        """
        return self.cost_coef * self.i_tot

    def startup_cost(self):
        return self.stc_coef * self.opex

    def total_capital_cost(self):
        """Expression of system's capital cost.

        Attributes:
            tfi (`Float`) : total facility investment

            stc (`float`) : start - up cost

        Returns:
            expression of the system's total capital cost.
        """
        return self.tfi + self.stc

    def annual_product_loss(self, model):
        """Expression of the annual production losses.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process's model instance

        Returns:
            expression of annual production losses
        """
        if not self.k_gp:
            return 0

        return (model.OUT_waste * self.loss_coef * self.t_op) * (
            model.XOUT_waste[model.final_product] / model.XOUT_prod[model.final_product]
        )

    def total_annual_cost(self):
        """Expression of the annual total cost.

        Args:
            capex (`Float`) : total capital cost

            opex (`Float`) : total operational expenditure

            apl (`Float`) : annual production losses

        Returns:
            expression of annual total cost.
        """
        return self.capex * self.amm + self.opex + self.apl

    def specific_product_separation(self, model):
        """Expression of the specific separation cost.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process's model instance

            tac (`Float`) : annual total cost

        Returns:
            expression of the specific separation cost Euro per ton OR Euro per Nm3.
        """
        product_annual_separation = (
            model.OUT_prod
            * model.XOUT_prod[model.final_product]
            * model.molarmass[model.final_product]
            * 1e-6
            * 3600
            * self.t_op
        )
        # self.annual * self.t_op)

        return self.tac / product_annual_separation

    def objective_function(self, model):
        """Expression of objective's function formulation.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process's model instance

        Returns:
            return objective's funcion expression.
        """

        # Equipement cost (remark w represent power)
        self.ims = self.get_membrane_cost(model)
        self.i_mfs = self.get_membrane_frame_cost(model)
        self.i_ccs, wcs = self.get_stage_compressor_cost(model)
        self.i_ccf, wcf = self.get_feed_compressor_cost(model)
        self.i_cprod, wcprod = self.get_product_compressor_cost(model)
        self.i_exp, wiexp = self.get_expander_cost(model)
        self.i_vps, wvps = self.get_vacuum_pump_cost(model)

        self.i_tot = self.total_equipement(model)
        self.cli = self.contract_maintenance(model)
        self.dlc = self.labor(model)
        self.ec = self.energy_cost(model, wcf, wcprod, wiexp, wcs, wvps)
        self.mrc = self.membrane_replacement(model)

        self.opex = self.operational_expenditure()

        self.tfi = self.total_facility_invest()
        self.stc = self.startup_cost()

        self.capex = self.total_capital_cost()

        self.apl = self.annual_product_loss(model)
        self.tac = self.total_annual_cost()
        self.sc_prod = self.specific_product_separation(model)

        # sum of expression
        self.ims = sum(self.ims)
        self.i_mfs = sum(self.i_mfs)
        self.i_ccs = sum(self.i_ccs)
        self.i_ccf = sum(self.i_ccf)
        self.i_vps = sum(self.i_vps)

        # TODO: changer le cout à volonté
        return self.sc_prod


# TODO: preparer le pg pour utiliser le metamodel
# TODO: threads
# TODO: voir pour le fichier log
