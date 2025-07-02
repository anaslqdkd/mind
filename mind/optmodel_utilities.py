"""Defining some utilities for the project."""

import pyomo.environ as pe


def initZero(model_instance):
    """ Initaliaze all model variables unifixed to zero.

    Args:

        model_instance (`mind.system.MembranesDesignModel`) : design process model's instance
    """
    out_var = ["OUT_prod", "OUT_waste", "XOUT_prod", "XOUT_waste"]
    for v in model_instance.component_objects(pe.Var, active=True):
        varobject = getattr(model_instance, str(v))
        for index in varobject:
            if not varobject[index].fixed:
                varobject[index] = varobject[index].lb or 0.0


def printDifferences(difflist, outfile=None):
    if outfile is None:
        for item in difflist:
            print(item)
    else:
        for item in difflist:
            outfile.write(item + "\n")


def initDifferences(pippo, mymodel, ConfPar, create=False):
    if create:
        for s in mymodel.states:
            pippo.append("Area[" + str(s) + "]")
        if (ConfPar['uniform_pup']):
            pippo.append("pressure_up     ")
        else:
            for s in mymodel.states:
                pippo.append("pressure_up[" + str(s) + "]")
        for s in mymodel.states:
            pippo.append("pressure_down[" + str(s) + "]")
        # pippo.append("------------------FEED----------------\n")
        for s in mymodel.states:
            pippo.append("FEED_frac[" + str(s) + "]")
        for s in mymodel.states:
            pippo.append("RET[" + str(s) + "] ")
        for s in mymodel.states:
            pippo.append("PERM[" + str(s) + "]")
    else:
        i = 0
        for s in mymodel.states:
            pippo[i] = "Area[" + str(s) + "]"
            i += 1
        if (ConfPar['uniform_pup']):
            pippo[i] = "pressure_up     "
            i += 1
        else:
            for s in mymodel.states:
                pippo[i] = "pressure_up[" + str(s) + "]"
                i += 1
        for s in mymodel.states:
            pippo[i] = "pressure_down[" + str(s) + "]"
            i += 1
        for s in mymodel.states:
            pippo[i] = "FEED_frac[" + str(s) + "]"
            i += 1
        for s in mymodel.states:
            pippo[i] = "RET[" + str(s) + "] "
            i += 1
        for s in mymodel.states:
            pippo[i] = "PERM[" + str(s) + "]"
            i += 1


# def saveDifferences(pippo, mymodel):
#
#     i = 0
#     for s in mymodel.states:
#         pippo[i] += ' -  {0:10.2f}'.format(mymodel.acell[s].value * mymodel.n)
#         i += 1
#     if (ConfPar['uniform_pup']):
#         pippo[i] += ' -  {0:4.2f}'.format(mymodel.pressure_up.value)
#         i += 1
#     else:
#         for s in mymodel.states:
#             pippo[i] += ' -  {0:4.2f}'.format(mymodel.pressure_up[s].value)
#             i += 1
#     for s in mymodel.states:
#         pippo[i] += ' -  {0:4.2f}'.format(mymodel.pressure_down[s].value)
#         i += 1
#     for s in mymodel.states:
#         pippo[i] += ' -  {0:01.3f}'.format(mymodel.splitFEED_frac[s].value)
#         i += 1
#     for s in mymodel.states:
#         pippo[i] += ' -'
#         for s1 in mymodel.states:
#             pippo[i] += '  {0:01.3f}'.format(
#                 mymodel.splitRET_frac[s, s1].value)
#         pippo[i] += '  {0:01.3f}'.format(mymodel.splitOutRET_frac[s].value)
#         i += 1
#     for s in mymodel.states:
#         pippo[i] += ' -'
#         for s1 in mymodel.states:
#             pippo[i] += '  {0:01.3f}'.format(
#                 mymodel.splitPERM_frac[s, s1].value)
#         pippo[i] += '  {0:01.3f}'.format(mymodel.splitOutPERM_frac[s].value)
#         i += 1


def CheckBounds(model_instance):
    for v in model_instance.component_objects(pe.Var, active=True):
        varobject = getattr(model_instance, str(v))
        for index in varobject:
            if varobject[index].lb <= varobject[index] <= varobject[index].ub:
                print(v, "[", index, "] ", "OK")
            else:
                print(v, "[", index, "] ", "outofbounds")


def PrintBounds(model_instance):
    for v in model_instance.component_objects(pe.Var, active=True):
        varobject = getattr(model_instance, str(v))
        for index in varobject:
            print(pe.value(varobject[index].lb), varobject[index],
                  pe.value(varobject[index].ub))


def printPointFromModelAMPL(model_instance):
    for v in model_instance.component_objects(pe.Var, active=True):
        varobject = getattr(model_instance, str(v))
        for index in varobject:
            print(v, "[", index, "] ", varobject[index].value)


def printPointFromModel(model_instance):
    for v in model_instance.component_objects(pe.Var, active=True):
        varobject = getattr(model_instance, str(v))
        for index in varobject:
            print(v, index, varobject[index].value)


def printSlacks(model_instance):
    for c in model_instance.component_objects(pe.Constraint, active=True):
        constobject = getattr(model_instance, str(c))
        for index in constobject:
            print(c, index, constobject[index].slack())
            print(c, index, constobject[index].lslack(),
                  constobject[index].uslack())
            print(c, index, constobject[index].slack(),
                  constobject[index].expr())
