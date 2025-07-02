"""Output printing functions.

Printing functions are described in this module.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches


def print_model_solution(model, outfile, parameter, behavior, flows=False):
    """ Print in outfile, the feasible solution obtained.

    Args:

        model (`Pyomo's model instance`) : constructed model of membrane design model.

        outfile (_io.TextIOWrapper) : output file for writing.

        parameter (`mind.builder.Configuration`) : design process configuration.

        behavior (`mind.membranes.MembranesTypes`) : desing process's membrane object description

        flows (bool) : `True` if printing variables related to flows quantity
        (`default = False`).
    """

    for s in model.states:
        outfile.write("splitFEED_frac[" + str(s) + "] " +
                      '{0:01.3f}  '.format(model.splitFEED_frac[s].value) +
                      "\n")
    for s in model.states:
        for s1 in model.states:
            outfile.write("splitRET_frac[" + str(s) + "," + str(s1) + "] " +
                          '{0:01.3f}  '.format(model.splitRET_frac[s,
                                                                   s1].value) +
                          "\n")

        outfile.write("splitOutRET_frac[" + str(s) + "] " +
                      '{0:01.3f}  '.format(model.splitOutRET_frac[s].value) +
                      "\n")

        for s1 in model.states:
            outfile.write("splitPERM_frac[" + str(s) + "," + str(s1) + "] " +
                          '{0:01.3f}  '.format(model.splitPERM_frac[s,
                                                                    s1].value) +
                          "\n")

        outfile.write("splitOutPERM_frac[" + str(s) + "] " +
                      '{0:01.3f}  '.format(model.splitOutPERM_frac[s].value) +
                      "\n")

    for s in model.states:
        outfile.write("Area[" + str(s) + "] " +
                      '{0:10.2f}'.format(model.area[s].value) + "\n")

    if parameter.uniform_pup:
        outfile.write('pressure_up {0:4.2f}'.format(model.pressure_up.value) +
                      "\n")
    else:
        for s in model.states:
            outfile.write("pressure_up[" + str(s) + "] " +
                          ' {0:4.2f}'.format(model.pressure_up[s].value) + "\n")

    for s in model.states:
        outfile.write("pressure_down[" + str(s) + "] " +
                      ' {0:4.2f}'.format(model.pressure_down[s].value) + "\n")

    # print permeability informations
    behavior.print_permeability_variable(model, parameter, outfile)

    # print output values
    outfile.write("output prod " + str(model.OUT_prod.value) + "\n")

    for c in model.components:
        outfile.write("composition (" + str(c) + ") in output prod " +
                      str(model.lb_perc_prod[c]) + str(" <= ") +
                      str(model.XOUT_prod[c].value) + str(" <= ") +
                      str(model.ub_perc_prod[c]) + "\n")

    outfile.write("output waste " + str(model.OUT_waste.value) + "\n")

    for c in model.components:
        outfile.write("composition (" + str(c) + ") in output waste " +
                      str(model.lb_perc_waste[c]) + str(" <= ") +
                      str(model.XOUT_waste[c].value) + str(" <= ") +
                      str(model.ub_perc_waste[c]) + "\n")

    if (flows):
        for s in model.states:
            outfile.write("splitFEED[" + str(s) + "] " +
                          str(model.splitFEED[s].value) + "\n")

        for s in model.states:
            outfile.write("splitOutRET[" + str(s) + "] " +
                          str(model.splitOutRET[s].value) + "\n")

            for s1 in model.states:
                outfile.write("splitRET[" + str(s) + "," + str(s1) + "] " +
                              str(model.splitRET[s, s1].value) + "\n")

            outfile.write("splitOutPERM[" + str(s) + "] " +
                          str(model.splitOutPERM[s].value) + "\n")

            for s1 in model.states:
                outfile.write("splitPERM[" + str(s) + "," + str(s1) + "] " +
                              str(model.splitPERM[s, s1].value) + "\n")
    outfile.write("\n")
    outfile.flush()


# try to print something with matplotlib
def plotting_solution(model, parameter, plt_show=True):
    """ Plotting current solution saved in model.

    Args:

        model (`Pyomo's model instance`) : constructed model of membrane design model.

        parameter (`mind.builder.Configuration`) : design process configuration.

        plt_show (bool) : `True` if plotting in screen
        `Else` save figure (`plotting.png`).
    """
    area = []
    if plt_show:
        fontSize = 8
        flow_out_size = 9
        final_flow_size = 10
    else:
        fontSize = 4
        flow_out_size = 5
        final_flow_size = 6
    plt.rcParams.update({'font.size': fontSize})
    nb_mem = len(model.states)
    x_mem = 0
    y_mem = 0
    mem_width = 4
    mem_height = 1
    y_position = 10 + mem_height
    line_width = 8
    fig = plt.figure()
    ax = fig.add_axes([0, 0, 1, 1])
    tab_patches = []

    # pretraitement
    for s in model.states:
        area.append(round(model.area[s].value, 2))

    plt.arrow((x_mem - line_width) - 0.2, (y_position + 0.5),
              line_width,
              0,
              head_width=0.5,
              head_length=0.2,
              fc='r',
              ec='r')

    plt.text((x_mem - line_width), (y_position - 0.5), "FEED")

    # flow values
    plt.text((x_mem - line_width), (y_position - 2),
             "F = " + str(model.FEED.value) + " mol/s")
    # total area
    plt.text(
        (x_mem - line_width), (y_position - 2.8), "At = " +
        str(round(sum(model.area[s].value for s in model.states), 2)) + " m^2")

    # composition in each elements
    position = 4.5
    for j in model.components:
        plt.text((x_mem - line_width), (y_position - position),
                 str(model.XIN[j] * 100) + " % " + str(j))
        position -= 0.8

    for i in range(nb_mem):
        # print inlet mem informations
        position = 0.8
        # components
        for j in model.components:
            plt.text((x_mem - (3 * line_width / 4)),
                     (y_position + mem_height + position),
                     str(round(model.XIN_mem[(i + 1), j].value * 100, 2)) +
                     " % " + str(j))
            position += 0.8
        # Permeability
        # for j in model.components:
        #     mem_type = model.mem_type[i+1]
        #     plt.text(
        #         (x_mem - (3*line_width/4)),
        #         (y_position + mem_height + position),
        #         "Perm[" + str(j) + "] = "
        #         + str(
        #             round(model.Permeability[j, mem_type].value / 3.347e-05, 2)
        #             )
        #         + " barrer"
        #         )
        #     position += 1
        position += 0.8
        # flows
        plt.text(
            (x_mem - (3 * line_width / 4)),
            (y_position + mem_height + position),
            "F = " + str(round(model.Feed_mem[(i + 1)].value, 2)) + " mol/s")
        position += 0.8

        # pression
        if parameter.uniform_pup:
            # down
            plt.text((x_mem - (3 * line_width / 4)),
                     (y_position + mem_height + position), "Down : " +
                     str(round(model.pressure_down[(i + 1)].value, 2)) + " bar")
            position += 0.8
            # up
            plt.text((x_mem - (3 * line_width / 4)),
                     (y_position + mem_height + position),
                     "up : " + str(round(model.pressure_up.value, 2)) + " bar")
            position += 0.8

        else:
            # down
            plt.text((x_mem - (3 * line_width / 4)),
                     (y_position + mem_height + position), "Down : " +
                     str(round(model.pressure_down[(i + 1)].value, 2)) + " bar")
            position += 0.8
            # up
            plt.text((x_mem - (3 * line_width / 4)),
                     (y_position + mem_height + position), "up : " +
                     str(round(model.pressure_up[(i + 1)].value, 2)) + " bar")
            position += 0.8

        p = patches.Rectangle((x_mem, y_position),
                              mem_width,
                              mem_height,
                              fill=False,
                              edgecolor='g',
                              linewidth=1)
        tab_patches.append(p)

        # stage (num)
        # print Area value
        plt.text((x_mem), (y_position + mem_height + 1.3),
                 "Stage " + str(i + 1))

        plt.text((x_mem), (y_position + mem_height + 0.3),
                 "A = " + str(area[i]) + " m^2")

        if i != (nb_mem - 1):
            # plt.plot(
            #     [x_mem + mem_width, x_mem + (mem_width+4)],
            #     [(mem_height/2), (mem_height/2)]
            # )

            plt.arrow((x_mem + mem_width), (y_position + 0.5),
                      (line_width - 0.2),
                      0,
                      head_width=0.5,
                      head_length=0.2,
                      fc='k',
                      ec='k')

        # RET lines

        position = 10
        for s1 in model.states:
            plt.text((x_mem - (3 * line_width / 4)),
                     (y_position + mem_height + position),
                     "RET[" + str(s1) + " -> " + str(i + 1) + "] = " +
                     str(round(model.splitRET[s1,
                                              (i + 1)].value, 2)) + " mol/s")

            position += 2

        # split feed
        plt.text((x_mem - (3 * line_width / 4)),
                 (y_position + mem_height + position), "FEED = " +
                 str(round(model.splitFEED[(i + 1)].value, 2)) + " mol/s")
        position += 2

        plt.arrow((x_mem - (line_width / 2)), (y_position + mem_height + 10),
                  0,
                  -2,
                  head_width=0.5,
                  head_length=0.2,
                  fc='b',
                  ec='b')

        # PERM lines
        position = 15
        for s1 in model.states:
            plt.text((x_mem - (3 * line_width / 4)), (y_position - position),
                     "PERM[" + str(s1) + " -> " + str(i + 1) + "] = " +
                     str(round(model.splitPERM[s1,
                                               (i + 1)].value, 2)) + " mol/s")
            position -= 2

        plt.arrow((x_mem - (line_width / 2)), (y_position - 8),
                  0,
                  +3,
                  head_width=0.5,
                  head_length=0.2,
                  fc='r',
                  ec='r')

        # RET out
        position = 5
        plt.text(
            (x_mem + mem_width - 0.7), (y_position + mem_height + position),
            "RET_out = " + str(round(model.splitOutRET[(i + 1)].value, 2)) +
            " mol/s",
            rotation='vertical',
            style='italic',
            color="blue",
            fontsize=flow_out_size)

        # component of ret element
        decalage = 0.7
        n = 0
        for j in model.components:
            plt.text(
                (x_mem + mem_width + n * decalage),
                (y_position + mem_height + position),
                str(round(model.X_RET_mem[(i + 1), j].value * 100, 2)) + " % " +
                str(j),
                rotation='vertical',
                color="blue",
            )
            n += 1

        # PERM out
        position = 10
        plt.text((x_mem + mem_width - 0.7), (y_position - position),
                 "PERM_out = " +
                 str(round(model.splitOutPERM[(i + 1)].value, 2)) + " mol/s",
                 rotation='vertical',
                 style='italic',
                 color="red",
                 fontsize=flow_out_size)

        # component of perm element
        decalage = 0.7
        n = 0
        for j in model.components:
            plt.text(
                (x_mem + mem_width + n * decalage),
                (y_position - position),
                str(round(model.X_PERM_mem[(i + 1), j].value * 100, 2)) +
                " % " + str(j),
                rotation='vertical',
                color="red",
            )
            n += 1

        # update x_mem and y_mem for next iteration
        x_mem += mem_width + line_width
        y_mem += 0

    # at the end of loops
    # print(tab_patches)
    for i in range(nb_mem):
        ax.add_patch(tab_patches[i])

    # ax.add_patch(p1)

    # output
    plt.arrow((x_mem - line_width), (y_position + 0.5), (line_width - 0.2),
              0,
              head_width=0.5,
              head_length=0.2,
              fc='r',
              ec='r')

    position = 0.3
    plt.text((x_mem - (line_width / 2)), (y_position + mem_height + position),
             str(model.final_product.value) + " product")

    if model.pressure_prod.value != -1:
        # output pressure value
        plt.text((x_mem - (line_width / 2)),
                 (y_position - mem_height - position),
                 "pressure = " + str(model.pressure_prod.value) + " bar")

        if model.ub_press_up.value <= model.pressure_prod.value:
            # compressor
            plt.text((x_mem - (line_width / 2)),
                     (y_position - mem_height - position - 0.8),
                     "using compressor")
        if model.lb_press_up.value >= model.pressure_prod.value:
            # expander
            plt.text((x_mem - (line_width / 2)),
                     (y_position - mem_height - position - 0.8),
                     "using expander")
    else:
        # output pressure equal pressure_up
        plt.text((x_mem - (line_width / 2)),
                 (y_position - mem_height - position), "Any constraint")

        plt.text((x_mem - (line_width / 2)),
                 (y_position - mem_height - position - 0.8),
                 "on output pressure")

    # outprod
    position = 0.3

    # component
    for j in model.components:
        plt.text((x_mem + (line_width / 4)),
                 (y_position + mem_height + position),
                 str(round(model.XOUT_prod[j].value * 100, 2)) + " % " + str(j))
        position += 0.8

    # flow
    plt.text((x_mem + (line_width / 4)), (y_position + mem_height + position),
             str(round(model.OUT_prod.value, 3)) + " mol/s")
    position += 0.8

    plt.text((x_mem + (line_width / 4)), (y_position + mem_height + position),
             "Outprod",
             style='italic',
             fontsize=final_flow_size,
             color="darkmagenta")
    position += 1.8
    try:
        obj_func = str(round(model.obj(), 6))
    except Exception:
        obj_func = str("None")
    plt.text((x_mem + (line_width / 4)), (y_position + mem_height + position),
             "Obj = " + obj_func,
             style='italic',
             fontsize=final_flow_size + 1,
             color="darkmagenta")
    position += 0.8

    # OUT_waste
    position = 0.3

    plt.text((x_mem + (line_width / 4)), (y_position - position),
             "Waste",
             style='italic',
             fontsize=final_flow_size,
             color="steelblue")
    position += 0.8

    # flow
    plt.text((x_mem + (line_width / 4)), (y_position - position),
             str(round(model.OUT_waste.value, 3)) + " mol/s")
    position += 0.8

    # component
    for j in model.components:
        plt.text(
            (x_mem + (line_width / 4)), (y_position - position),
            str(round(model.XOUT_waste[j].value * 100, 2)) + " % " + str(j))
        position += 0.8

    plt.title("Affichage rectangle")
    # TODO: define these values automaticaly
    min_x = -line_width - 2
    max_x = 10 + (mem_width * nb_mem + nb_mem * line_width)
    min_y = -15
    max_y = y_position + (mem_width * nb_mem + nb_mem * line_width)
    plt.xlim(min_x, max_x)
    plt.ylim(min_y, max_y)
    # axes.set_xlabel('axe des x')
    # ax.set_axis_off()
    # plt.text(0.5, 0.5,'lalala')
    if plt_show:
        plt.show()
    else:
        # plt.draw()
        plt.savefig('plotting.png', dpi=1000)
