"""Evaluating objective function given a solution [economic formalism]."""

import logging
import os

from pyomo.core.expr.visitor import evaluate_expression
import pyomo.environ as pe
import matplotlib.pyplot as plt

# logging variable
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
# handler = logging.FileHandler(filename)
logger.addHandler(handler)
formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s : %(message)s',
                              datefmt='%a, %d %b %Y %H:%M:%S')
handler.setFormatter(formatter)


class PostProcess():
    """Object used to :
        - evaluate
        - and doing other operations

    on post's solution of model's instance.
    """
    def evaluate_objective(self, model):
        """Evaluate objective's function.

        Args:
            model (mind.system.MembranesDesignModel) : desing process model's instance

        Returns:
            return objective's function value

        """

        # print("economic = ", evaluate_expression(model.objeco_.expr))
        # print("generalized = ", evaluate_expression(model.objgen_.expr))
        return evaluate_expression(model.obj.expr)

    def evaluate_feasibility(self, model):
        """Evaluate feasibility constraint of a solution.

        Evaluate objective's function.

        Args:
            model (mind.system.MembranesDesignModel) : desing process model's instance

        Note:

            generate `constraint.log` for each insatisfacted constraint.

        """
        log_dir = generate_absolute_path() + "log" + os.path.sep
        filename = (log_dir + 'constraint.log')
        outfile = open(filename, 'w')

        tol_ctr = 1e-3
        for ctr in model.component_data_objects(ctype=pe.Constraint,
                                                active=True):
            my_printing_format = False
            maj = 0  # this variable serve to delete blankline in final result
            if ctr.equality:
                # Equality constraint
                if abs(pe.value(ctr.lower) - pe.value(ctr.body)) >= tol_ctr:
                    outfile.write(ctr.name + " (Equality): " +
                                  str(pe.value(ctr.lower)) + " <= " +
                                  str(pe.value(ctr.body)) + " <= " +
                                  str(pe.value(ctr.upper)) + "\n")
            else:
                if (ctr.lower is not None and
                    (pe.value(ctr.lower) - pe.value(ctr.body) > tol_ctr)):
                    # Check constraint lower bound

                    # invalid lower bound
                    # print(
                    #     ctr.name
                    #     + " (Lb bound): "
                    #     + str(pe.value(ctr.lower))
                    #     + " <= "
                    #     + str(pe.value(ctr.body)),
                    #     end=''
                    # )
                    outfile.write(ctr.name + " (Lb bound): " +
                                  str(pe.value(ctr.lower)) + " <= " +
                                  str(pe.value(ctr.body)))
                    my_printing_format = True
                    maj += 1

                # Check constraint upper bound
                if (ctr.upper is not None and
                    (pe.value(ctr.body) - pe.value(ctr.upper) > tol_ctr)):
                    # invalid upper bound
                    maj += 1
                    if my_printing_format:
                        # print(
                        #     "\t AND (Ub bound)\t "
                        #     + str(pe.value(ctr.body))
                        #     + " <= "
                        #     + str(pe.value(ctr.upper)),
                        #     end=''
                        # )
                        outfile.write("\t AND (Ub bound)\t " +
                                      str(pe.value(ctr.body)) + " <= " +
                                      str(pe.value(ctr.upper)))
                    else:
                        # print(
                        #     ctr.name
                        #     + " (Ub bound): "
                        #     + str(pe.value(ctr.body))
                        #     + " <= "
                        #     + str(pe.value(ctr.upper)),
                        #     end=''
                        # )
                        outfile.write(ctr.name + " (Ub bound): " +
                                      str(pe.value(ctr.body)) + " <= " +
                                      str(pe.value(ctr.upper)))
                if maj != 0:
                    # print()
                    outfile.write("\n")

        # add variables bound checking
        # TODO: variables bounds must be checked

    def histogramme_opex(self, obj_object):
        """Histogram of opex values.

        Args:
            model (`mind.system.MembranesDesignModel`) : desing process instance

            parameter (`mind.builder.Configuration`) : desing process configuration

        Returns:
            plot the opex histogram.
        """
        plt.clf()
        # TODO: print plot by max to min value
        ec =  [evaluate_expression(obj_object.ec)]
        cli =  [evaluate_expression(obj_object.cli)]

        opex =  [evaluate_expression(obj_object.opex)]

        obj_1 = (ec, 'red', f"Energy ({round(ec[0], 2)})")
        obj_2 = (cli, 'blue', f"Maintain ({round(cli[0], 2)})")
        obj_struct = [obj_1, obj_2]
        obj_struct.sort(reverse=True)

        r = range(len(ec))

        plt.bar(r,
                opex,
                width=0.8,
                color=['black' for i in ec],
                linestyle='solid',
                linewidth=3,
                label='Opex')

        for obj in obj_struct:
            plt.bar(r,
                    obj[0],
                    width=0.8,
                    color=[obj[1] for i in ec],
                    linestyle='solid',
                    linewidth=3,
                    label=obj[2])

        plt.xticks(range(len(ec)), ['Best'])
        plt.legend()
        plt.show()


    def generate_sol_log(self, model, fname, obj_object):
        """generate some objective expression and save it to `fname`.

        Args:
            fname (`str`) : path to output file

            obj_object : objective function object
        """
        with open(fname, 'w') as file:
            file.write("Ims = " + str(evaluate_expression(obj_object.ims)) + "\n")

            file.write("imfs = " + str(evaluate_expression(obj_object.i_mfs)) + "\n")

            file.write("icc_s = " + str(evaluate_expression(obj_object.i_ccs)) + "\n")

            file.write("icc_f = " + str(evaluate_expression(obj_object.i_ccf)) + "\n")

            if model.pressure_prod.value != -1:
                file.write("icc_prod = " + str(evaluate_expression(obj_object.i_cprod)) + "\n")

                file.write("icc_exp = " + str(evaluate_expression(obj_object.i_exp)) + "\n")

            file.write("ivp = " + str(evaluate_expression(obj_object.i_vps)) + "\n")

            file.write(
                "------------------------------------------------------------" +
                "\n")

            # file.write("wcc_s = " + str(self.wcc_s) + "\n")
            #
            # file.write("wcc_f = " + str(self.wcc_f) + "\n")
            #
            # if parameter["pressure_prod"]:
            #     file.write("wcc_prod = " + str(self.wcc_prod) + "\n")
            #
            #     file.write("wcc_exp = " + str(self.wcc_exp) + "\n")
            #
            # file.write("wvp = " + str(self.wvp) + "\n")
            #
            # file.write(
            #     "----------------------------------------------------- " + "\n")

            file.write("Energy cost = " + str(evaluate_expression(obj_object.ec)) + "\n")

            file.write("contract maintenance cost = " + str(evaluate_expression(obj_object.cli)) + "\n")

            file.write(
                "----------------------------------------------------- " + "\n")

            file.write("Total annual cost = " + str(evaluate_expression(obj_object.tac)) + "\n")

            file.write("Separation cost = " + str(evaluate_expression(obj_object.sc_prod)) + "\n")


    def histogram_capex(self, model, obj_object):
        """Histogram of capex values.

        Args:
            model (`mind.system.MembranesDesignModel`) : desing process instance

        Returns:
            plot the capex histogram.
        """
        plt.clf()
        # TODO: print plot by max to min value
        x1 =  evaluate_expression(obj_object.ims)
        x2 =  evaluate_expression(obj_object.i_mfs)

        if model.pressure_prod.value != -1:
            if model.ub_press_up.value <= model.pressure_prod.value:
                # using compressor on RET flow
                x3 = obj_object.i_ccs + obj_object.i_ccf + obj_object.i_cprod
            if model.lb_press_up.value >= model.pressure_prod.value:
                # using expander for F_prod
                x3 = obj_object.i_ccs + obj_object.i_ccf + obj_object.i_exp
        else:
            x3 = obj_object.i_ccs + obj_object.i_ccf


        x4 = obj_object.i_vps
        x3 = evaluate_expression(x3)
        x4 = evaluate_expression(x4)

        x1 = [x1]
        x2 = [x2]
        x3 = [x3]
        x4 = [x4]
        capex = [evaluate_expression(obj_object.capex)]

        # print(x1)
        # print(x2)
        # print(x3)
        # print(x4)
        # print(capex)

        obj_1 = (x1, 'red', f"IMS ({round(x1[0], 2)})")
        obj_2 = (x2, 'blue', f"IMFS ({round(x2[0], 2)})")
        obj_3 = (x3, 'green', f"ICC ({round(x3[0], 2)})")
        obj_4 = (x4, 'cyan', f"IVP ({round(x4[0], 2)})")
        obj_struct = [obj_1, obj_2, obj_3, obj_4]
        obj_struct.sort(reverse=True)

        r = range(len(x1))
        plt.bar(r,
                capex,
                width=0.8,
                color=['black' for i in x1],
                linestyle='solid',
                linewidth=3,
                label='Capex')

        for obj in obj_struct:
            plt.bar(r,
                    obj[0],
                    width=0.8,
                    color=[obj[1] for i in x1],
                    linestyle='solid',
                    linewidth=3,
                    label=obj[2])

        plt.xticks(range(len(x1)), ['Best'])
        plt.legend()
        plt.show()
